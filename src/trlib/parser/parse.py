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
import itertools
from typing import Any, Dict, List, Optional, Sequence, Set, Union
from .metatyping import istypeof, is_type_mapping, is_type_seq, get_sub_types, get_type, is_setof_types


class ParseError(RuntimeError):
    def __init__(self, str):
        super().__init__(str)


def parse(data, typeinfo, default=None):
    if istypeof(data, list) and (is_type_seq(typeinfo) or hasattr(typeinfo, "attribute_list")):
        tmp = parse_seq(data, typeinfo, default)
    elif istypeof(data, dict) and is_type_mapping(typeinfo):
        tmp = parse_mapping(data, typeinfo)
    elif is_setof_types(typeinfo):
        tmp = parse_setof(data, typeinfo)
    elif istypeof(typeinfo, type) or hasattr(typeinfo, '__class__'):
        tmp = parse_object(data, typeinfo, default)
    else:
        raise ParseError("Unknown Type")
    return tmp


def parse_mapping(data, typeinfo):
    if istypeof(typeinfo, dict):
        return data
    else:  # fix me later
        return data


def parse_setof(data, typeinfo):
    '''
    parse the json object based on that it is one of the known types
    '''
    # get the subtypes
    types = get_sub_types(typeinfo)
    for t in types:
        try:
            # Try to parse the object as this type
            obj = parse(data, t)
            return obj
        except ParseError:
            # did not
            pass
    raise ParseError("Could not match to any of the types: {}".format(types))


def parse_seq(data, typeinfo, default):
    '''
    create a seqence of objects
    '''
    if not istypeof(data, list):
        raise ParseError("data must be a list")

    if not istypeof(typeinfo, (Set, List)) and not hasattr(typeinfo, "attribute_list"):
        raise ParseError(
            "typeinfo must be typing.List,typing.Set or have cls.attribute_list")
    elif hasattr(typeinfo, "attribute_list"):
        # in this case we have an object in which we defined a set of attributes in the order we expect
        # to get them. At the moment we have no logic for non-fixed set of attributes. We can view this case
        # as if it was a tuple
        attributes = typeinfo.attribute_list
        items = []
        for item, attr in itertools.zip_longest(data, attributes):
            if item is None:
                item = attr.default
            retobj = parse(item, attr.typeinfo)
            items.append(retobj)
        return typeinfo(*items)
    else:
        types = get_sub_types(typeinfo)
        seq_type = get_type(typeinfo)
        values = []
        for d in data:
            tmp = parse_setof(d, types)
            values.append(tmp)
        return seq_type(values)


def parse_object(data, typeinfo, default):
    '''
    parses data as if it was the provided type
    The type itself is type basic builtin such
    as a int or str or is a more complex object
    it cannot however be a mapping or seqence type
    Anything else is an error undefined
    '''

    if istypeof(data, (str, int, float, bytes)):
        return typeinfo(data)
    elif istypeof(data, dict):
        if not hasattr(typeinfo, "attributes"):
            raise ParseError("Type must have attributes list")
        typevalues = {}
        for k, v in data.items():
            match = False
            for attr in typeinfo.attributes:
                if attr.name == k:
                    typevalues[attr.argument_name] = parse(v, attr.typeinfo)
                    match = True
                    break
            if not match:
                print("Warning: {} is not a known value. Skipping...".format(k))
        return typeinfo(**typevalues)
    else:
        raise ParseError("Invaid type defined to parse")
