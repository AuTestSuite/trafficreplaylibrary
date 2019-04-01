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

#from .svUtils import *
from trlib.parser.attribute import Attribute
from .request import Request
from .response import Response
from deprecated import deprecated
from typing import Optional


class Transaction(object):
    ''' Tranaction encapsulates a single UA transaction '''
    attributes = [
        Attribute("uuid", str),
        # should be some epoch/time/date-time value
        Attribute("start-time", int, argument_name="timestamp"),
        Attribute("client-request", Request, required=True,
                  argument_name="c_request"),
        Attribute("server-response", Response,
                  required=True, argument_name="s_response"),
        Attribute("proxy-request", Request, argument_name="p_request"),
        Attribute("proxy-response", Response, argument_name="p_response"),
    ]

    def __init__(self, c_request: Request, s_response: Response, p_request: Optional[Request] = None, p_response: Optional[Response] = None, uuid: Optional[str] = None, timestamp: Optional[str] = None):
        self._c_request: Request = c_request
        self._s_response: Response = s_response
        self._p_request: Request = p_request if not None else c_request
        self._p_response: Response = p_response if not None else s_response
        self._uuid: Optional[str] = uuid
        self._timestamp: Optional[str] = timestamp

    @deprecated(reason="Use clientRequest property instead")
    def getClientRequest(self):
        return self._c_request

    @deprecated(reason="Use serverResponse property instead")
    def getServerResponse(self):
        return self._s_response

    @deprecated(reason="Use proxyRequest property instead")
    def getProxyRequest(self):
        return self._p_request

    @deprecated(reason="Use proxyResponse property instead")
    def getProxyResponse(self):
        return self._p_response

    @deprecated(reason="Use UUID property instead")
    def getUUID(self):
        return self._uuid

    @deprecated(reason="Use timestamp property instead")
    def getTimestamp(self):
        return self._timestamp

    @property
    def clientRequest(self) -> Request:
        return self._c_request

    @property
    def serverResponse(self) -> Response:
        return self._s_response

    @property
    def proxyRequest(self) -> Request:
        return self._p_request

    @property
    def proxyResponse(self) -> Response:
        return self._p_response

    @property
    def UUID(self) -> str:
        return self._uuid

    @property
    def timestamp(self) -> str:
        return self._timestamp

    def validate(self) -> bool:
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
