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


from typing import Any, Optional


class Attribute(object):
    def __init__(self, name: str, type_info, default: Any = None, required: bool = False, argument_name:Optional[str]=None):
        self._name = name
        self._type = type_info
        self._default = default
        self._required = required
        self._arg_name = argument_name

    @property
    def typeinfo(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def default(self):
        return self._default

    @property
    def required(self):
        return self._required

    @property
    def argument_name(self) -> str:
        return self._arg_name if self._arg_name else self.name







