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


import socket
import struct
import time
import uuid

from telemetry.telemetry_stream import stream_from_json
from telemetry.telemetry_storage import MemoryTelemetryStorage


class _StreamCallback:
    def __init__(self, stream_name, topic, unique_id, sub_method):
        self.stream_name = stream_name
        self.stream = None
        self.topic = topic
        self.unique_id = unique_id
        self.sub_method = sub_method
        self.retrieve_callbacks = []
        self.oldest_callbacks = []
        self.defs_callbacks = []

        self.retrieveTopic = topic + "/retrieve_" + unique_id + "_" + stream_name
        self.oldestTimestampTopic = topic + "/oldest_" + unique_id + "_" + stream_name
        self.streamDefTopic = topic + "/streamdef_" + unique_id + "_" + stream_name

        self.sub_method(self.retrieveTopic, self._handle_retrieve)
        self.sub_method(self.oldestTimestampTopic, self._handle_oldest)
        self.sub_method(self.streamDefTopic, self._handle_stream_def)

    def stop(self):
        pass

    def _handle_retrieve(self, _topic, payload):
        record_length = self.stream.fixed_length

        received_records = len(payload) // record_length
        if received_records * record_length != len(payload):
            pass  # what to do here?

        records = []
        for i in range(0, received_records):
            record = struct.unpack(self.stream.pack_string, payload[i * record_length: (i + 1) * record_length])
            records.append(record)

        callbacks = self.retrieve_callbacks
        self.retrieve_callbacks = []

        while len(callbacks) > 0:
            callbacks[0](records)
            del callbacks[0]

    def _handle_oldest(self, _topic, payload):
        oldest, size = struct.unpack('<di', payload)
        while len(self.oldest_callbacks) > 0:
            self.oldest_callbacks[0](oldest, size)
            del self.oldest_callbacks[0]

    def _handle_stream_def(self, _topic, payload):
        payload = str(payload, 'UTF-8')
        self.stream = stream_from_json(payload)
        if self.stream is not None:
            self.stream.build(self.stream.stream_id)
        while len(self.defs_callbacks) > 0:
            self.defs_callbacks[0](self.stream)
            del self.defs_callbacks[0]


class TelemetryClient:
    def __init__(self):
        pass

    def get_streams(self, callback):
        pass

    def get_stream_definition(self, stream_name, callback):
        pass

    def get_oldest_timestamp(self, stream, callback):
        pass

    def trim(self, stream, to_timestamp):
        pass

    def retrieve(self, stream, from_timestamp, to_timestmap, callback):
        pass

    def stop(self) -> None:
        pass

class PubSubTelemetryClient(TelemetryClient):
    def __init__(self, topic=None, pub_method=None, sub_method=None):
        super(PubSubTelemetryClient, self).__init__()

        self.topic = topic
        self.pub_method = pub_method
        self.sub_method = sub_method
        self.uniqueId = str(uuid.uuid4())
        self.stream_callbacks = {}
        self.streams_callbacks = []
        self.streams_topic = self.topic + "/streams_" + self.uniqueId

        self.sub_method(self.streams_topic, self._handle_streams)

    def _handle_streams(self, _topic, payload):
        payload = str(payload, 'UTF-8')
        stream_names = payload.split("\n")
        while len(self.streams_callbacks) > 0:
            self.streams_callbacks[0](stream_names)
            del self.streams_callbacks[0]

    def _add_stream_callback(self, stream_name):
        if stream_name not in self.stream_callbacks:
            stream_callback = _StreamCallback(stream_name, self.topic, self.uniqueId, self.sub_method)
            self.stream_callbacks[stream_name] = stream_callback
        else:
            stream_callback = self.stream_callbacks[stream_name]

        return stream_callback

    def stop(self):
        for stream_callback in self.stream_callbacks:
            stream_callback.stop()

    def get_streams(self, callback):
        self.streams_callbacks.append(callback)
        self.pub_method(self.topic + "/streams", self.streams_topic)

    def get_stream_definition(self, stream_name, callback):
        stream_callback = self._add_stream_callback(stream_name)
        if stream_callback.stream is not None:
            callback(stream_callback.stream)
        else:
            stream_callback.defs_callbacks.append(callback)
            self.pub_method(self.topic + "/streamdef/" + stream_name, stream_callback.streamDefTopic)

    def get_oldest_timestamp(self, stream, callback):
        if self.pub_method is None:
            raise NotImplemented("Publish method not defined")

        stream_callback = self._add_stream_callback(stream.name)
        stream_callback.oldest_callbacks.append(callback)
        self.pub_method(self.topic + "/oldest/" + stream.name, stream_callback.oldestTimestampTopic)

    def trim(self, stream, to_timestamp):
        self.pub_method(self.topic + "/trim/" + stream.name, str(to_timestamp))

    def retrieve(self, stream, from_timestamp, to_timestmap, callback):
        if self.pub_method is None:
            raise NotImplemented("Publish method not defined")

        stream_callback = self._add_stream_callback(stream.name)
        stream_callback.retrieve_callbacks.append(callback)
        self.pub_method(self.topic + "/retrieve/" + stream.name, ",".join(str(f) for f in [stream_callback.retrieveTopic, from_timestamp, to_timestmap]))


