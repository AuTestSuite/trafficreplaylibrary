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

import hashlib

from deprecated import deprecated

from trlib.parser.attribute import Attribute
from typing import Optional
from .content import Content
from .header import Header

#from .svUtils import *


class Request(object):
    ''' Request encapsulates a single request from the UA '''
    attributes = [
        # validate that it is 1.0, 1.1, 2.0
        Attribute("version", str, default="1.1"),
        Attribute("method", str, required=True),  # Get, Post, etc...
        Attribute("url", str, required=True),  # validate as url
        # http or https .. should be move to transaction level
        Attribute("scheme", str,),
        Attribute("content", Content),
        Attribute("headers", Header),
        Attribute("options", dict),
    ]

    def __init__(self, version: str, url: str, method: str, scheme: Optional[str] = None, content: Optional[Content] = None, headers: Optional[Header] = None, options={}):
        self._scheme = scheme
        self._method = method
        self._headers = headers
        self._version = version
        self._url = url
        self._body = content
        self._options = options

    @deprecated(reason="Use header property instead")
    def getHeaders(self):
        return self._headers

    @deprecated(reason="Use schema property instead")
    def getScheme(self):
        return self._scheme

    @deprecated(reason="Use version property instead")
    def getVersion(self):
        return self._version

    @deprecated(reason="Use method property instead")
    def getMethod(self):
        return self._method

    @deprecated(reason="Use len(obj.body) property instead")
    def getContentSize(self):
        return len(self.body)

    @deprecated(reason="Use encoding property of header or content instead")
    def getEncoding(self):
        return self._body.encoding

    @deprecated(reason="Use url property instead")
    def getURL(self):
        return self._url

    @deprecated(reason="Use body property instead")
    def getBody(self):
        return self._body

    @deprecated(reason="Use options property instead")
    def getOptions(self):
        return self._options

    @property
    def headers(self):
        return self._headers

    @property
    def scheme(self):
        return self._scheme

    @property
    def version(self):
        return self._version

    @property
    def method(self):
        return self._method

    @property
    def url(self):
        return self._url

    @property
    def body(self):
        return self._body

    @property
    def options(self):
        return self._options

    def getHeaderMD5(self):
        ''' Returns the MD5 hash of the headers

        This is used to do a unique mapping to a request/response transaction '''
        return hashlib.md5(self._headers.encode()).hexdigest()

    '''def validate(self):
        retval = True

        # skipping scheme
        if not self._method:
            retval = False
            verbose_print("Request does not have a valid method.")
        elif not self._url:
            retval = False
            verbose_print("Request does not have valid URL.")
        # elif not self._contentSize: # NOTE: check this in conjunction with transfer-encoding
        #     retval = False
        #     verbose_print("Request does not have valid contentSize.")
        elif not self._headers:  # NOTE: make conditional
            retval = False
            verbose_print("Request does not have valid headers.")
        # NOTE: what to do with content

        return retval'''

    def __repr__(self):
        retstr = '<Request: '

        for varname, varval in vars(self).items():
            retstr += '{0}: {1} '.format(varname, varval)

        retstr += '>\n'

        return retstr

    # mostly adapted from Apache Traffic Server's tests' simple request lines
    @classmethod
    def fromRequestLine(cls, requestLine, body, options=None):
        req, headers = requestLine.split("\r\n", 1)

        # reassign since we don't need the original anymore
        headers = generateHeadersFromRequestLine(headers)
        method = req.split(" ")[0]
        path = req.split(" ")[1]

        contentSize = None

        if body:
            contentSize = len(body)

        return cls(None, None, path, method, None, contentSize, body, headers, options)
