###############################################################################
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


from telemetry.telemetry_mqtt import MQTTWrapper
from telemetry.telemetry_server import PubSubLocalPipeTelemetryServer


class MQTTLocalPipeTelemetryServer(PubSubLocalPipeTelemetryServer):
    def __init__(self, host="localhost", port=1883, topic="telemetry"):
        self.mqtt = MQTTWrapper(host, port, topic)

        super(MQTTLocalPipeTelemetryServer, self).__init__(topic, self.mqtt.publish, self.mqtt.subscribe)

    def wait_and_process(self, wait_time=0.02):  # 50 times a second by default
        self.mqtt.loop(wait_time)

    def run_forever(self, wait_time=0.02, outer=None):  # 50 times a second by default
        self.mqtt.forever(wait_time, outer)
