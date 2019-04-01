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
from trlib.parser.attribute import Attribute


class Content:
    attributes = [
        Attribute("encoding", str),  # "plain","uri","esc_json"
        Attribute("size", int),
        Attribute("data", str),
    ]

    content_buffer: str = "ab"*(64*1024)  # starting buffer

    def __init__(self, content: Optional[str] = None, size: Optional[int] = None, encoding: Optional[str] = None) -> None:
        self._content: Optional[str] = content
        self._length: Optional[int] = None
        content_length = size
        if content and content_length and (len(content) != content_length):
            raise RuntimeError(
                "The length of content does not equal the content_length value provided")
        elif content and not content_length:
            self._length = len(content)
        else:
            self._length = content_length

        if self._length and self._length > len(Content.content_buffer):
            Content.content_buffer = "ab"*int((self._length/2)+1)

        self._encoding: Optional[str] = encoding

    @property
    def content(self) -> str:
        return Content.content_buffer[0:self._length]

    @property
    def encoding(self):
        return self._encoding
