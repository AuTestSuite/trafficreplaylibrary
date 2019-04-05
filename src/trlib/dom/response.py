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
from typing import Optional

from deprecated import deprecated

from trlib.parser.attribute import Attribute

#from .svUtils import *
from .content import Content
from .header import Header


class Response(object):
    ''' Response encapsulates a single response from the UA '''
    attributes = [
        Attribute("status", int, required=True),
        # http or https .. should be move to transaction level
        Attribute("reason", str,),
        Attribute("content", Content),
        Attribute("headers", Header),
        Attribute("options", dict),
    ]

    def __init__(self, status: int, reason: Optional[str] = None, encoding: Optional[str] = None, content: Optional[Content] = None, headers: Optional[Header] = None, options={}):
        self._status: int = status
        self._reason: Optional[str] = reason
        self._encoding: Optional[str] = encoding
        self._content: Content = content
        self._header: Header = headers
        self._options = options

    @deprecated(reason="Use headers property instead")
    def getHeaders(self):
        return self._header

    @deprecated(reason="Use status property instead")
    def getStatus(self):
        return self._status

    @deprecated(reason="Use reason property instead")
    def getReason(self):
        return self._reason

    @deprecated(reason="Use len(obj.body) property instead")
    def getContentSize(self):
        return len(self._content)

    @deprecated(reason="Use encoding property instead")
    def getEncoding(self):
        return self._encoding

    @deprecated(reason="Use body property instead")
    def getBody(self):
        return self._content.content

    @deprecated(reason="Use options property instead")
    def getOptions(self):
        return self._options
    ###

    @property
    def headers(self) -> Header:
        return self._header

    @property
    def status(self) -> int:
        return self._status

    @property
    def reason(self) -> Optional[str]:
        return self._reason

    @property
    def encoding(self) -> Optional[str]:
        return self._encoding

    @property
    def body(self) -> Content:
        return self._content

    @property
    def options(self):
        return self._options

    def __repr__(self):
        retstr = '<Response: '

        for varname, varval in vars(self).items():
            retstr += '{0}: {1} '.format(varname, varval)

        retstr += '>\n'

        return retstr

    # def validateValues(self,stat:int=None,content:str= None, content_length:int= None,headers:Optional[Dict[str,str]]=None,reason:Optional[str]= None):

    def validateFormat(self):
        retval = True

        # skipping reason
        if not self._status:
            retval = False
            verbose_print("Response does not have a valid status.")
        # elif not self._headers:  # NOTE: make conditional
        #     retval = False
        #     verbose_print("Response does not have valid headers.")
        # NOTE: what to do with content

        return retval

    def toJSON(self):
        retJson = dict()

        retJson['status'] = self._status

        if self._reason:
            retJson['reason'] = self._reason

        if self._options:
            retJson['options'] = self._options

        if self._contentSize or self._body:
            retJson['content'] = dict()

            if self._body:
                retJson['content']['data'] = self._body

            if self._contentSize:
                retJson['content']['size'] = self._contentSize

            if self._encoding:
                retJson['content']['encoding'] = self._encoding

        if self._headers:
            retJson['headers'] = dict()
            retJson['headers']['fields'] = list()

            for hdr in self._headers:
                retJson['headers']['fields'].append([hdr, self._headers[hdr]])

        return retJson

    # mostly adapted from Apache Traffic Server's tests' simple request lines
    @classmethod
    def fromRequestLine(cls, requestLine, body, options):
        res, headers = requestLine.split("\r\n", 1)

        # reassign since we don't need the original anymore
        headers = generateHeadersFromRequestLine(headers)
        status = int(res.split(" ", 2)[1])
        reason = res.split(" ", 2)[2]

        contentSize = None

        if body:
            contentSize = len(body)

        return cls(status, reason, None, contentSize, body, headers, options)
