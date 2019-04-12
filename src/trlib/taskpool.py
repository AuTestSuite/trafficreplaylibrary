'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
'''

# plan to move to this its own library once we think it is ready to do so


import os
import asyncio
import multiprocessing
import queue
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Union, List, Any, Optional, cast, Tuple, Dict


class Event(object):

    def __init__(self):
        self.__callbacks = list()

    def connect(self, callback, prepend=False):
        if prepend:
            self.__callbacks = [callback]+self.__callbacks
        else:
            self.__callbacks.append(callback)
        return self

    def __iadd__(self, callback):
        return self.connect(callback)

    def disconnect(self, callback):
        try:
            self.__callbacks.remove(callback)
        except BaseException:
            pass
        return self

    def __isub__(self, callback):
        return self.disconnect(callback)

    def __call__(self, *args, **kargs):
        for callback in self.__callbacks:
            callback(*args, **kargs)

    def __len__(self):
        return len(self.__callbacks)


class _Yield(object):
    def __await__(self):
        yield


async def Yield():
    await _Yield()


class TaskSet:
    def __init__(self, iter=None):
        self._tasks = {}
        self._results = {}
        self.update(iter)

    def add(self, task):
        if task.ID not in self._tasks:
            if not task.done():
                task.on_finished.connect(lambda: self._add_result(self.remove(task)))
                self._tasks[task.ID] = task
            else:
                self._add_result(task)
        return task

    def update(self, iter):
        if iter:
            for l in iter:
                self.add(l)

    def _add_result(self, task):
        if task:
            self._results[task.ID] = task.result

    def empty(self) -> bool:
        if self._tasks:
            return True
        return False

    def remove(self, obj):
        return self._tasks.pop(obj.ID)

    async def gather(self):
        await self.wait_all()
        return self._results.values()

    async def wait_all(self):
        while self._tasks:
            await asyncio.sleep(0.1)


class _AyncioTaskSet:
    def __init__(self):
        self._tasks = {}

    def add(self, task, aiotask):
        task.on_finished.connect(lambda: self.remove(task))
        self._tasks[task.ID] = aiotask

    def remove(self, task):
        try:
            return self._tasks.pop(task.ID)
        except KeyError:
            print(task.ID, "not found")

    async def wait_all(self):
        while self._tasks:
            await asyncio.sleep(0.1)


async def read_queue(q, tasks):
    cnt = 0
    while True:
        # try:
        if not q.empty():
            val = q.get()
            if val == "__stop__":
                break
            yield val
            cnt = 0
            # need yield else we might pull most of the items of the queue
            # preventing a good load balance
            await Yield()
        else:
            # until task stealing is in place...
            # if nothing on the queue we want to delay at the moment
            # this delay should is to prevent the CPU from running at 100%
            # when there is nothing to do
            cnt += 1
            if cnt > 10000:
                cnt = 0
            else:
                await asyncio.sleep(0.01)
    return


def _task_finished(task, parent_q):
    def _start_capture():
        parent_q.put((task.ID, task.result(no_throw=False)))
    return _start_capture


async def read_queue_till_exit(loop, q, parent_q):
    #print("Starting read queue")
    tasks = _AyncioTaskSet()
    #st = None
    cnt = 0
    misses = 0
    #async for task in read_queue(q, tasks):
    while True:
        if not q.empty():
            task = q.get()
            if task == "__stop__":
                break
            #if not st:
                #if cnt == 1:
                  #st = time.time()
            cnt+=1
            misses = 0
            # add the task to the task set
            # add a event handler for when the task is done to return the
            # result to the parent
            task.on_finished.connect(_task_finished(task, parent_q))
            tasks.add(task, task.startup(loop))
            # focus on empting the queue
            if cnt%100: # make this a noob to control
                await Yield()
        else:
            misses += 1
            if misses > 10000:
                await asyncio.sleep(0.01)
            else:
                await Yield()

    #tt = time.time() - st
    #print("{} msg/sec".format(cnt/tt))
    await tasks.wait_all()
    #tt = time.time() - st
    #print("{} task/sec".format(cnt/tt))
    #print("Exiting - Done!")


def _process_main(q, parent_q):
    '''
    This is the main entry point and thread we make to handle a task
    It will setup a loop in case the task has async logic in it
    '''
    ret: Any = None
    try:
        # make a thread pool Executor to deal with tasks
        executor = ThreadPoolExecutor()
        # create our event loop for this process
        loop = asyncio.new_event_loop()
        # add executor
        loop.set_default_executor(executor)
        # set the event loop as default
        asyncio.set_event_loop(loop)
        # run the tasks loggic
        ret = loop.run_until_complete(read_queue_till_exit(loop, q, parent_q))
    except KeyboardInterrupt:
        print("Main Loop - Process {} got ctrl-C", os.getpid())
        pass
    return ret


class BaseTask:
    def __init__(self, func, *args, **kw) -> None:
        # what we will call
        self._func = func
        self._args = args
        self._kw = kw
        # the result
        self._result = None
        # the ID used for this task
        self._id = id(self)

        # some events to help efficancy
        self._finished_event = Event()
        self._is_done = False

    # some function to control what is pickled
    def __getstate__(self):
        # we don't pickle the result, worker or queue
        return (self._func, self._args, self._kw, self._id)

    def __setstate__(self, state):
        self._func, self._args, self._kw, self._id = state
        self._finished_event = Event()
        self._is_done = False

    # Some event hooks
    @property
    def on_finished(self):
        return self._finished_event

    @property
    def ID(self):
        return self._id

    @property
    def _return_queue(self) -> Optional[multiprocessing.Queue]:
        return self._result_queue

    @_return_queue.setter
    def _return_queue(self, queue) -> None:
        self._result_queue = queue

    def _set_result(self, result):
        self._result = result
        self._is_done = True
        self._finished_event()

    def add_to(self, pool):
        return pool.add_task(self)

    def done(self) -> bool:
        return self._is_done

    async def failed(self) -> bool:
        '''
        return True is the task is done and had an exception
        return False if not done or it did not have exeception
        Other ways to do this...
        '''
        return self.done() and isinstance(self._result, Exception)

    def result(self, no_throw=True):
        # might want to add a timeout value to break waiting
        # wait till we are done
        if self.done():
            # This should throw if there was an expection
            if isinstance(self._result, Exception) and not no_throw:
                raise self._result
            return self._result
        raise asyncio.InvalidStateError


class Task(BaseTask):

    def startup(self, loop):
        return loop.run_in_executor(None, self._start)

    def _start(self):
        # if self._result_queue is None:
            #raise RuntimeError("can not start if result queue is not set.")
        try:
            ret = self._func(*self._args, **self._kw)
            self._set_result(ret)
        except Exception as e:
            self._set_result(e)


class AsyncTask(BaseTask):

    def startup(self, loop):
        return asyncio.ensure_future(self._start())

    async def _start(self):
        # if self._result_queue is None:
            #raise RuntimeError("can not start if result queue is not set.")
        try:
            ret = await self._func(*self._args, **self._kw)
            self._set_result(ret)
        except Exception as e:
            self._set_result(e)


class Worker:
    def __init__(self, queue: Optional[multiprocessing.Queue] = None, rqueue: Optional[multiprocessing.Queue] = None, pump=None) -> None:
        # the main asyncio pump
        self._pump = pump if pump else asyncio.get_event_loop()
        # this is the queue we push task out one
        self._in_queue: multiprocessing.Queue = queue if queue else multiprocessing.Queue()
        # this is the Queue we get return codes on
        # we don't use the manager as it has a major factor 100x+ slow down when used
        # it is faster to write to our own return queue and sort the result to the correct Task object
        self._return_queue: multiprocessing.Queue = rqueue if rqueue else multiprocessing.Queue()
        # this is the process we use for as the worker "thread"
        self._process: multiprocessing.Process = multiprocessing.Process(
            target=_process_main, args=(self._in_queue, self._return_queue))
        # these are all the task we have mapped to the worker
        # self._tasks:Dict[int,BaseTask]={}

    @property
    def queue(self) -> multiprocessing.Queue:
        return self._in_queue

    @property
    def process(self) -> multiprocessing.Process:
        return self._process

    @property
    def return_queue(self):
        return self._return_queue

    @property
    def event_loop(self):
        return self._pump

    def add_task(self, task):
        self._in_queue.put(task)

    def start(self) -> None:
        self._process.start()

    def stop(self) -> None:
        return self._in_queue.put("__stop__")  # send stop command

    def join(self) -> None:
        self._process.join()

    def total_tasks_count(self) -> int:
        pass

    def AsyncTasks(self) -> int:
        pass

    def ThreadedTasks(self) -> int:
        pass


class TaskPool:
    def __init__(self, workers: Optional[int], shared_queue: bool = False) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        if not workers or workers < 0:
            workers = os.cpu_count()
        self._num_workers = workers
        self._shared_queue: bool = shared_queue
        self._return_queues: List[multiprocessing.Queue] = []

        self._setup()

        self._curr_worker = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._tasks: Dict[int, BaseTask] = {}

    def _get_next_worker(self):
        self._curr_worker = (self._curr_worker+1) % len(self._workers)
        return self._workers[self._curr_worker]

    def size(self):
        return self._num_workers

    def create(self) -> None:
        # create process/thread pool
        #executor = ProcessPoolExecutor(max_workers=len(self._workers))
        # get event loop
        loop = asyncio.get_event_loop()
        # set default executor
        # loop.set_default_executor(executor)
        self._loop = loop

    def _setup(self):
        if not self._running:
            if self._shared_queue:
                # shared input queue
                queue: multiprocessing.Queue = multiprocessing.Queue()
                self._workers: List[Worker] = [
                    Worker(queue=queue) for i in range(0, cast(int, self._num_workers))]
                # get the return queues for each worker
                self._return_queues = [w.return_queue for w in self._workers]
            else:
                self._workers: List[Worker] = [Worker()
                                               for i in range(0, cast(int, self._num_workers))]
                # get the return queues for each worker
                self._return_queues = [w.return_queue for w in self._workers]
        else:
            raise RuntimeError("Task pool is already running")

    def _start(self):
        self._setup()
        # start the workers
        for w in self._workers:
            w.start()
        self._running = True
        self._return_reader_ = asyncio.ensure_future(self._reader_task())

    def _stop(self):
        for w in self._workers:
            w.stop()

    def _join(self):
        for w in self._workers:
            w.join()
        self._running = False

    async def _run_wrapper(self, callback, *lst, **kw):
        self._return_reader_ = asyncio.ensure_future(self._reader_task())
        ret = await callback(*lst, **kw)
        self._stop()
        self._join()

    def run(self, callback, *lst, **kw) -> Any:
        if not self._loop:
            self.create()
        self._start()
        ret = self._loop.run_until_complete(self._run_wrapper(callback, *lst, **kw))

    def gather_tasks(self):
        '''get any new tasks that are finished'''
        while self.process_return_queue():
            pass

    async def _reader_task(self):
        while self._running:
            if not self.process_return_queue():
                await asyncio.sleep(0.1)

    def process_return_queue(self):
        ret = False
        for q in self._return_queues:
            while not q.empty():
                taskid, result = q.get()
                # if we add chaining ... it will be handled here
                task = self._tasks.pop(taskid)
                task._set_result(result)
                ret = True
        return ret

    def add_task(self, task):
        if not isinstance(task, Task) and not isinstance(task, AsyncTask):
            # check to see if this is a coroutine
            if False:
                pass
            # if not we add it to a task
            elif callable(task):
                task = Task(task)
            else:
                raise RuntimeError(
                    "task is not callable: {}".format(repr(task)))
        # get the worker that will own this task as it runs
        worker = self._get_next_worker()
        # give the task to the worker
        worker.add_task(task)
        task._pool = self
        self._tasks[task.ID] = task
        return task


############################################
# public functions for waiting on items

async def wait_all(tasks: List[Union[Task, AsyncTask]], timeout=None) -> None:
    '''
    Wait for all task to finish
    '''
    ts = TaskSet(tasks)
    await ts.wait_all()


async def gather(tasks: List[Union[Task, AsyncTask]]) -> List[Any]:
    '''this will gather everything once it is finished'''
    ts = TaskSet(tasks)
    return await ts.gather()


async def gather_done(tasks: List[Union[Task, AsyncTask]]) -> Tuple[List[Any], List[Union[Task, AsyncTask]]]:
    '''
    gather result of any tasks that are finished and return task list of items not finished
    '''
    working_tasks = []
    results = []
    for task in tasks:
        if not task.done():
            working_tasks.append(task)
        else:
            results.append(task.result(no_throw=True))
    return (results, working_tasks)


def create_pool(workers: Optional[int] = None, shared_queue: bool = False):
    return TaskPool(workers, shared_queue)
