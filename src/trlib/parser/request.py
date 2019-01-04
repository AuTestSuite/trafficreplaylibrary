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

from .svUtils import *


class Request(object):
    ''' Request encapsulates a single request from the UA '''

    def getHeaders(self):
        return self._headers

    def getScheme(self):
        return self._scheme

    def getVersion(self):
        return self._version

    def getMethod(self):
        return self._method

    def getContentSize(self):
        return self._contentSize

    def getEncoding(self):
        return self._encoding

    def getURL(self):
        return self._url

    def getBody(self):
        return self._body

    def getOptions(self):
        return self._options

    def getHeaderMD5(self):
        ''' Returns the MD5 hash of the headers

        This is used to do a unique mapping to a request/response transaction '''
        return hashlib.md5(self._headers.encode()).hexdigest()

    def validate(self):
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

        return retval

    def __repr__(self):
        retstr = '<Request: '

        for varname, varval in vars(self).items():
            retstr += '{0}: {1} '.format(varname, varval)

        retstr += '>\n'

        return retstr

    def toJSON(self):
        retJson = dict()

        retJson['method'] = self._method
        retJson['url'] = self._url

        if self._version:
            retJson['version'] = self._version

        if self._scheme:
            retJson['scheme'] = self._scheme

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

    def __init__(self, scheme, version, url, method, encoding, contentSize, data, headers, options):
        self._scheme = scheme
        self._method = method
        self._encoding = encoding
        self._contentSize = contentSize
        self._headers = headers
        self._version = version
        self._url = url
        self._body = data
        self._options = options

    @classmethod
    def fromJSON(cls, data, metaName):
        if not data:
            return None

        try:
            _httpVersion = getOptional(data, 'version')
            _scheme = getOptional(data, 'scheme')
            _method = getRequired(data, 'method')
            _url = getRequired(data, 'url')
            _options = getOptional(data, 'options')

            # if _scheme != 'GET':
            #     raise KeyError('nah')

            content = getOptional(data, 'content')
            _encoding = getOptional(content, 'encoding')  # NOTE NOT USED
            _size = getOptional(content, 'size')
            _data = getOptional(content, 'data')

            headers = getOptional(data, 'headers')
            header_encoding = getOptional(headers, 'encoding')  # NOTE NOT USED
            # NOTE can and will break sometime because headers is optional
            _headers = generateHeadersFromTxnFields(
                getOptional(headers, 'fields'))

            # if _size and ('Content-Length' not in _headers or 'content-length' not in _headers):
            # _headers.update({'Content-Length': _size})  # NOTE temporary solution
        except Exception as e:
            print("Error in parsing {0} request".format(metaName))
            raise e

        return cls(_scheme, _httpVersion, _url, _method, _encoding, _size, _data, _headers, _options)

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
