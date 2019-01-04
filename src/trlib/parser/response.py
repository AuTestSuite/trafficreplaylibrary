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


class Response(object):
    ''' Response encapsulates a single response from the UA '''

    def getHeaders(self):
        return self._headers

    def getStatus(self):
        return self._status

    def getReason(self):
        return self._reason

    def getContentSize(self):
        return self._contentSize

    def getEncoding(self):
        return self._encoding

    def getBody(self):
        return self._body

    def getOptions(self):
        return self._options

    def __repr__(self):
        retstr = '<Response: '

        for varname, varval in vars(self).items():
            retstr += '{0}: {1} '.format(varname, varval)

        retstr += '>\n'

        return retstr

    def validate(self):
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

    def __init__(self, status, reason, encoding, contentSize, data, headers, options):
        self._status = status
        self._reason = reason
        self._encoding = encoding
        self._contentSize = contentSize
        self._headers = headers
        self._body = data
        self._options = options

    @classmethod
    def fromJSON(cls, data, metaName):
        if not data:
            return None

        try:
            _status = getRequired(data, 'status')
            _reason = getOptional(data, 'reason')
            _encoding = getOptional(data, 'encoding')
            _options = getOptional(data, 'options')

            content = getOptional(data, 'content')
            _encoding = getOptional(content, 'encoding')  # NOTE NOT USED
            _size = getOptional(content, 'size')
            _data = getOptional(content, 'data')

            headers = getOptional(data, 'headers')
            header_encoding = getOptional(headers, 'encoding')  # NOTE NOT USED
            # NOTE can and will break sometime because headers is optional
            _headers = generateHeadersFromTxnFields(
                getOptional(headers, 'fields'))
            # print(_headers)

            # if _size and ('Content-Length' not in _headers or 'content-length' not in _headers):
            # _headers.update({'Content-Length': _size})  # NOTE temporary solution
        except Exception as e:
            print("Error in parsing {0} response. Error {1}".format(
                metaName, e))
            raise e

        return cls(_status, _reason, _encoding, _size, _data, _headers, _options)

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
