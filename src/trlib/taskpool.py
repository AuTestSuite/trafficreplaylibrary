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
from typing import Union, List, Any, Optional, cast, Tuple


class _Yield(object):
    def __await__(self):
        yield

async def Yield():
    await _Yield()

async def read_queue(q):
    while True:
        try:
            val = q.get(False)
            if val == "__stop__":
                print("Stop command was read")
                break
            yield val
            await Yield()
        except queue.Empty:
            # until task stealing is in place...
            # if nothing on the queue we want to delay at the moment
            # this delay should is to prevent the CPU from running at 100%
            # when there is nothing to do
            await asyncio.sleep(.1)
    return

async def clean_up_tasks(tasks,q):
    new_tasks = []
    for t in tasks:
        if t.done():
            # report a task is done to queue for Join in parent process
            q.task_done()
        else:
            new_tasks.append(t)
        #await Yield()
    return new_tasks


async def read_queue_till_exit(loop,q,parent_q=None):
    #print("Starting read queue")
    tasks = []
    async for task in read_queue(q):
        # if is task.. execute on thread
        if isinstance(task,Task):
            t = loop.run_in_executor(None,task._start)
            tasks.append(t)
        # else is aync task .. start future
        elif isinstance(task,AsyncTask):
            t = asyncio.ensure_future(task._start())
            tasks.append(t)
        tasks = await clean_up_tasks(tasks,q)

    #print("Exiting - wait for tasks to finish")
    while tasks:
        tasks = await clean_up_tasks(tasks,q)
    #print("Exiting - Done!")


def _process_main(q):
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
        ret = loop.run_until_complete(read_queue_till_exit(loop,q))
    except KeyboardInterrupt:
        print("Main Loop - Process {} got ctrl-C", os.getpid())
        pass
    # report a task is done to queue for Join in parent process
    q.task_done()
    return ret

class TaskResult:
    def __init__(self, result:Any, throw:bool=False) -> None:
        self._result: Any = result
        self._throw: bool = throw

    @property
    def result(self):
        if self.throw:
            raise self._result
        return self._result

    @property
    def throw(self):
        return self._throw

class BaseTask:
    def __init__(self, func,*args,**kw) -> None:
        self._func = func
        self._args = args
        self._kw=kw
        self._result_queue:Optional[multiprocessing.Queue] = None
        self._result = None

    @property
    def _return_queue(self) -> Optional[multiprocessing.Queue]:
        return self._result_queue

    @_return_queue.setter
    def _return_queue(self,queue) -> None:
        self._result_queue=queue

    def add_to(self,pool):
        return pool.add_task(self)

    def done(self)-> bool:
        # if the result queue is None we are done
        if self._result_queue:
            try:
                # try to get something
                self._result = self._result_queue.get(False)
                # got something set queue to None as we are done
                self._result_queue=None
            except queue.Empty:
                # did not get anything
                # break the to the async event loop
                return False
        return True

    async def failed(self)-> bool:
        '''
        return True is the task is done and had an exception
        return False if not done or it did not have exeception
        Other ways to do this...
        '''
        return self.done() and isinstance(self._result,Exception)

    async def result(self,no_throw=True):
        # check that we have a queue
        if self._result_queue:
            # have a queue so loop
            while True:
                # check that we have a queue in the loop
                if self._result_queue:
                    try:
                        # try to get something
                        self._result = self._result_queue.get(False)
                        # got something set queue to None as we are done
                        self._result_queue=None
                        break
                    except queue.Empty:
                        # did not get anything
                        # break the to the async event loop
                        await Yield()
                else:
                    # for some reason while in the loop something cleared this out
                    # we assume it did everything correctly.. so we break and return the result
                    break
        # This should throw if there was an expection
        if isinstance(self._result,Exception) and not no_throw:
            raise self._result
        return self._result


