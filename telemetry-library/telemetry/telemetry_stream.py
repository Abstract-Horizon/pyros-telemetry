################################################################################
# Copyright (C) 2016-2020 Abstract Horizon
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License v2.0
# which accompanies this distribution, and is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#    Daniel Sendula - initial API and implementation
#
#################################################################################


import struct

STREAM_ID_BYTE = 0
STREAM_ID_WORD = 1
STREAM_SIZE_BYTE = 0
STREAM_SIZE_WORD = 2
STREAM_SIZE_LONG = 4

TYPE_BYTE = 'b'
TYPE_WORD = 'w'
TYPE_INT = 'i'
TYPE_LONG = 'l'
TYPE_FLOAT = 'f'
TYPE_DOUBLE = 'd'
TYPE_STRING = 's'
TYPE_BYTES = 'a'


class TelemetryStreamField:
    def __init__(self, name, field_type, size):
        self.name = name
        self.field_type = field_type
        self.field_size = size

    def size(self, _value):
        return self.field_size

    def _store(self, buffer, ptr, _value):
        return ptr + self.field_size

    def pack_format(self):
        return None

    def to_json(self):
        return "\"type\" : \"" + self.field_type + "\""

    def __eq__(self, other):
        if isinstance(other, TelemetryStreamField):
            return self.name == other.name and self.field_type == other.field_type
        return False

    def from_string(self, s):
        return s


class TelemetryStreamByteField(TelemetryStreamField):
    def __init__(self, name, signed=False):
        super(TelemetryStreamByteField, self).__init__(name, TYPE_BYTE, 1)
        self.signed = signed

    def _store(self, buffer, ptr, value):
        if self.signed:
            buffer[ptr] = struct.pack('b', value)
        else:
            buffer[ptr] = struct.pack('B', value)
        return ptr + self.field_size

    def pack_format(self):
        return 'b' if self.signed else 'B'

    def to_json(self):
        return super(TelemetryStreamByteField, self).to_json() + ", \"signed\" : " + str(self.signed).lower()

    def __eq__(self, other):
        if isinstance(other, TelemetryStreamByteField):
            return super(TelemetryStreamByteField, self).__eq__(other) and self.signed == other.signed
        return False

    def from_string(self, s):
        return int(s)


class TelemetryStreamWordField(TelemetryStreamField):
    def __init__(self, name, signed=False):
        super(TelemetryStreamWordField, self).__init__(name, TYPE_WORD, 2)
        self.signed = signed

    def _store(self, buffer, ptr, value):
        if self.signed:
            buffer[ptr:ptr+2] = struct.pack('h', value)
        else:
            buffer[ptr:ptr+2] = struct.pack('H', value)
        return ptr + self.field_size

    def pack_format(self):
        return 'h' if self.signed else 'H'

    def to_json(self):
        return super(TelemetryStreamWordField, self).to_json() + ", \"signed\" : " + str(self.signed).lower()

    def __eq__(self, other):
        if isinstance(other, TelemetryStreamWordField):
            return super(TelemetryStreamWordField, self).__eq__(other) and self.signed == other.signed
        return False

    def from_string(self, s):
        return int(s)


class TelemetryStreamIntField(TelemetryStreamField):
    def __init__(self, name, signed=False):
        super(TelemetryStreamIntField, self).__init__(name, TYPE_INT, 4)
        self.signed = signed

    def _store(self, buffer, ptr, value):
        if self.signed:
            buffer[ptr:ptr+4] = struct.pack('i', value)
        else:
            buffer[ptr:ptr+4] = struct.pack('I', value)
        return ptr + self.field_size

    def pack_format(self):
        return 'i' if self.signed else 'I'

    def to_json(self):
        return super(TelemetryStreamIntField, self).to_json() + ", \"signed\" : " + str(self.signed).lower()

    def __eq__(self, other):
        if isinstance(other, TelemetryStreamIntField):
            return super(TelemetryStreamIntField, self).__eq__(other) and self.signed == other.signed
        return False

    def from_string(self, s):
        return int(s)


class TelemetryStreamLongField(TelemetryStreamField):
    def __init__(self, name, signed=False):
        super(TelemetryStreamLongField, self).__init__(name, TYPE_LONG, 8)
        self.signed = signed

    def _store(self, buffer, ptr, value):
        if self.signed:
            buffer[ptr:ptr+8] = struct.pack('q', value)
        else:
            buffer[ptr:ptr+8] = struct.pack('Q', value)
        return ptr + self.field_size

    def pack_format(self):
        return 'q' if self.signed else 'Q'

    def to_json(self):
        return super(TelemetryStreamLongField, self).to_json() + ", \"signed\" : " + str(self.signed).lower()

    def __eq__(self, other):
        if isinstance(other, TelemetryStreamLongField):
            return super(TelemetryStreamLongField, self).__eq__(other) and self.signed == other.signed
        return False

    def from_string(self, s):
        return int(s)


