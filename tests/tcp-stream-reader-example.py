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

from telemetry.telemetry_client import *



client = CachingSocketTelemetryClient("172.24.1.174")

stream_names = None
test_stream = None
some_stream = None
test_stream_data = None


def client_loop():
    while True:
        try:
            client.process_incoming_data()
        except Exception as ex:
            pass


client_thread = threading.Thread(target=client_loop, daemon=True)

time.sleep(1)

client.start()
client_thread.start()


def receive_streams(streams):
    global stream_names
    stream_names = streams


def receive_test_stream(received_stream):
    global test_stream
    test_stream = received_stream


def receive_test_stream_data(received_records):
    global test_stream_data
    test_stream_data = received_records


client.get_streams(receive_streams)


while stream_names is None:
    time.sleep(0.01)

print("Received streams " + str(stream_names))

client.get_stream_definition('balance-data', receive_test_stream)

while test_stream is None:
    time.sleep(0.01)

print("Received stream def " + str(test_stream.to_json()))

time.sleep(1)

client.retrieve(test_stream, 0, time.time(), receive_test_stream_data)

while test_stream_data is None:
    time.sleep(0.01)

print("Received data for test stream " + str(test_stream_data))

