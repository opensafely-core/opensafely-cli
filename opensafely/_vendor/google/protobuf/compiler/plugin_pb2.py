# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/protobuf/compiler/plugin.proto
"""Generated protocol buffer code."""
from opensafely._vendor.google.protobuf.internal import builder as _builder
from opensafely._vendor.google.protobuf import descriptor as _descriptor
from opensafely._vendor.google.protobuf import descriptor_pool as _descriptor_pool
from opensafely._vendor.google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from opensafely._vendor.google.protobuf import descriptor_pb2 as google_dot_protobuf_dot_descriptor__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%google/protobuf/compiler/plugin.proto\x12\x18google.protobuf.compiler\x1a google/protobuf/descriptor.proto\"F\n\x07Version\x12\r\n\x05major\x18\x01 \x01(\x05\x12\r\n\x05minor\x18\x02 \x01(\x05\x12\r\n\x05patch\x18\x03 \x01(\x05\x12\x0e\n\x06suffix\x18\x04 \x01(\t\"\xba\x01\n\x14\x43odeGeneratorRequest\x12\x18\n\x10\x66ile_to_generate\x18\x01 \x03(\t\x12\x11\n\tparameter\x18\x02 \x01(\t\x12\x38\n\nproto_file\x18\x0f \x03(\x0b\x32$.google.protobuf.FileDescriptorProto\x12;\n\x10\x63ompiler_version\x18\x03 \x01(\x0b\x32!.google.protobuf.compiler.Version\"\xc1\x02\n\x15\x43odeGeneratorResponse\x12\r\n\x05\x65rror\x18\x01 \x01(\t\x12\x1a\n\x12supported_features\x18\x02 \x01(\x04\x12\x42\n\x04\x66ile\x18\x0f \x03(\x0b\x32\x34.google.protobuf.compiler.CodeGeneratorResponse.File\x1a\x7f\n\x04\x46ile\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x17\n\x0finsertion_point\x18\x02 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x0f \x01(\t\x12?\n\x13generated_code_info\x18\x10 \x01(\x0b\x32\".google.protobuf.GeneratedCodeInfo\"8\n\x07\x46\x65\x61ture\x12\x10\n\x0c\x46\x45\x41TURE_NONE\x10\x00\x12\x1b\n\x17\x46\x45\x41TURE_PROTO3_OPTIONAL\x10\x01\x42W\n\x1c\x63om.google.protobuf.compilerB\x0cPluginProtosZ)google.golang.org/protobuf/types/pluginpb')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'google.protobuf.compiler.plugin_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\034com.google.protobuf.compilerB\014PluginProtosZ)google.golang.org/protobuf/types/pluginpb'
  _VERSION._serialized_start=101
  _VERSION._serialized_end=171
  _CODEGENERATORREQUEST._serialized_start=174
  _CODEGENERATORREQUEST._serialized_end=360
  _CODEGENERATORRESPONSE._serialized_start=363
  _CODEGENERATORRESPONSE._serialized_end=684
  _CODEGENERATORRESPONSE_FILE._serialized_start=499
  _CODEGENERATORRESPONSE_FILE._serialized_end=626
  _CODEGENERATORRESPONSE_FEATURE._serialized_start=628
  _CODEGENERATORRESPONSE_FEATURE._serialized_end=684
# @@protoc_insertion_point(module_scope)
