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

from trlib.parser.attribute import Attribute
from typing import List
from deprecated import deprecated

#from .svUtils import *
from .transaction import Transaction


class Session(object):
    attributes = [
        Attribute("transactions", List[Transaction], required=True),
        # should be validated as "ipv4 or ipv6"
        Attribute("protocol", List[str],),
        Attribute("connection-time", int, argument_name="timestamp")
    ]

    ''' Session encapsulates a single user session '''

    def __init__(self, timestamp: str, protocol: str, transactions: List[Transaction]):

        self._timestamp: str = timestamp
        self._protocol: str = protocol
        self._transaction_list: List[Transaction] = transactions

    @property
    def transactions(self) -> List[Transaction]:
        return self._transaction_list

    @deprecated(reason="Use transactions property instead")
    def getTransactionList(self):
        ''' Returns a list of transaction objects '''
        return self._transaction_list

    @deprecated(reason="Use 'obj.transactions[0]' instead")
    def getFirstTransaction(self):
        return self._transaction_list[0]

    @deprecated(reason="Iter over transactions property instead")
    def getTransactionIter(self):
        return iter(self._transaction_list)

    @deprecated(reason="Don't use")
    def getFilename(self):
        return ""

    @property
    def timestamp(self):
        return self._timestamp

    @deprecated(reason="Use timestamp property instead")
    def getTimestamp(self):
        return self._timestamp

    @property
    def protocol(self):
        return self._protocol

    @deprecated(reason="Use protocol property instead")
    def getProtocol(self) -> str:
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

        for txn in self._transaction_list():
            retval = retval and txn.validate()

        return retval

    def __repr__(self):
        retstr = '<Session: '

        for varname, varval in vars(self).items():
            retstr += '{0}: {1} '.format(varname, varval)

        retstr += '>\n'

        return retstr
