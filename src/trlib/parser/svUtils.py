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

G_VERBOSE_LOG = True


def verbose_print(msg, verbose_on=False):
    ''' Print msg if verbose_on is set to True or G_VERBOSE_LOG is set to True'''
    if verbose_on or G_VERBOSE_LOG:
        print(msg)


def getOptional(item, field):
    if item:
        if field in item:
            return item[field]

    return None


def getRequired(item, field):
    if not item:
        raise KeyError(field)

    return item[field]


def generateHeadersFromTxnFields(fields):
    if not fields:
        return None

    headers = {}

    for idx, field in enumerate(fields):
        header = field[0]

        if header not in headers:
            headerVal = field[1]

            for idx2, headerSet in enumerate(fields):
                if idx2 == idx:
                    continue

                if header == headerSet[0]:
                    headerVal += ', {0}'.format(headerSet[1])

            headers[header] = headerVal

    return headers


def generateHeadersFromRequestLine(headerLine):
    if not headerLine:
        return None

    headers = {}

    for pair in headerLine.split("\r\n"):
        # test to get rid of the empty split part that is from \r\n\r\n
        if pair:
            key, val = pair.split(":", 1)

            val = val.strip()

            if key in headers:
                headers[key] = headers[key] + ", {0}".format(val)
            else:
                headers[key] = val

    return headers
