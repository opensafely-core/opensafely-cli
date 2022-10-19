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
# source: google/type/localized_text.proto
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import message as _message
from opensafely._vendor.google.protobuf import reflection as _reflection
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n google/type/localized_text.proto\x12\x0bgoogle.type"4\n\rLocalizedText\x12\x0c\n\x04text\x18\x01 \x01(\t\x12\x15\n\rlanguage_code\x18\x02 \x01(\tBz\n\x0f\x63om.google.typeB\x12LocalizedTextProtoP\x01ZHgoogle.golang.org/genproto/googleapis/type/localized_text;localized_text\xf8\x01\x01\xa2\x02\x03GTPb\x06proto3'
)


_LOCALIZEDTEXT = DESCRIPTOR.message_types_by_name["LocalizedText"]
LocalizedText = _reflection.GeneratedProtocolMessageType(
    "LocalizedText",
    (_message.Message,),
    {
        "DESCRIPTOR": _LOCALIZEDTEXT,
        "__module__": "google.type.localized_text_pb2"
        # @@protoc_insertion_point(class_scope:google.type.LocalizedText)
    },
)
_sym_db.RegisterMessage(LocalizedText)

if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b"\n\017com.google.typeB\022LocalizedTextProtoP\001ZHgoogle.golang.org/genproto/googleapis/type/localized_text;localized_text\370\001\001\242\002\003GTP"
    _LOCALIZEDTEXT._serialized_start = 49
    _LOCALIZEDTEXT._serialized_end = 101
# @@protoc_insertion_point(module_scope)