class Task(BaseTask):
    def _start(self):
        #if self._result_queue is None:
            #raise RuntimeError("can not start if result queue is not set.")
        try:
            ret = self._func(*self._args,**self._kw)
            self._result_queue.put(ret)
        except Exception as e:
            self._result_queue.put(e)

class AsyncTask(BaseTask):

    async def _start(self):
        #if self._result_queue is None:
            #raise RuntimeError("can not start if result queue is not set.")
        try:
            ret = await self._func(*self._args,**self._kw)
            self._result_queue.put(ret)
        except Exception as e:
            self._result_queue.put(e)


class Worker:
    def __init__(self, queue:Optional[multiprocessing.JoinableQueue]=None, pump=None) -> None:
        self._pump = pump if pump else asyncio.get_event_loop()
        self._in_queue:multiprocessing.Queue = queue if queue else multiprocessing.JoinableQueue()
        self._process: multiprocessing.Process = multiprocessing.Process(target=_process_main, args=(self._in_queue,))

    @property
    def queue(self) -> multiprocessing.Queue:
        return self._in_queue

    @property
    def process(self) -> multiprocessing.Process:
        return self._process

    @property
    def event_loop(self):
        return self._pump

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
        #self._loop: Optional[asyncio.AbstractEventLoop] = None
        if not workers or workers < 0:
            workers = os.cpu_count()
        self._shared_queue: bool = shared_queue
        if shared_queue:
            queue:multiprocessing.JoinableQueue = multiprocessing.JoinableQueue()
            self._workers: List[Worker] = [
                Worker(queue=queue) for i in range(0, cast(int, workers))]
        else:
            self._workers: List[Worker] = [Worker()
                                           for i in range(0, cast(int, workers))]
        self._curr_worker = len(self._workers)
        self._manager=multiprocessing.Manager()
        self._loop:Optional[asyncio.AbstractEventLoop]=None

    def _get_next_worker(self):
        self._curr_worker = (self._curr_worker+1) % len(self._workers)
        return self._workers[self._curr_worker]

    def size(self):
        return len(self._workers)

    def create(self) -> None:
        # create process/thread pool
        #executor = ProcessPoolExecutor(max_workers=len(self._workers))
        # get event loop
        loop = asyncio.get_event_loop()
        # set default executor
        #loop.set_default_executor(executor)
        self._loop = loop

    def start(self):
        # start the workers
        for w in self._workers:
            w.start()

    def run(self, callback, *lst, **kw) -> Any:
        if not self._loop:
            self.create()
        return self._loop.run_until_complete(callback(*lst, **kw))


    def add_task(self, task):
        if not isinstance(task,Task) and not isinstance(task,AsyncTask):
            # check to see if this is a coroutine
            if False:
                pass
            # if not we add it to a task
            elif callable(task):
                task = Task(task)
            else:
                raise RuntimeError("task is not callable: {}".format(repr(task)))
        task._return_queue=self._manager.Queue(1)
        self._get_next_worker().queue.put(task)
        return task

    def stop(self):
        for w in self._workers:
            w.stop()

    def join(self):
        for w in self._workers:
            w.join()

async def wait_all(tasks:List[Union[Task,AsyncTask]],timeout=None) -> None:
    '''
    Wait for all task to finish
    '''
    while tasks:
        tasks = [task for task in tasks if not task.done()]

async def gather(tasks:List[Union[Task,AsyncTask]]) -> List[Any]:
    '''this will gather everything once it is finished'''
    await wait_all(tasks)
    return [await task.result() for task in tasks]

async def gather_done(tasks:List[Union[Task,AsyncTask]]) -> Tuple[List[Any],List[Union[Task,AsyncTask]]]:
    '''
    gather result of any tasks that are finished and return task list of items not finished
    '''
    working_tasks = []
    results = []
    for task in tasks:
        if not task.done():
            working_tasks.append(task)
        else:
            results.append(await task.result(no_throw=True))
    return (results,working_tasks)

def create_pool(workers: Optional[int] = None, shared_queue: bool = False):
    return TaskPool(workers, shared_queue)
