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
from .request import Request
from .response import Response


class Transaction(object):
    ''' Tranaction encapsulates a single UA transaction '''

    def getClientRequest(self):
        return self._c_request

    def getServerResponse(self):
        return self._s_response

    def getProxyRequest(self):
        return self._p_request

    def getProxyResponse(self):
        return self._p_response

    def getUUID(self):
        return self._uuid

    def getTimestamp(self):
        return self._timestamp

    def validate(self):
        retval = True

        # is uuid necessary
        # if not self._uuid:
        #     retval = False
        #     verbose_print("Transaction does not have a valid UUID.")

        retval = retval and self._c_request.validate()
        retval = retval and self._s_response.validate()

        # this may have to be removed
        if self._p_request:
            retval = retval and self._p_request.validate()

        if self._p_response:
            retval = retval and self._p_response.validate()

        return retval

    def __repr__(self):
        retstr = '<Transaction: '

        for varname, varval in vars(self).items():
            retstr += '{0}: {1} '.format(varname, varval)

        retstr += '>\n'

        return retstr

    @classmethod
    def fromJSON(cls, data):
        try:
            _uuid = getOptional(data, 'uuid')
            _start_time = getOptional(data, 'start-time')  # NOTE NOT USED

            # TODO: can't handle non-existent proxy-req/resp right now
            _c_req = Request.fromJSON(getRequired(
                data, 'client-request'), 'client')
            _p_req = Request.fromJSON(
                getOptional(data, 'proxy-request'), 'proxy')
            _p_res = Response.fromJSON(
                getOptional(data, 'proxy-response'), 'proxy')
            _s_res = Response.fromJSON(getRequired(
                data, 'server-response'), 'server')
        except Exception as e:
            print("Exception in parsing txn {0}. Error: {1}".format(
                _uuid if _uuid else "", e))
            raise e

        return cls(_c_req, _p_req, _s_res, _p_res, _uuid, _start_time)

    def toJSON(self):
        retJson = dict()

        if self._timestamp:
            retJson['start-time'] = self._timestamp

        if self._uuid:
            retJson['uuid'] = self._uuid

        # p_request and p_response not required
        if self._p_request:
            retJson['proxy-request'] = self._p_request.toJSON()

        if self._p_response:
            retJson['proxy-response'] = self._p_response.toJSON()

        # c_request and s_response are required, so if check is not needed
        retJson['client-request'] = self._c_request.toJSON()
        retJson['server-response'] = self._s_response.toJSON()

        return retJson

    def __init__(self, c_request, p_request, s_response, p_response, uuid, timestamp):
        self._c_request = c_request
        self._s_response = s_response
        self._p_request = p_request
        self._p_response = p_response
        self._uuid = uuid
        self._timestamp = timestamp
