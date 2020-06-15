#!/usr/bin/env python3

#
# Copyright 2019 Games Creators Club
#
# MIT License
#

import os
import sys
import time

from telemetry.telemetry_mqtt import MQTTTelemetryClient
from telemetry.telemetry_client import CachingSocketTelemetryClient

args = sys.argv


def print_help():
    print("usage: download-steram-mqtt [(-f|--file) <filename>] [(-c|--CSV)|(-b|--binary)] [-d|--delete] [(-t|--topic) <topic>] <host[:port]> <stream-name>")
    print(" ")
    print("    -h                    help message")
    print("    -f|--file             filename. If supplied output will go to that file, otherwise to stdout.")
    print("    -c|--CSV              result output will be CSV. This is default.")
    print("    -b|--binary           result output will be binary.")
    print("    -d|--delete           remove data after downloading.")
    print("    -t|--topic <topic>    topic to be used for retrieving telemetry. Default is 'telemetry'.")
    print("    -m|--mqtt             use MQTT to talk to server. Default.")
    print("    -s|--tcp              use TCP (stream) to talk to server.")
    print("     <host[:port]>        MQTT broker host and port. Default port is 1883.")
    print("    <stream-name>         name of stream.")


RESULT_TYPE_CSV = 1
RESULT_TYPE_BINARY = 2

filename = None
file = None
result_type = RESULT_TYPE_CSV
delete = False
host = None
port = 1883
stream_name = None
timeout = 60
stream = None
timestamp = None
step = 10  # 15 seconds a time
time_to_leave = False
topic = "telemetry"
mqtt = True

i = 1

while i < len(args):
    arg = args[i]
    if arg == '-h':
        print_help()
        sys.exit(0)
    elif arg == "-f" or arg == "--file":
        if i == len(args) - 1:
            print("Missing file argument")
            print("")
            print_help()
            sys.exit(1)
        else:
            i += 1
            filename = args[i]
            if filename.endswith(".csv"):
                result_type = RESULT_TYPE_CSV
    elif arg == '-c' or arg == '--CSV':
        result_type = RESULT_TYPE_CSV
    elif arg == '-b' or arg == '--binary':
        result_type = RESULT_TYPE_BINARY
    elif arg == '-d' or arg == '--delete':
        delete = True
    elif arg == '-n' or arg == '--mqtt':
        mqtt = True
    elif arg == '-s' or arg == '--tcp' or arg == '--stream':
        mqtt = False
        delete = True
    elif arg == '-t' or arg == '--topic':
        if i + 1 >= len(args):
            print("Missing <topic> argument")
            print("")
            print_help()
            sys.exit(1)
        else:
            i += 1
            topic = args[i]
    elif host is None:
        hostport = arg.split(':')
        if len(hostport) > 1:
            host = hostport[0]
            port = int(hostport[1])
        else:
            host = hostport[0]
    elif stream_name is None:
        stream_name = arg
    else:
        print("Unknown argument " + str(arg))
        print("")
        print_help()
        sys.exit(-1)

    i += 1

if host is None:
    print("Missing host")
    print("")
    print_help()
    sys.exit(-1)

if stream_name is None:
    print("Missing stream name")
    print("")
    print_help()
    sys.exit(-1)


def process_stream_def(stream_def):
    global stream
    if stream_def is None:
        print("No such stream")
        sys.exit(-1)
    else:
        stream = stream_def
        client.get_oldest_timestamp(stream, process_oldest_timestamp)


def process_oldest_timestamp(oldest_timestamp, records_count):
    global timestamp, file
    timestamp = oldest_timestamp
    print("   The oldest timestamp is " + str(oldest_timestamp) + " (it is " + str(time.time() - oldest_timestamp) + "s ago) and there are " + str(records_count) + " records.")

    if result_type == RESULT_TYPE_CSV:
        if filename is not None:
            file = open(os.path.expanduser(filename), "wt")
            file.write("timestamp," + ",".join(f.name for f in stream.fields) + "\n")
        else:
            print("timestamp," + ",".join(f.name for f in stream.fields))
    else:
        if filename is not None:
            file = open(os.path.expanduser(filename), "wt")
        else:
            print(",".join(f.name for f in stream.fields))

    if  not mqtt or records_count > 0:
        client.retrieve(stream, timestamp, timestamp + step, process_data)


def process_data(records):
    global timestamp, time_to_leave

    reached_end = False

    try:
        timestamp += step

        for record in records:
            if result_type == RESULT_TYPE_CSV:
                if file is not None:
                    file.write(",".join([str(f) for f in record]) + "\n")
                else:
                    print(",".join([str(f) for f in record]))
            else:
                if file is not None:
                    file.write(stream.rawRecord(*record))
                else:
                    print(" ".join(["0x%02x" % b for b in stream.rawRecord(*record)]))

        if timestamp > time.time() or len(records) == 0:
            time_to_leave = mqtt
            if time_to_leave:
                if file is not None:
                    file.close()
                if delete:
                    # print("*** trimming to " + str(time.time()))
                    client.trim(stream, time.time())
                return

        if delete:
            # print("*** trimming to " + str(timestamp))
            client.trim(stream, timestamp)

        if mqtt:
            client.retrieve(stream, timestamp, timestamp + step, process_data)
    except KeyboardInterrupt:
        time_to_leave = True


def progress_client():
    if mqtt:
        client.mqtt.loop(0.01)
    else:
        client.process_incoming_data()
        t = time.time()
        client.retrieve(stream, 0, t, process_data)
        client.trim(stream, t)


if mqtt:
    print("    Using topic " + topic)
    client = MQTTTelemetryClient(host=host, port=port, topic=topic)
else:
    client = CachingSocketTelemetryClient(host=host, port=port)
    client.start()
    client.socket.settimeout(2)

client.get_stream_definition(stream_name, process_stream_def)

if mqtt:
    now = time.time()
    while stream is None and time.time() - now < timeout:
        client.mqtt.loop(0.01)

if stream is None:
    print("Failed to receive stream " + str(stream_name) + " definition in " + str(timeout) + " seconds")
    sys.exit(-1)

if mqtt:
    now = time.time()
    while timestamp is None and time.time() - now < timeout:
        client.mqtt.loop(0.01)

if stream is None:
    print("Failed to receive oldest timestamp for  " + str(stream_name) + " in " + str(timeout) + " seconds")
    sys.exit(-1)

while True:
    try:
        current_timestamp = timestamp
        now = time.time()
        while not time_to_leave and current_timestamp == timestamp and time.time() - now < timeout:
            progress_client()

        if time_to_leave:
            if mqtt:
                client.mqtt.loop(0.01)

            sys.exit()
        elif current_timestamp == timestamp:
            print("Failed to receive data for  " + str(stream_name) + " in " + str(timeout) + " seconds")
            sys.exit(-1)
    except KeyboardInterrupt:
        print("Finishing stream...")
        if file is not None:
            file.close()
        time_to_leave = True