class TelemetryStreamFloatField(TelemetryStreamField):
    def __init__(self, name):
        super(TelemetryStreamFloatField, self).__init__(name, TYPE_FLOAT, 4)

    def _store(self, buffer, ptr, value):
        buffer[ptr:ptr+4] = struct.pack('f', value)
        return ptr + self.field_size

    def pack_format(self):
        return 'f'

    def from_string(self, s):
        return float(s)


class TelemetryStreamDoubleField(TelemetryStreamField):
    def __init__(self, name):
        super(TelemetryStreamDoubleField, self).__init__(name, TYPE_DOUBLE, 8)

    def _store(self, buffer, ptr, value):
        buffer[ptr:ptr+8] = struct.pack('d', value)
        return ptr + self.field_size

    def pack_format(self):
        return 'd'

    def from_string(self, s):
        return float(s)


class TelemetryStreamTimestampField(TelemetryStreamField):
    def __init__(self, name):
        super(TelemetryStreamTimestampField, self).__init__(name, TYPE_DOUBLE, 8)

    def _store(self, buffer, ptr, value):
        buffer[ptr:ptr+8] = struct.pack('d', value)
        return ptr + self.field_size

    def pack_format(self):
        return 'd'

    def from_string(self, s):
        return float(s)


class TelemetryStreamStringField(TelemetryStreamField):
    def __init__(self, name, size):
        super(TelemetryStreamStringField, self).__init__(name, TYPE_STRING, size)

    def _store(self, buffer, ptr, value):
        _length = len(value)
        buffer[ptr:ptr+self.field_size] = struct.pack(str(self.field_size) + 'd', value)
        return ptr + self.field_size

    def pack_format(self):
        return str(self.field_size) + 's'

    def to_json(self):
        return super(TelemetryStreamStringField, self).to_json() + ", \"size\" : " + str(self.field_size)

    def __eq__(self, other):
        if isinstance(other, TelemetryStreamStringField):
            return super(TelemetryStreamStringField, self).__eq__(other) and self.field_size == other.field_size
        return False


class TelemetryStreamBytesField(TelemetryStreamField):
    def __init__(self, name, size):
        super(TelemetryStreamBytesField, self).__init__(name, TYPE_BYTES, size)

    def _store(self, buffer, ptr, value):
        _length = len(value)
        buffer[ptr:ptr+self.field_size] = value
        return ptr + self.field_size

    def pack_format(self):
        return str(self.field_size) + 'p'

    def to_json(self):
        return super(TelemetryStreamBytesField, self).to_json() + ", \"size\" : " + str(self.field_size)

    def __eq__(self, other):
        if isinstance(other, TelemetryStreamBytesField):
            return super(TelemetryStreamBytesField, self).__eq__(other) and self.field_size == other.field_size
        return False


