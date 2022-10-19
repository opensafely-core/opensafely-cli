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
# source: google/api/metric.proto
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import message as _message
from opensafely._vendor.google.protobuf import reflection as _reflection
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from opensafely._vendor.google.api import label_pb2 as google_dot_api_dot_label__pb2
from opensafely._vendor.google.api import launch_stage_pb2 as google_dot_api_dot_launch__stage__pb2
from opensafely._vendor.google.protobuf import duration_pb2 as google_dot_protobuf_dot_duration__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x17google/api/metric.proto\x12\ngoogle.api\x1a\x16google/api/label.proto\x1a\x1dgoogle/api/launch_stage.proto\x1a\x1egoogle/protobuf/duration.proto"\x9f\x06\n\x10MetricDescriptor\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x08 \x01(\t\x12+\n\x06labels\x18\x02 \x03(\x0b\x32\x1b.google.api.LabelDescriptor\x12<\n\x0bmetric_kind\x18\x03 \x01(\x0e\x32\'.google.api.MetricDescriptor.MetricKind\x12:\n\nvalue_type\x18\x04 \x01(\x0e\x32&.google.api.MetricDescriptor.ValueType\x12\x0c\n\x04unit\x18\x05 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x06 \x01(\t\x12\x14\n\x0c\x64isplay_name\x18\x07 \x01(\t\x12G\n\x08metadata\x18\n \x01(\x0b\x32\x35.google.api.MetricDescriptor.MetricDescriptorMetadata\x12-\n\x0claunch_stage\x18\x0c \x01(\x0e\x32\x17.google.api.LaunchStage\x12 \n\x18monitored_resource_types\x18\r \x03(\t\x1a\xb0\x01\n\x18MetricDescriptorMetadata\x12\x31\n\x0claunch_stage\x18\x01 \x01(\x0e\x32\x17.google.api.LaunchStageB\x02\x18\x01\x12\x30\n\rsample_period\x18\x02 \x01(\x0b\x32\x19.google.protobuf.Duration\x12/\n\x0cingest_delay\x18\x03 \x01(\x0b\x32\x19.google.protobuf.Duration"O\n\nMetricKind\x12\x1b\n\x17METRIC_KIND_UNSPECIFIED\x10\x00\x12\t\n\x05GAUGE\x10\x01\x12\t\n\x05\x44\x45LTA\x10\x02\x12\x0e\n\nCUMULATIVE\x10\x03"q\n\tValueType\x12\x1a\n\x16VALUE_TYPE_UNSPECIFIED\x10\x00\x12\x08\n\x04\x42OOL\x10\x01\x12\t\n\x05INT64\x10\x02\x12\n\n\x06\x44OUBLE\x10\x03\x12\n\n\x06STRING\x10\x04\x12\x10\n\x0c\x44ISTRIBUTION\x10\x05\x12\t\n\x05MONEY\x10\x06"u\n\x06Metric\x12\x0c\n\x04type\x18\x03 \x01(\t\x12.\n\x06labels\x18\x02 \x03(\x0b\x32\x1e.google.api.Metric.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x42_\n\x0e\x63om.google.apiB\x0bMetricProtoP\x01Z7google.golang.org/genproto/googleapis/api/metric;metric\xa2\x02\x04GAPIb\x06proto3'
)


_METRICDESCRIPTOR = DESCRIPTOR.message_types_by_name["MetricDescriptor"]
_METRICDESCRIPTOR_METRICDESCRIPTORMETADATA = _METRICDESCRIPTOR.nested_types_by_name[
    "MetricDescriptorMetadata"
]
_METRIC = DESCRIPTOR.message_types_by_name["Metric"]
_METRIC_LABELSENTRY = _METRIC.nested_types_by_name["LabelsEntry"]
_METRICDESCRIPTOR_METRICKIND = _METRICDESCRIPTOR.enum_types_by_name["MetricKind"]
_METRICDESCRIPTOR_VALUETYPE = _METRICDESCRIPTOR.enum_types_by_name["ValueType"]
MetricDescriptor = _reflection.GeneratedProtocolMessageType(
    "MetricDescriptor",
    (_message.Message,),
    {
        "MetricDescriptorMetadata": _reflection.GeneratedProtocolMessageType(
            "MetricDescriptorMetadata",
            (_message.Message,),
            {
                "DESCRIPTOR": _METRICDESCRIPTOR_METRICDESCRIPTORMETADATA,
                "__module__": "google.api.metric_pb2"
                # @@protoc_insertion_point(class_scope:google.api.MetricDescriptor.MetricDescriptorMetadata)
            },
        ),
        "DESCRIPTOR": _METRICDESCRIPTOR,
        "__module__": "google.api.metric_pb2"
        # @@protoc_insertion_point(class_scope:google.api.MetricDescriptor)
    },
)
_sym_db.RegisterMessage(MetricDescriptor)
_sym_db.RegisterMessage(MetricDescriptor.MetricDescriptorMetadata)

Metric = _reflection.GeneratedProtocolMessageType(
    "Metric",
    (_message.Message,),
    {
        "LabelsEntry": _reflection.GeneratedProtocolMessageType(
            "LabelsEntry",
            (_message.Message,),
            {
                "DESCRIPTOR": _METRIC_LABELSENTRY,
                "__module__": "google.api.metric_pb2"
                # @@protoc_insertion_point(class_scope:google.api.Metric.LabelsEntry)
            },
        ),
        "DESCRIPTOR": _METRIC,
        "__module__": "google.api.metric_pb2"
        # @@protoc_insertion_point(class_scope:google.api.Metric)
    },
)
_sym_db.RegisterMessage(Metric)
_sym_db.RegisterMessage(Metric.LabelsEntry)

if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b"\n\016com.google.apiB\013MetricProtoP\001Z7google.golang.org/genproto/googleapis/api/metric;metric\242\002\004GAPI"
    _METRICDESCRIPTOR_METRICDESCRIPTORMETADATA.fields_by_name[
        "launch_stage"
    ]._options = None
    _METRICDESCRIPTOR_METRICDESCRIPTORMETADATA.fields_by_name[
        "launch_stage"
    ]._serialized_options = b"\030\001"
    _METRIC_LABELSENTRY._options = None
    _METRIC_LABELSENTRY._serialized_options = b"8\001"
    _METRICDESCRIPTOR._serialized_start = 127
    _METRICDESCRIPTOR._serialized_end = 926
    _METRICDESCRIPTOR_METRICDESCRIPTORMETADATA._serialized_start = 554
    _METRICDESCRIPTOR_METRICDESCRIPTORMETADATA._serialized_end = 730
    _METRICDESCRIPTOR_METRICKIND._serialized_start = 732
    _METRICDESCRIPTOR_METRICKIND._serialized_end = 811
    _METRICDESCRIPTOR_VALUETYPE._serialized_start = 813
    _METRICDESCRIPTOR_VALUETYPE._serialized_end = 926
    _METRIC._serialized_start = 928
    _METRIC._serialized_end = 1045
    _METRIC_LABELSENTRY._serialized_start = 1000
    _METRIC_LABELSENTRY._serialized_end = 1045
# @@protoc_insertion_point(module_scope)
