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
import threading

from telemetry.telemetry_server import TelemetryServer
from telemetry.telemetry_logger import TelemetryLogger


class SocketTelemetryServer(TelemetryServer):
    def __init__(self, host="0.0.0.0", port=1860, deffered_buffer_len=1000):
        super(SocketTelemetryServer, self).__init__()
        self.debug = True
        self.host = host
        self.port = port
        self._server_socket = None
        self._client_sockets = {}
        self._deferred = None
        self._deferred_length = deffered_buffer_len
        self._deferred_thread = None
        self._deferred_event = None
        self._deferred_exception_callback = None
        self._accept_clients_thread = None
        self._accept_clients_exception_callback = None

    def start(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.settimeout(0.5)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(0)

    def setup_accept_clients_thread(self, exception_callback=None):
        self._accept_clients_exception_callback = exception_callback
        self._accept_clients_thread = threading.Thread(target=self._accept_clients, daemon=True)
        self._accept_clients_thread.start()

    def setup_deferred(self, exception_callback=None):
        self._deferred = []
        self._deferred_event = threading.Event()
        self._deferred_exception_callback = exception_callback
        self._deferred_thread = threading.Thread(target=self._process_deferred, daemon=True)
        self._deferred_thread.start()

    def get_socket(self):
        return self._server_socket

    def process_incoming_connections(self):
        try:
            client_socket, address = self._server_socket.accept()
        except socket.timeout:
            return
        if self.debug:
            print(f"Got client from address {address}, sending stream definitions back...")

        # noinspection PyBroadException
        try:
            packet = "STRS".encode('utf-8') + struct.pack("I", len(self.streams))
            client_socket.sendall(packet)
            for stream_name in self.streams:
                stream = self.streams[stream_name]

                stream_def_string = stream.to_json().encode('utf-8')

                packet = "STDF".encode('utf-8') + struct.pack("I", len(stream_def_string)) + stream_def_string
                client_socket.sendall(packet)

            self._client_sockets[address] = client_socket
            if self.debug:
                print(f"Finished sending definition to client from address {address}.")
        except Exception:
            self._close_client(address)

    def _close_client(self, address):
        client_socket = self._client_sockets[address]
        # noinspection PyBroadException
        try:
            client_socket.close()
        except Exception:
            pass
        del self._client_sockets[address]

    def create_logger(self, stream_name):
        return TelemetryLogger(stream_name, destination=self, telemetry_client=self)

    # This is to satisfy 'TelemetryClient' interface
    def register_stream_with_server(self, stream, callback):
        self.streams[stream.name] = stream
        self.next_stream_id += 1
        stream.stream_id = self.next_stream_id
        self.stream_ids[stream.stream_id] = stream
        callback(stream.stream_id)

    # This is to satisfy 'TelemetryLoggerDestination' interface
    def log(self, stream, time_stamp, *args):
        record = struct.pack(stream.pack_string, time_stamp, *args)

        buf = stream.header + record

        if self._deferred is not None:
            self._deferred.append(buf)
            if len(buf) > self._deferred_length:
                del self._deferred[0]
            if len(self._client_sockets) > 0:
                self._deferred_event.set()
        else:
            known_addresses = [address for address in self._client_sockets]

            for address in known_addresses:
                client_socket = self._client_sockets[address]
                # noinspection PyBroadException
                try:
                    client_socket.send(buf)
                except Exception as ex:
                    self._close_client(address)

    def _accept_clients(self):
        while True:
            try:
                self.process_incoming_connections()
            except Exception as ex:
                if self._accept_clients_exception_callback is not None:
                    self._accept_clients_exception_callback(ex)

    def _process_deferred(self):
        records = []
        while True:
            try:
                if len(self._client_sockets) > 0 and len(self._deferred) > 0:
                    records.extend(self._deferred)
                    del self._deferred[:]

                    for address in [address for address in self._client_sockets]:
                        client_socket = self._client_sockets[address]
                        # noinspection PyBroadException
                        try:
                            for buf in records:
                                client_socket.send(buf)
                        except Exception as ex:
                            self._close_client(address)
                            if self.debug:
                                print(f"Closing client's socket at address {address}")
                    if len(records) > 10:
                        print(f"Processed {len(records)} deferred records.")
                    del records[:]
                else:
                    self._deferred_event.clear()
                    self._deferred_event.wait(1)

            except Exception as ex:
                if self._deferred_exception_callback is not None:
                    self._deferred_exception_callback(ex)