class TelemetryStreamDefinition:

    def __init__(self, name):
        self.name = name
        self.stream_id = 0  # Not defined yet
        self.buildCallback = None
        self.fields = []
        self.fixed_length = 0
        self.pack_string = None
        self.header_byte = 0
        self.header_pack = None
        self.header = None
        self.storage = None

    def add_byte(self, name, signed=False):
        self.fields.append(TelemetryStreamByteField(name, signed))
        return self

    def add_word(self, name, signed=False):
        self.fields.append(TelemetryStreamWordField(name, signed))
        return self

    def add_int(self, name, signed=True):
        self.fields.append(TelemetryStreamIntField(name, signed))
        return self

    def add_long(self, name, signed=True):
        self.fields.append(TelemetryStreamLongField(name, signed))
        return self

    def add_float(self, name):
        self.fields.append(TelemetryStreamFloatField(name))
        return self

    def add_double(self, name):
        self.fields.append(TelemetryStreamDoubleField(name))
        return self

    def add_timestamp(self, name):
        self.fields.append(TelemetryStreamDoubleField(name))
        return self

    def add_fixed_string(self, name, size):
        self.fields.append(TelemetryStreamStringField(name, size))
        return self

    def add_fixed_bytes(self, name, size):
        self.fields.append(TelemetryStreamBytesField(name, size))
        return self

    def add_var_len_string(self, name, size):
        raise NotImplemented("Not implemented yet")

    def add_var_len_bytes(self, name, size):
        raise NotImplemented("Not implemented yet")

    def get_fields(self):
        return self.fields

    def build(self, stream_id):
        self.stream_id = stream_id
        self.fixed_length = 0
        self.pack_string = ""
        for field in self.fields:
            if self.fixed_length is not None:
                field_len = field.field_size
                if field_len > 0:
                    self.fixed_length += field_len
                    self.pack_string += field.pack_format()
                else:
                    self.fixed_length = None
                    self.pack_string = None

        if self.pack_string is not None:
            self.pack_string = '<d' + self.pack_string
            self.fixed_length += 8

        if self.buildCallback is not None:
            self.buildCallback(self)

        self.header_pack = '<B'
        if self.stream_id < 256:
            self.header_byte = STREAM_ID_BYTE
            self.header_pack += 'B'
        else:
            self.header_byte = STREAM_ID_WORD
            self.header_pack += 'H'

        if self.fixed_length < 256:
            self.header_byte |= STREAM_SIZE_BYTE
            self.header_pack += 'B'
        elif self.fixed_length < 65536:
            self.header_byte |= STREAM_SIZE_WORD
            self.header_pack += 'H'
        else:
            self.header_byte |= STREAM_SIZE_LONG
            self.header_pack += 'I'

        self.header = struct.pack(self.header_pack, self.header_byte, self.stream_id, self.fixed_length)

    @staticmethod
    def extract_timestamp(record):
        return struct.unpack('<d', record[0:8])[0]

    def log(self, time_stamp, *args):
        if self.fixed_length is None:
            raise NotImplemented("Variable record size len is not yet implemented")

        if self.storage is None:
            raise NotImplemented("Stream storage is not set")

        record = struct.pack(self.pack_string, time_stamp, *args)
        self.storage.store(self, self, time_stamp, record)

    def raw_record(self, *args):
        if self.fixed_length is None:
            raise NotImplemented("Variable record size len is not yet implemented")

        if self.storage is None:
            raise NotImplemented("Stream storage is not set")

        return struct.pack(self.pack_string, *args)

    def retrieve(self, from_timestamp, to_timestmap):
        if self.storage is None:
            raise NotImplemented("Stream storage is not set")

        return self.storage.retrieve(self, from_timestamp, to_timestmap)

    def trim(self, _stream, to_timestamp):
        if self.storage is None:
            raise NotImplemented("Stream storage is not set")

        self.storage.trim(self, to_timestamp)

    def get_oldest_timestamp(self):
        if self.storage is None:
            raise NotImplemented("Stream storage is not set")

        return self.storage.get_oldest_timestamp(self)

    def to_json(self):
        return "{ \"id\" : " + str(self.stream_id) + \
               ", \"name\" : \"" + self.name + "\", \"fields\" : { " + ", ".join(["\"" + field.name + "\" : { " + field.to_json() + " }" for field in self.fields]) + " } }"


