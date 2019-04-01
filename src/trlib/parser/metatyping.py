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

from typing import Any, Dict, List, Optional, Sequence, Set, Union

def typing_name(tobj) -> Union[str,None]:
    # ideal case for py 3.7
    if hasattr(tobj, "_name") and repr(tobj).startswith("typing."):
        return tobj._name
    # non ideal case py 3.6 or below
    elif repr(tobj).startswith("typing."):
        if hasattr(tobj, "__origin__") and tobj.__origin__:
            return str(tobj.__origin__)[len("typing."):]
        else:
            return repr(tobj)[len("typing."):]
    return None

def is_typing_obj(tobj) -> bool:
    return repr(tobj).startswith("typing.")


def istypeof(obj, typeinfo):
    type_list = []
    typing_list = []
    obj_name = typing_name(obj)
    if isinstance(typeinfo, tuple):
        for t in typeinfo:
            if is_typing_obj(t):
                typing_list.append(typing_name(t))
            else:
                type_list.append(t)
    elif is_typing_obj(typeinfo):
        typing_list.append(typing_name(typeinfo))
    else:
        type_list.append(typeinfo)

    if obj_name in typing_list:
        return True
    elif not obj_name and isinstance(obj, tuple(type_list)):
        return True
    elif not obj_name and obj in (type_list):
        return True
    return False

def check_type(obj: Any, typeinfo) -> bool:

    if istypeof(typeinfo, List) and istypeof(obj, list):
        return check_types_seq(obj, typeinfo.__args__)
    elif istypeof(typeinfo, Set) and istypeof(obj, set):
        return check_types_seq(obj, typeinfo.__args__)
    elif istypeof(typeinfo, Optional):
        return check_types_anyof(obj, typeinfo.__args__)
    elif istypeof(typeinfo, Union):
        return check_types_anyof(obj, typeinfo.__args__)
    elif istypeof(typeinfo, Dict) and istypeof(obj, dict):
        return check_types_mapping(obj, typeinfo.__args__)
    else:
        return istypeof(obj, typeinfo)

def check_types_seq(objs, til: tuple) -> bool:
    for obj in objs:
        if not check_types_anyof(obj, til):
            return False
    return True


def check_types_mapping(objs, typeinfo) -> bool:
    for k, v in objs.items():
        if not check_type(k, typeinfo.__args__[0]) or not check_type(k, typeinfo.__args__[1]):
            return False
    return True


def check_types_anyof(obj: Any, til: tuple) -> bool:
    for typeinfo in til:
        if check_type(obj, typeinfo):
            return True
    return False

def is_type_seq(typeinfo):
    '''
    returns true that the type is a seqence of some kind
    At the moment this means it List, Set,list or set type
    '''
    return istypeof(typeinfo, (Set, List, set, list))


def is_type_mapping(typeinfo):
    '''
    returns true that the type is a mapping object of some kind
    At the moment this means it Dict or dict type
    '''
    return istypeof(typeinfo, (Dict, dict))


def is_setof_types(typeinfo):
    '''
    returns true that the type is a set of types
    At the moment this means it Optional, Union
    '''
    return istypeof(typeinfo, (Optional, Union))

def get_sub_types(typeinfo):
    '''
    get the subtypes, if any else return parent type
    '''
    # if this is tuple or list
    if isinstance(typeinfo, (tuple, list)):
        return typeinfo
    try:
        return typeinfo.__args__
    except:
        return typeinfo


def get_type(typeinfo):
    if istypeof(typeinfo, List):
        return list
    elif istypeof(typeinfo, Set):
        return set
    elif istypeof(typeinfo, Dict):
        return dict
    elif istypeof(typeinfo, type):
        return
    else:
        return None