# -*- coding: utf-8 -*-

# Copyright 2025 Google LLC
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
# source: google/api/quota.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database
from opensafely._vendor.google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x16google/api/quota.proto\x12\ngoogle.api"]\n\x05Quota\x12&\n\x06limits\x18\x03 \x03(\x0b\x32\x16.google.api.QuotaLimit\x12,\n\x0cmetric_rules\x18\x04 \x03(\x0b\x32\x16.google.api.MetricRule"\x91\x01\n\nMetricRule\x12\x10\n\x08selector\x18\x01 \x01(\t\x12=\n\x0cmetric_costs\x18\x02 \x03(\x0b\x32\'.google.api.MetricRule.MetricCostsEntry\x1a\x32\n\x10MetricCostsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x03:\x02\x38\x01"\x95\x02\n\nQuotaLimit\x12\x0c\n\x04name\x18\x06 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x15\n\rdefault_limit\x18\x03 \x01(\x03\x12\x11\n\tmax_limit\x18\x04 \x01(\x03\x12\x11\n\tfree_tier\x18\x07 \x01(\x03\x12\x10\n\x08\x64uration\x18\x05 \x01(\t\x12\x0e\n\x06metric\x18\x08 \x01(\t\x12\x0c\n\x04unit\x18\t \x01(\t\x12\x32\n\x06values\x18\n \x03(\x0b\x32".google.api.QuotaLimit.ValuesEntry\x12\x14\n\x0c\x64isplay_name\x18\x0c \x01(\t\x1a-\n\x0bValuesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x03:\x02\x38\x01\x42l\n\x0e\x63om.google.apiB\nQuotaProtoP\x01ZEgoogle.golang.org/genproto/googleapis/api/serviceconfig;serviceconfig\xa2\x02\x04GAPIb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "google.api.quota_pb2", _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals["DESCRIPTOR"]._options = None
    _globals[
        "DESCRIPTOR"
    ]._serialized_options = b"\n\016com.google.apiB\nQuotaProtoP\001ZEgoogle.golang.org/genproto/googleapis/api/serviceconfig;serviceconfig\242\002\004GAPI"
    _globals["_METRICRULE_METRICCOSTSENTRY"]._options = None
    _globals["_METRICRULE_METRICCOSTSENTRY"]._serialized_options = b"8\001"
    _globals["_QUOTALIMIT_VALUESENTRY"]._options = None
    _globals["_QUOTALIMIT_VALUESENTRY"]._serialized_options = b"8\001"
    _globals["_QUOTA"]._serialized_start = 38
    _globals["_QUOTA"]._serialized_end = 131
    _globals["_METRICRULE"]._serialized_start = 134
    _globals["_METRICRULE"]._serialized_end = 279
    _globals["_METRICRULE_METRICCOSTSENTRY"]._serialized_start = 229
    _globals["_METRICRULE_METRICCOSTSENTRY"]._serialized_end = 279
    _globals["_QUOTALIMIT"]._serialized_start = 282
    _globals["_QUOTALIMIT"]._serialized_end = 559
    _globals["_QUOTALIMIT_VALUESENTRY"]._serialized_start = 514
    _globals["_QUOTALIMIT_VALUESENTRY"]._serialized_end = 559
# @@protoc_insertion_point(module_scope)
