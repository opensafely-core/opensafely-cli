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
# source: google/api/client.proto
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import message as _message
from opensafely._vendor.google.protobuf import reflection as _reflection
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from opensafely._vendor.google.protobuf import descriptor_pb2 as google_dot_protobuf_dot_descriptor__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b"\n\x17google/api/client.proto\x12\ngoogle.api\x1a google/protobuf/descriptor.proto:9\n\x10method_signature\x12\x1e.google.protobuf.MethodOptions\x18\x9b\x08 \x03(\t:6\n\x0c\x64\x65\x66\x61ult_host\x12\x1f.google.protobuf.ServiceOptions\x18\x99\x08 \x01(\t:6\n\x0coauth_scopes\x12\x1f.google.protobuf.ServiceOptions\x18\x9a\x08 \x01(\tBi\n\x0e\x63om.google.apiB\x0b\x43lientProtoP\x01ZAgoogle.golang.org/genproto/googleapis/api/annotations;annotations\xa2\x02\x04GAPIb\x06proto3"
)


METHOD_SIGNATURE_FIELD_NUMBER = 1051
method_signature = DESCRIPTOR.extensions_by_name["method_signature"]
DEFAULT_HOST_FIELD_NUMBER = 1049
default_host = DESCRIPTOR.extensions_by_name["default_host"]
OAUTH_SCOPES_FIELD_NUMBER = 1050
oauth_scopes = DESCRIPTOR.extensions_by_name["oauth_scopes"]

if _descriptor._USE_C_DESCRIPTORS == False:
    google_dot_protobuf_dot_descriptor__pb2.MethodOptions.RegisterExtension(
        method_signature
    )
    google_dot_protobuf_dot_descriptor__pb2.ServiceOptions.RegisterExtension(
        default_host
    )
    google_dot_protobuf_dot_descriptor__pb2.ServiceOptions.RegisterExtension(
        oauth_scopes
    )

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b"\n\016com.google.apiB\013ClientProtoP\001ZAgoogle.golang.org/genproto/googleapis/api/annotations;annotations\242\002\004GAPI"
# @@protoc_insertion_point(module_scope)