class CachingSocketTelemetryClient(TelemetryClient):
    def __init__(self, host, port=1860):
        super(CachingSocketTelemetryClient, self).__init__()
        self.debug = True
        self.host = host
        self.port = port
        self.socket = None
        self.streams = {}
        self.stream_ids = {}
        self.next_stream_id = 0
        self.storage = MemoryTelemetryStorage()

    def start(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(0.1)
        client_socket.connect((self.host, self.port))

        # Read stream definition
        try:
            buf = client_socket.recv(8)
            if len(buf) < 8:
                hex_str = " ".join(["{:02x}".format(b) for b in buf])
                raise ValueError(f"Received wrong number of bytes for stream header; '{len(buf)}'; {hex_str}")
            if "STRS" != buf[:4].decode('utf-8'):
                hex_str = " ".join(["{:02x}".format(b) for b in buf])
                raise ValueError(f"Received wrong stream numbers header; '{buf[:3].decode('utf-8')}'; {hex_str}")
            stream_number = struct.unpack("I", buf[4:])[0]
            if self.debug:
                print(f"Received number of streams ({stream_number}). Reading definitions...")
            for i in range(stream_number):
                buf = client_socket.recv(8)
                if len(buf) < 8:
                    hex_str = " ".join(["{:02x}".format(b) for b in buf])
                    raise ValueError(f"Received wrong number of bytes for stream definition header; '{len(buf)}'; {hex_str}")
                if "STDF" != buf[:4].decode('utf-8'):
                    hex_str = " ".join(["{:02x}".format(b) for b in buf])
                    raise ValueError(f"Received wrong stream definition {i} header; '{buf[:3].decode('utf-8')}'; {hex_str}")

                definition_len = struct.unpack("I", buf[4:])[0]
                if self.debug:
                    print(f"  stream {i} definition is {definition_len} bytes long...")
                definition_buffer = bytes()
                while len(definition_buffer) < definition_len:
                    load_len = min(definition_len - len(definition_buffer), 1024)
                    buf = client_socket.recv(load_len)
                    if buf == b'':
                        raise RuntimeError("Socket connection broken while receiving definition buffer")
                    definition_buffer += buf

                stream_definition = definition_buffer.decode('utf-8')
                stream = stream_from_json(stream_definition)
                if stream is not None:
                    stream.build(stream.stream_id)

                self.stream_ids[stream.stream_id] = stream
                self.streams[stream.name] = stream

            if self.debug:
                print("Successfully read stream definitions.")

            self.socket = client_socket
        except SyntaxError as syntax_ex:
            raise syntax_ex
        except ConnectionError as cex:
            raise cex
        except Exception as ex:
            self._close_socket()
            raise ex

    def stop(self):
        if self.socket is not None:
            self._close_socket()

    def _close_socket(self):
        # noinspection PyBroadException
        try:
            self.socket.shutdown()
            self.socket.close()
        except Exception:
            pass
        self.socket = None

    def process_incoming_data(self):
        if self.socket is None:
            # raise ConnectionError("Socket is closed. Please call 'start()' method.")
            return

        try:
            buf = self.socket.recv(1)
        except socket.timeout:
            return
        if buf == b'':
            raise RuntimeError("Socket connection broken while receiving stream data")

        b = buf[0]
        header_pack_def = ("B" if b & 1 == 0 else "W") + ("B" if b & 6 == 0 else ("H" if b & 6 == 2 else "I"))
        header_size = (1 if b & 1 == 0 else 2) + (1 if b & 6 == 0 else (2 if b & 6 == 2 else 4))

        if self.socket is not None:
            buf = self.socket.recv(header_size)
            if buf == b'':
                raise RuntimeError(f"Socket connection broken while receiving stream header data; {header_size} bytes")

            if len(buf) != header_size:
                raise RuntimeError(f"Socket connection broken while receiving stream header data; {header_size} bytes, bug got {len(buf)}")

            header = struct.unpack(header_pack_def, buf)
            stream_id = header[0]
            stream_record_size = header[1]

            record_bytes = bytes()
            while self.socket is not None and len(record_bytes) < stream_record_size:
                buf = self.socket.recv(min(stream_record_size - len(record_bytes), 1024))
                if buf == b'':
                    raise RuntimeError(f"Socket connection broken while receiving stream data; {stream_record_size} bytes")
                record_bytes += buf

            if stream_id not in self.stream_ids:
                pass  # Ignoring stream id we don't know anything about
            else:
                stream = self.stream_ids[stream_id]

                record = struct.unpack(stream.pack_string, record_bytes)

                self.storage.store(stream, stream.extract_timestamp(record_bytes), record)

    def get_streams(self, callback):
        if self.socket is None:
            raise ConnectionError("Socket is closed. Please call 'start()' method.")

        callback([stream_name for stream_name in self.streams])

    def get_stream_definition(self, stream_name, callback):
        if self.socket is None:
            raise ConnectionError("Socket is closed. Please call 'start()' method.")

        if stream_name not in self.streams:
            raise KeyError(f"Stream {stream_name} is not reported by server at connection.")

        callback(self.streams[stream_name])

    def get_oldest_timestamp(self, stream, callback):
        if self.socket is None:
            raise ConnectionError("Socket is closed. Please call 'start()' method.")

        if stream.stream_id not in self.stream_ids:
            raise KeyError(f"Stream {stream.name} is not reported by server at connection.")

        self.storage.get_oldest_timestamp(stream, callback)

    def trim(self, stream, to_timestamp):
        if self.socket is None:
            raise ConnectionError("Socket is closed. Please call 'start()' method.")

        if stream.stream_id not in self.stream_ids:
            raise KeyError(f"Stream {stream.name} is not reported by server at connection.")

        self.storage.trim(stream, to_timestamp)

    def retrieve(self, stream, from_timestamp, to_timestmap, callback):
        def _drop_timestamp(records):
            callback([r[1] for r in records])

        # if self.socket is None:
        #     raise ConnectionError("Socket is closed. Please call 'start()' method.")

        if stream.stream_id not in self.stream_ids:
            raise KeyError(f"Stream {stream.name} is not reported by server at connection.")

        self.storage.retrieve(stream, from_timestamp, to_timestmap, _drop_timestamp)
