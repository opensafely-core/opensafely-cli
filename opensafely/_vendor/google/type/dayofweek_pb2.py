# -*- coding: utf-8 -*-

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/type/dayofweek.proto
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf.internal import enum_type_wrapper
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import message as _message
from opensafely._vendor.google.protobuf import reflection as _reflection
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b"\n\x1bgoogle/type/dayofweek.proto\x12\x0bgoogle.type*\x84\x01\n\tDayOfWeek\x12\x1b\n\x17\x44\x41Y_OF_WEEK_UNSPECIFIED\x10\x00\x12\n\n\x06MONDAY\x10\x01\x12\x0b\n\x07TUESDAY\x10\x02\x12\r\n\tWEDNESDAY\x10\x03\x12\x0c\n\x08THURSDAY\x10\x04\x12\n\n\x06\x46RIDAY\x10\x05\x12\x0c\n\x08SATURDAY\x10\x06\x12\n\n\x06SUNDAY\x10\x07\x42i\n\x0f\x63om.google.typeB\x0e\x44\x61yOfWeekProtoP\x01Z>google.golang.org/genproto/googleapis/type/dayofweek;dayofweek\xa2\x02\x03GTPb\x06proto3"
)

_DAYOFWEEK = DESCRIPTOR.enum_types_by_name["DayOfWeek"]
DayOfWeek = enum_type_wrapper.EnumTypeWrapper(_DAYOFWEEK)
DAY_OF_WEEK_UNSPECIFIED = 0
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6
SUNDAY = 7


if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b"\n\017com.google.typeB\016DayOfWeekProtoP\001Z>google.golang.org/genproto/googleapis/type/dayofweek;dayofweek\242\002\003GTP"
    _DAYOFWEEK._serialized_start = 45
    _DAYOFWEEK._serialized_end = 177
# @@protoc_insertion_point(module_scope)