def stream_from_json(json):
    _STATE_TOP = 1
    _STATE_OBJECT = 2
    _STATE_NAME = 3
    _STATE_AFTER_NAME = 4
    _STATE_BEFORE_VALUE = 5
    _STATE_AFTER_VALUE = 6
    _STATE_INT_VALUE = 7
    _STATE_FLOAT_VALUE = 8
    _STATE_STR_VALUE = 9
    _STATE_CONST_VALUE = 10

    top = {'_key_order': []}
    stack = [top]

    def add_to_top(_name, _value):
        stack[len(stack) - 1][_name] = _value
        stack[len(stack) - 1]['_key_order'].append(_name)

    def const_to_object(v):
        return False if v == 'false' else True

    def decode_string(v):
        return bytes(v, "utf-8").decode("unicode_escape")

    i = 0
    length = len(json)
    state = _STATE_TOP
    name = ""
    value = None
    negative = 1
    while i < length:
        c = json[i]
        if state == _STATE_TOP:
            if c == '{':
                state = _STATE_OBJECT
            elif c == ' ':
                pass
            else:
                raise SyntaxError("Expected '{'; index=" + str(i))

        elif state == _STATE_OBJECT:
            if c == '}':
                del stack[len(stack) - 1]
                state = _STATE_AFTER_VALUE
            elif c == ' ':
                pass
            elif c == '"':
                state = _STATE_NAME
                name = ""
            else:
                raise SyntaxError("Expected '{' or '\"'; index=" + str(i))

        elif state == _STATE_NAME:
            if c == '"':
                state = _STATE_AFTER_NAME
            else:
                name += c

        elif state == _STATE_AFTER_NAME:
            if c == ' ':
                pass
            elif c == ':':
                state = _STATE_BEFORE_VALUE
            else:
                raise SyntaxError("Expected ':'; index=" + str(i))

        elif state == _STATE_BEFORE_VALUE:
            if c == '{':
                d = {'_key_order': []}
                add_to_top(name, d)
                stack.append(d)
                state = _STATE_OBJECT
            elif c == ' ':
                pass
            elif '0' <= c <= '9':
                negative = 1
                value = c
                state = _STATE_INT_VALUE
            elif c == '-':
                negative = -1
                value = c
                state = _STATE_INT_VALUE
            elif c == '.':
                negative = 1
                value = c
                state = _STATE_FLOAT_VALUE
            elif c == '"':
                state = _STATE_STR_VALUE
                value = ""
            elif 'A' <= c <= 'Z' or 'a' <= c <= 'z' or c == '_':
                state = _STATE_CONST_VALUE
                value = c
            else:
                raise SyntaxError("Expected '\"', number or constant; index=" + str(i))

        elif state == _STATE_INT_VALUE:
            if '0' <= c <= '9':
                value += c
            elif c == '.':
                state = _STATE_FLOAT_VALUE
                value += c
            elif c == ' ':
                add_to_top(name, int(value) * negative)
                state = _STATE_AFTER_VALUE
            elif c == ',':
                add_to_top(name, int(value) * negative)
                state = _STATE_OBJECT
            elif c == '}':
                add_to_top(name, int(value) * negative)
                del stack[len(stack) - 1]
                state = _STATE_AFTER_VALUE
            else:
                raise SyntaxError("Expected ',' or '}'; index=" + str(i))

        elif state == _STATE_FLOAT_VALUE:
            if '0' <= c <= '9':
                value += c
            elif c == ' ':
                add_to_top(name, float(value) * negative)
                state = _STATE_AFTER_VALUE
            elif c == ',':
                add_to_top(name, float(value) * negative)
                state = _STATE_OBJECT
            elif c == '}':
                add_to_top(name, float(value) * negative)
                del stack[len(stack) - 1]
                state = _STATE_AFTER_VALUE
            else:
                raise SyntaxError("Expected ',' or '}'; index=" + str(i))

        elif state == _STATE_CONST_VALUE:
            if 'A' <= c <= 'Z' or 'a' <= c <= 'z' or c == '_':
                value += c
            elif c == ' ':
                add_to_top(name, const_to_object(value))
                state = _STATE_AFTER_VALUE
            elif c == ',':
                add_to_top(name, const_to_object(value))
                state = _STATE_OBJECT
            elif c == '}':
                add_to_top(name, const_to_object(value))
                del stack[len(stack) - 1]
                state = _STATE_AFTER_VALUE
            else:
                raise SyntaxError("Expected ',' or '}'; index=" + str(i))

        elif state == _STATE_STR_VALUE:
            if c == '"':
                add_to_top(name, decode_string(value))
                state = _STATE_AFTER_VALUE
            else:
                value += c

        elif state == _STATE_AFTER_VALUE:
            if c == '}':
                del stack[len(stack) - 1]
                state = _STATE_AFTER_VALUE
            elif c == ',':
                state = _STATE_OBJECT
            elif c == ' ':
                pass
            else:
                raise SyntaxError("Expected '}' or ','; index=" + str(i))

        i += 1

    # after parsing
    # print("Got: " + str(top))
    if 'id' not in top:
        return None
    if 'name' not in top:
        raise SyntaxError("Missing 'name' value")
    if 'fields' not in top:
        raise SyntaxError("Missing 'fields' value")

    stream = TelemetryStreamDefinition(top['name'])
    stream.stream_id = int(top['id'])
    fields = top['fields']
    for fieldName in fields['_key_order']:
        field = fields[fieldName]
        if 'type' not in field:
            raise SyntaxError("Missing 'type' value for field " + str(fieldName))
        if field['type'] == TYPE_BYTE:
            stream.add_byte(fieldName, field['signed'])
        elif field['type'] == TYPE_WORD:
            stream.add_word(fieldName, field['signed'])
        elif field['type'] == TYPE_INT:
            stream.add_int(fieldName, field['signed'])
        elif field['type'] == TYPE_LONG:
            stream.add_long(fieldName, field['signed'])
        elif field['type'] == TYPE_FLOAT:
            stream.add_float(fieldName)
        elif field['type'] == TYPE_DOUBLE:
            stream.add_double(fieldName)
        elif field['type'] == TYPE_STRING:
            stream.add_fixed_string(fieldName, field['size'])
        elif field['type'] == TYPE_BYTES:
            stream.add_fixed_bytes(fieldName, field['size'])

    return stream
