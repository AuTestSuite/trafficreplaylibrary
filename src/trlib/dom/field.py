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

from typing import Dict, Optional, Tuple, Union
from trlib.parser.attribute import Attribute

class Field:
    ''' This represents a header we would receive and want to test against'''
    attribute_list = [
        Attribute("key",str,required=True),
        Attribute("value",str,required=True),
        Attribute("comp",str, default = "=="), # validate e->exists, != not equal to, == equal to [defaults] 
    ]

    def __init__(self,key,value,comp):
        self._key = key
        self._value = value
        self._comp = comp
        
    def __getitem__(self,indx):
        if indx == 0:
            return self._key
        elif indx == 1:
            return self._value
        elif indx == 2:
            return self._comp
        raise IndexError("index out of range")

    @property
    def key(self) -> Optional[str]:
        return self._key
    @property
    def value(self) -> Optional[str]:
        return self._value
    @property
    def comp(self) -> Optional[str]:
        return self._comp
    