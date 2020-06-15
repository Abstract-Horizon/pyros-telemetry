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


import threading
import time

from telemetry.telemetry_mqtt_server import MQTTLocalPipeTelemetryServer
from telemetry.telemetry_mqtt import MQTTLocalPipeTelemetryLogger, MQTTTelemetryClient


##############################################################################################
# Example how server is set up

print("Creating server...")
server = MQTTLocalPipeTelemetryServer(host="172.24.1.185", port=1883)
print("Server created.")

print("Starting server...")
# if in its own process then no need for thread - just call server.runForever()
thread = threading.Thread(target=server.run_forever)
thread.daemon = True
thread.start()
print("Server started")


##############################################################################################
# Example how logger is set up

print("Creating logger...")
logger = MQTTLocalPipeTelemetryLogger('test-stream', host="172.24.1.185", port=1883)
logger.add_byte('byte')
logger.add_double('double')
logger.init()
print("Logger created.")

logger.log(1, 10, 2.0)
logger.log(2, 20, 2.1)
logger.log(3, 30, 2.2)


##############################################################################################
# Example how to use client

print("Creating client...")
client = MQTTTelemetryClient(host="172.24.1.185", port=1883)
print("Client created.")

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
    # client needs to loop through mqtt so it can fetch new messages and process them
    client.mqtt.loop(0.02)

print("Received streams " + str(stream_names))

client.get_stream_definition('test-stream', receive_test_stream)

while test_stream is None:
    # client needs to loop through mqtt so it can fetch new messages and process them
    client.mqtt.loop(0.02)

print("Received stream def " + str(test_stream.toJSON()))

time.sleep(1)

client.trim(test_stream, 1.9)

client.retrieve(test_stream, 0, time.time(), receive_test_stream_data)

while test_stream_data is None:
    # client needs to loop through mqtt so it can fetch new messages and process them
    client.mqtt.loop(0.02)

print("Received data " + str(test_stream_data))
