


import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='hl7server.proto',
  package='hl7server',
  syntax='proto3',
  serialized_options=_b('\n\027com.smartcity.hl7serverB\016HL7ServerProtoP\001\242\002\003HLW'),
  serialized_pb=_b(
    '\n\x0fhl7server.proto\x12\thl7server\"4\n\x0eMessageRequest\x12\x0f\n\x07\x63ommand\x18\x01 \x01(\t\x12\x11\n\tmessageID\x18\x02 \x01(\x05\",\n\x0cMessageReply\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x0e\n\x06status\x18\x02 \x01(\t2T\n\rCommunication\x12\x43\n\x0b\x45xecCommand\x12\x19.hl7server.MessageRequest\x1a\x17.hl7server.MessageReply\"\x00\x42\x31\n\x17\x63om.smartcity.hl7serverB\x0eHL7ServerProtoP\x01\xa2\x02\x03HLWb\x06proto3')

)




_MESSAGEREQUEST = _descriptor.Descriptor(
  name='MessageRequest',
  full_name='hl7server.MessageRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='command', full_name='hl7server.MessageRequest.command', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='messageID', full_name='hl7server.MessageRequest.messageID', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=30,
  serialized_end=82,
)


_MESSAGEREPLY = _descriptor.Descriptor(
  name='MessageReply',
  full_name='hl7server.MessageReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='code', full_name='hl7server.MessageReply.code', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='status', full_name='hl7server.MessageReply.status', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=84,
  serialized_end=128,
)

DESCRIPTOR.message_types_by_name['MessageRequest'] = _MESSAGEREQUEST
DESCRIPTOR.message_types_by_name['MessageReply'] = _MESSAGEREPLY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MessageRequest = _reflection.GeneratedProtocolMessageType('MessageRequest', (_message.Message,), dict(
  DESCRIPTOR = _MESSAGEREQUEST,
  __module__ = 'hl7server_pb2'
  # @@protoc_insertion_point(class_scope:hl7server.MessageRequest)
  ))
_sym_db.RegisterMessage(MessageRequest)

MessageReply = _reflection.GeneratedProtocolMessageType('MessageReply', (_message.Message,), dict(
  DESCRIPTOR = _MESSAGEREPLY,
  __module__ = 'hl7server_pb2'
  # @@protoc_insertion_point(class_scope:hl7server.MessageReply)
  ))
_sym_db.RegisterMessage(MessageReply)


DESCRIPTOR._options = None

_COMMUNICATION = _descriptor.ServiceDescriptor(
  name='Communication',
  full_name='hl7server.Communication',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=130,
  serialized_end=214,
  methods=[
  _descriptor.MethodDescriptor(
    name='ExecCommand',
    full_name='hl7server.Communication.ExecCommand',
    index=0,
    containing_service=None,
    input_type=_MESSAGEREQUEST,
    output_type=_MESSAGEREPLY,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_COMMUNICATION)

DESCRIPTOR.services_by_name['Communication'] = _COMMUNICATION

# @@protoc_insertion_point(module_scope)
