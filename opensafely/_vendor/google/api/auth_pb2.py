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
# source: google/api/auth.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database
from opensafely._vendor.google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x15google/api/auth.proto\x12\ngoogle.api"l\n\x0e\x41uthentication\x12-\n\x05rules\x18\x03 \x03(\x0b\x32\x1e.google.api.AuthenticationRule\x12+\n\tproviders\x18\x04 \x03(\x0b\x32\x18.google.api.AuthProvider"\xa9\x01\n\x12\x41uthenticationRule\x12\x10\n\x08selector\x18\x01 \x01(\t\x12,\n\x05oauth\x18\x02 \x01(\x0b\x32\x1d.google.api.OAuthRequirements\x12 \n\x18\x61llow_without_credential\x18\x05 \x01(\x08\x12\x31\n\x0crequirements\x18\x07 \x03(\x0b\x32\x1b.google.api.AuthRequirement"^\n\x0bJwtLocation\x12\x10\n\x06header\x18\x01 \x01(\tH\x00\x12\x0f\n\x05query\x18\x02 \x01(\tH\x00\x12\x10\n\x06\x63ookie\x18\x04 \x01(\tH\x00\x12\x14\n\x0cvalue_prefix\x18\x03 \x01(\tB\x04\n\x02in"\x9a\x01\n\x0c\x41uthProvider\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0e\n\x06issuer\x18\x02 \x01(\t\x12\x10\n\x08jwks_uri\x18\x03 \x01(\t\x12\x11\n\taudiences\x18\x04 \x01(\t\x12\x19\n\x11\x61uthorization_url\x18\x05 \x01(\t\x12.\n\rjwt_locations\x18\x06 \x03(\x0b\x32\x17.google.api.JwtLocation"-\n\x11OAuthRequirements\x12\x18\n\x10\x63\x61nonical_scopes\x18\x01 \x01(\t"9\n\x0f\x41uthRequirement\x12\x13\n\x0bprovider_id\x18\x01 \x01(\t\x12\x11\n\taudiences\x18\x02 \x01(\tBk\n\x0e\x63om.google.apiB\tAuthProtoP\x01ZEgoogle.golang.org/genproto/googleapis/api/serviceconfig;serviceconfig\xa2\x02\x04GAPIb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "google.api.auth_pb2", _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals["DESCRIPTOR"]._options = None
    _globals[
        "DESCRIPTOR"
    ]._serialized_options = b"\n\016com.google.apiB\tAuthProtoP\001ZEgoogle.golang.org/genproto/googleapis/api/serviceconfig;serviceconfig\242\002\004GAPI"
    _globals["_AUTHENTICATION"]._serialized_start = 37
    _globals["_AUTHENTICATION"]._serialized_end = 145
    _globals["_AUTHENTICATIONRULE"]._serialized_start = 148
    _globals["_AUTHENTICATIONRULE"]._serialized_end = 317
    _globals["_JWTLOCATION"]._serialized_start = 319
    _globals["_JWTLOCATION"]._serialized_end = 413
    _globals["_AUTHPROVIDER"]._serialized_start = 416
    _globals["_AUTHPROVIDER"]._serialized_end = 570
    _globals["_OAUTHREQUIREMENTS"]._serialized_start = 572
    _globals["_OAUTHREQUIREMENTS"]._serialized_end = 617
    _globals["_AUTHREQUIREMENT"]._serialized_start = 619
    _globals["_AUTHREQUIREMENT"]._serialized_end = 676
# @@protoc_insertion_point(module_scope)
