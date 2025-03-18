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
# source: google/type/postal_address.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database
from opensafely._vendor.google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n google/type/postal_address.proto\x12\x0bgoogle.type"\xfd\x01\n\rPostalAddress\x12\x10\n\x08revision\x18\x01 \x01(\x05\x12\x13\n\x0bregion_code\x18\x02 \x01(\t\x12\x15\n\rlanguage_code\x18\x03 \x01(\t\x12\x13\n\x0bpostal_code\x18\x04 \x01(\t\x12\x14\n\x0csorting_code\x18\x05 \x01(\t\x12\x1b\n\x13\x61\x64ministrative_area\x18\x06 \x01(\t\x12\x10\n\x08locality\x18\x07 \x01(\t\x12\x13\n\x0bsublocality\x18\x08 \x01(\t\x12\x15\n\raddress_lines\x18\t \x03(\t\x12\x12\n\nrecipients\x18\n \x03(\t\x12\x14\n\x0corganization\x18\x0b \x01(\tBx\n\x0f\x63om.google.typeB\x12PostalAddressProtoP\x01ZFgoogle.golang.org/genproto/googleapis/type/postaladdress;postaladdress\xf8\x01\x01\xa2\x02\x03GTPb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(
    DESCRIPTOR, "google.type.postal_address_pb2", _globals
)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals["DESCRIPTOR"]._options = None
    _globals[
        "DESCRIPTOR"
    ]._serialized_options = b"\n\017com.google.typeB\022PostalAddressProtoP\001ZFgoogle.golang.org/genproto/googleapis/type/postaladdress;postaladdress\370\001\001\242\002\003GTP"
    _globals["_POSTALADDRESS"]._serialized_start = 50
    _globals["_POSTALADDRESS"]._serialized_end = 303
# @@protoc_insertion_point(module_scope)
