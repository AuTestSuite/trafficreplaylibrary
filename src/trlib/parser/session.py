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

from .svUtils import *
from .transaction import Transaction


class Session(object):
    REQUIRED_FIELDS = ['transactions']

    ''' Session encapsulates a single user session '''

    def getTransactionList(self):
        ''' Returns a list of transaction objects '''
        return self._transaction_list

    def getFirstTransaction(self):
        return self._transaction_list[0]

    def getTransactionIter(self):
        return iter(self._transaction_list)

    def getFilename(self):
        return self._filename

    def getTimestamp(self):
        return self._timestamp

    def getProtocol(self):
        return self._protocol

    def validate(self):
        # fields skipped: connect-time, protocol
        retval = True

        if not self._filename:
            retval = False
            verbose_print("Session does not have an associated filename.")
        elif not self._transaction_list:
            retval = False
            verbose_print(
                "Session from {0} does not have an associated transaction list.".format(self._filename))

        for txn in self.getTransactionIter():
            retval = retval and txn.validate()

        return retval

    def __repr__(self):
        retstr = '<Session: '

        for varname, varval in vars(self).items():
            retstr += '{0}: {1} '.format(varname, varval)

        retstr += '>\n'

        return retstr

    @classmethod
    def fromJSON(cls, fname, data):
        _protocol = getOptional(data, 'protocol')  # NOTE NOT USED
        _connection_time = getOptional(
            data, 'connection-time')  # NOTE NOT USED
        _txns = []

        for txn in getRequired(data, 'transactions'):
            try:
                _txns.append(Transaction.fromJSON(txn))
            except Exception as e:
                print("Skipping faulty txn in session with connect-time {0} in file {1}. Error: {2}".format(
                    _connection_time, fname, e))
                continue

        return cls(fname, _connection_time, _protocol, _txns)

    def toJSON(self):
        retJson = dict()

        if self._protocol:
            retJson['protocol'] = self._protocol

        if self._timestamp:
            retJson['connection-time'] = self._timestamp

        retJson['transactions'] = list()

        for txn in self._transaction_list:
            retJson['transactions'].append(txn.toJSON())

        return retJson

    def __init__(self, filename, timestamp, protocol, transaction_list):
        self._filename = filename
        self._timestamp = timestamp
        self._protocol = protocol
        self._transaction_list = transaction_list
