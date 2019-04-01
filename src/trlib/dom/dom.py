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

from trlib.parser import Attribute, parse

from typing import Any,List
from .session import Session

class DOM_1_0_1:
    ''' this class only exists to help with translating a json structure to object form'''
    attributes=[
        Attribute("meta",dict),
        Attribute("sessions",List[Session],required=True)
    ]

    def __init__(self, sessions:List[Session], meta):
        self._sessions = sessions
        self._meta = meta

    @property
    def sessions(self) -> List[Session]:
        return self._sessions

    @property
    def meta(self) -> dict:
        return self._meta

Dom = DOM_1_0_1
