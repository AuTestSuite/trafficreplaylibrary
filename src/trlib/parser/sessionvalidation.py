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

import json
import os
import traceback

from .session import Session
from .transaction import Transaction
from .request import Request
from .response import Response
from .svUtils import *

allowed_HTTP_request_methods = ['GET', 'POST', 'HEAD', 'PULL']
REPLAY_JSON_VERSION = '1.0'


class SessionValidator(object):
    '''
    SessionValidator parses, validates, and exports an API for a given set of JSON sessions generated from Apache Traffic Server

    SessionValidator is initialized with a path to a directory of JSON sessions. It then automatically parses and validates all the
    session in the directory. After initialization, the user may use the provided API

    TODO :
    Provide a list of guaranteed fields for each type of object (ie a Transaction has a request and a response, a request has ...)
    '''

    def parse(self):
        ''' 
        Constructs Session objects from JSON files on disk and stores objects into _sessions 

        All sessions missing required fields (ie. a session timestamp, a response for every request, etc) are
        dropped and the filename is stored inside _bad_sessions
        '''

        log_filenames = [os.path.join(self._json_log_dir, f) for f in os.listdir(
            self._json_log_dir) if os.path.isfile(os.path.join(self._json_log_dir, f))]

        for fname in log_filenames:
            with open(fname) as f:
                # first attempt to load the JSON
                try:
                    dataset = json.load(f)
                except Exception as e:
                    self._bad_sessions.append(fname)
                    verbose_print(
                        "Warning: JSON parse error on file={0}. Error: {1}".format(fname, e))
                    print(
                        "Warning: JSON parse error on file={0}. Error: {1}".format(fname, e))
                    continue

                # then attempt to extract all the required fields from the JSON
                try:
                    # print(dataset)
                    json_version = dataset["meta"]['version']

                    # ideally the G_REPLAY_JSON_VERSION variable gets updated
                    if json_version != REPLAY_JSON_VERSION:
                        self._bad_sessions.append(fname)
                        print("Warning: JSON version mismatch on file={0} got {1} expecting {2}".format(
                            fname, session_version, REPLAY_JSON_VERSION))
                        verbose_print("Warning: JSON version mismatch on file={0} got {1} expecting {2}".format(
                            fname, session_version, REPLAY_JSON_VERSION))
                        continue

                    try:
                        for s in dataset['sessions']:
                            self._sessions.append(Session.fromJSON(fname, s))
                    except Exception as e:
                        print(
                            "Faulty session in file {0} with error {1}".format(fname, e))
                        continue

                except Exception as e:
                    self._bad_sessions.append(fname)
                    # traceback.print_exc()
                    print(
                        "Warning: parse error for file={1}. Error: {0}".format(e, fname))
                    verbose_print(
                        "Warning: parse error for file={1}. Error: {0}".format(e, fname))
                    continue

    def validate(self):
        ''' Prunes out all the invalid Sessions in _sessions '''

        good_sessions = list()

        for sesh in self._sessions:
            if sesh.validate():
                good_sessions.append(sesh)
            else:
                self._bad_sessions.append(sesh._filename)

        self._sessions = good_sessions

    def getSessionList(self):
        ''' Returns the list of Session objects '''
        return self._sessions

    def getSessionIter(self):
        ''' Returns an iterator of the Session objects '''
        return iter(self._sessions)

    def getBadSessionList(self):
        ''' Returns a list of bad session filenames (list of strings) '''
        return self._bad_sessions

    def getBadSessionListIter(self):
        ''' Returns an iterator of bad session filenames (iterator of strings) '''
        return iter(self._bad_sessions)

    def __init__(self, json_log_dir, verbose=False):
        global valid_HTTP_request_methods, G_VERBOSE_LOG
        G_VERBOSE_LOG = verbose
        self._json_log_dir = json_log_dir
        self._bad_sessions = list()   # list of filenames
        self._sessions = list()       # list of _good_ session objects

        self.parse()
        self.validate()
