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


from telemetry.telemetry_server import *
from telemetry.telemetry_logger import *
from telemetry.telemetry_client import *


subs = {}


def sub(topic, callback):
    if topic not in subs:
        subs[topic] = []

    subs[topic].append(callback)


def pub(topic, payload):
    if type(payload) is str:
        payload = payload.encode('utf-8')
    if topic in subs:
        for callback in subs[topic]:
            callback(topic, payload)
    else:
        for _sub in subs:
            if _sub.endswith('#') and topic.startswith(_sub[0:len(_sub)-1]):
                for callback in subs[_sub]:
                    callback(topic, payload)
                return


server = PubSubLocalPipeTelemetryServer("topic", pub, sub)

logger = TelemetryLogger('test-stream')
logger.telemetry_client = PubSubTelemetryLoggerClient("topic", pub, sub)
logger.add_byte('byte')
logger.add_double('double')
logger.init()

client = PubSubTelemetryClient("topic", pub, sub)

logger.log(1, 10, 2.0)
logger.log(2, 20, 2.1)
logger.log(3, 30, 2.2)


stream_names = None
test_stream = None
test_stream_data = None


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

client.get_stream_definition('test-stream', receive_test_stream)

while test_stream is None:
    time.sleep(0.01)

print("Received stream def " + str(test_stream.to_json()))

assert str(test_stream.to_json()) == """{ "id" : 2, "name" : "test-stream", "fields" : { "byte" : { "type" : "b", "signed" : false }, "double" : { "type" : "d" } } }"""

time.sleep(1)

client.retrieve(test_stream, 0, time.time(), receive_test_stream_data)

while test_stream_data is None:
    time.sleep(0.01)

print("Received data " + str(test_stream_data))

assert test_stream_data == [(1.0, 10, 2.0), (2.0, 20, 2.1), (3.0, 30, 2.2)]
