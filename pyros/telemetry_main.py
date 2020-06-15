#!/usr/bin/env python3

#
# Copyright 2016-2017 Games Creators Club
#
# MIT License
#

import traceback
import pyroslib

from telemetry_stream import *
from telemetry_storage import *
from telemetry_logger import *
from telemetry_logger import *
from telemetry_server import *
from telemetry_mqtt_server import *

#
# echo service
#
# This service is just sending echo back to different topic.
#

DEBUG = False


def handleEcho(topic, payload, groups):
    print("Got echo in " + payload)
    if len(groups) > 0:
        pyroslib.publish("echo/out", groups[0] + ":" + payload)
    else:
        pyroslib.publish("echo/out", "default:" + payload)


if __name__ == "__main__":
    try:
        print("Starting telemetry service...")

        pyroslib.init("telemetry-service", unique=True)

        clusterId = pyroslib.getClusterId()
        if clusterId is not "master":
            telemetryTopic = clusterId + ":telemetry"
        else:
            telemetryTopic = "telemetry"

        print("  starting telemetry server...")
        server = MQTTLocalPipeTelemetryServer(telemetryTopic)

        print("Started telemetry service on topic " + telemetryTopic)

        pyroslib.forever(0.5)

    except Exception as ex:
        print("ERROR: " + str(ex) + "\n" + ''.join(traceback.format_tb(ex.__traceback__)))
