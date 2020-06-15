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


import time
import threading

from telemetry.telemetry_socket_server import *
from telemetry.telemetry_client import *


server = SocketTelemetryServer()
server.start()

server_socket = server.get_socket()
server_socket.settimeout(10)

logger1 = server.create_logger("some-stream")
logger1.add_word('value_1')
logger1.add_word('value_2')
logger1.init()

logger2 = server.create_logger("test-stream")
logger2.add_byte('byte')
logger2.add_double('double')
logger2.init()


client = CachingSocketTelemetryClient("127.0.0.1")

stream_names = None
test_stream = None
some_stream = None
test_stream_data = None


def server_loop():
    while True:
        try:
            server.process_incoming_connections()
        except Exception as ex:
            pass


def client_loop():
    while True:
        try:
            client.process_incoming_data()
        except Exception as ex:
            pass


server_thread = threading.Thread(target=server_loop, daemon=True)
client_thread = threading.Thread(target=client_loop, daemon=True)
server_thread.start()

time.sleep(1)

client.start()
client_thread.start()


def receive_streams(streams):
    global stream_names
    stream_names = streams


def receive_some_stream(received_stream):
    global some_stream
    some_stream = received_stream


def receive_test_stream(received_stream):
    global test_stream
    test_stream = received_stream


def receive_test_stream_data(received_records):
    global test_stream_data
    test_stream_data = received_records


logger2.log(1, 10, 2.0)
logger1.log(1, 12, 13)
logger2.log(2, 20, 2.1)
logger1.log(2.5, 14, 15)
logger2.log(3, 30, 2.2)


client.get_streams(receive_streams)


while stream_names is None:
    time.sleep(0.01)

print("Received streams " + str(stream_names))

client.get_stream_definition('test-stream', receive_test_stream)
client.get_stream_definition('some-stream', receive_some_stream)

while test_stream is None:
    time.sleep(0.01)

print("Received stream def " + str(test_stream.to_json()))

assert str(test_stream.to_json()) == """{ "id" : 2, "name" : "test-stream", "fields" : { "byte" : { "type" : "b", "signed" : false }, "double" : { "type" : "d" } } }"""

time.sleep(1)

client.retrieve(test_stream, 0, time.time(), receive_test_stream_data)

while test_stream_data is None:
    time.sleep(0.01)

print("Received data for test stream " + str(test_stream_data))

assert test_stream_data == [(1.0, 10, 2.0), (2.0, 20, 2.1), (3.0, 30, 2.2)]

client.retrieve(some_stream, 0, time.time(), receive_test_stream_data)

while test_stream_data is None:
    time.sleep(0.01)

print("Received data for some stream " + str(test_stream_data))

assert test_stream_data == [(1.0, 12, 13), (2.5, 14, 15)]
