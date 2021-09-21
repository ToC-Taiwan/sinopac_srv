# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: trade_bot_protobuf/src/entiretick.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='trade_bot_protobuf/src/entiretick.proto',
  package='entiretick_protobuf',
  syntax='proto3',
  serialized_options=b'Z\025pkg/models/entiretick',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\'trade_bot_protobuf/src/entiretick.proto\x12\x13\x65ntiretick_protobuf\"H\n\x12\x45ntireTickArrProto\x12\x32\n\x04\x64\x61ta\x18\x01 \x03(\x0b\x32$.entiretick_protobuf.EntireTickProto\"\x8a\x01\n\x0f\x45ntireTickProto\x12\n\n\x02ts\x18\x01 \x01(\x03\x12\r\n\x05\x63lose\x18\x02 \x01(\x01\x12\x0e\n\x06volume\x18\x03 \x01(\x03\x12\x11\n\tbid_price\x18\x04 \x01(\x01\x12\x12\n\nbid_volume\x18\x05 \x01(\x03\x12\x11\n\task_price\x18\x06 \x01(\x01\x12\x12\n\nask_volume\x18\x07 \x01(\x03\x42\x17Z\x15pkg/models/entiretickb\x06proto3'
)




_ENTIRETICKARRPROTO = _descriptor.Descriptor(
  name='EntireTickArrProto',
  full_name='entiretick_protobuf.EntireTickArrProto',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='data', full_name='entiretick_protobuf.EntireTickArrProto.data', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=64,
  serialized_end=136,
)


_ENTIRETICKPROTO = _descriptor.Descriptor(
  name='EntireTickProto',
  full_name='entiretick_protobuf.EntireTickProto',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='ts', full_name='entiretick_protobuf.EntireTickProto.ts', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='close', full_name='entiretick_protobuf.EntireTickProto.close', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='volume', full_name='entiretick_protobuf.EntireTickProto.volume', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='bid_price', full_name='entiretick_protobuf.EntireTickProto.bid_price', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='bid_volume', full_name='entiretick_protobuf.EntireTickProto.bid_volume', index=4,
      number=5, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ask_price', full_name='entiretick_protobuf.EntireTickProto.ask_price', index=5,
      number=6, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ask_volume', full_name='entiretick_protobuf.EntireTickProto.ask_volume', index=6,
      number=7, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=139,
  serialized_end=277,
)

_ENTIRETICKARRPROTO.fields_by_name['data'].message_type = _ENTIRETICKPROTO
DESCRIPTOR.message_types_by_name['EntireTickArrProto'] = _ENTIRETICKARRPROTO
DESCRIPTOR.message_types_by_name['EntireTickProto'] = _ENTIRETICKPROTO
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

EntireTickArrProto = _reflection.GeneratedProtocolMessageType('EntireTickArrProto', (_message.Message,), {
  'DESCRIPTOR' : _ENTIRETICKARRPROTO,
  '__module__' : 'trade_bot_protobuf.src.entiretick_pb2'
  # @@protoc_insertion_point(class_scope:entiretick_protobuf.EntireTickArrProto)
  })
_sym_db.RegisterMessage(EntireTickArrProto)

EntireTickProto = _reflection.GeneratedProtocolMessageType('EntireTickProto', (_message.Message,), {
  'DESCRIPTOR' : _ENTIRETICKPROTO,
  '__module__' : 'trade_bot_protobuf.src.entiretick_pb2'
  # @@protoc_insertion_point(class_scope:entiretick_protobuf.EntireTickProto)
  })
_sym_db.RegisterMessage(EntireTickProto)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
