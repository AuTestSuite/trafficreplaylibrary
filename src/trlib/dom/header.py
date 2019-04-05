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
from typing import Dict, List, Optional, Tuple, Union, cast

from trlib.parser.attribute import Attribute

from .field import Field


class Header:
    ''' This represents a header we would receive and want to test against'''
    attributes = [
        Attribute("encoding", str),  # "plain","uri","esc_json"
        Attribute("fields", List[Field], required=True),
    ]

    def __init__(self, fields: List[Field], encoding: Optional[str] = None):
        self._encoding: Optional[str] = None
        self._fields: List[Field] = fields
        self._is_chunked: bool = False
        tmp = {}
        for field in self._fields:
            key = cast(str, field.key)  # Header key
            val = field.value  # Header value
            # optional header test logic (e->exists, != not equal to, == equal to [defaults] )
            com = field.comp
            tmp[key] = (val, com)
            if key.lower() == 'transfer-encoding' and val.lower() == 'chunked':
                self._is_chunked = True

        self._fields_dict: Dict[str, Tuple[str, str]] = tmp
        self._headers_dict: Dict[str, str] = {v[0]: v[1] for v in self._fields}
        self._tuples = [(v[0], v[1]) for v in self._fields]

    @property
    def isChunkedEncoded(self) -> bool:
        return self._is_chunked

    @property
    def encoding(self) -> Optional[str]:
        return self._encoding

    @property
    def fields(self) -> List[Field]:
        ''' return fields as it was defined in the yaml file'''
        return self._fields

    @property
    def asDict(self) -> Dict[str, Tuple[str, str]]:
        ''' Return fields as a dictionary of key value pairs'''
        return self._fields_dict

    @property
    def asHeaderDict(self) -> Dict[str, str]:
        ''' Return fields as a dictionary of key value pairs'''
        return self._headers_dict
