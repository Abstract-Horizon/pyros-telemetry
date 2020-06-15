#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

LIB_DIR=$DIR/../telemetry-library/telemetry

echo "Uploading from $DIR"

echo ""
echo Uploading     telemetry
pyros $1 upload -s telemetry $DIR/telemetry_main.py -e $LIB_DIR/__init__.py $LIB_DIR/telemetry_client.py $LIB_DIR/telemetry_logger.py $LIB_DIR/telemetry_mqtt.py $LIB_DIR/telemetry_storage.py $LIB_DIR/telemetry_stream.py $LIB_DIR/telemetry_server.py $LIB_DIR/telemetry_mqtt_server.py $LIB_DIR/telemetry_server.py $LIB_DIR/telemetry_socket_server.py
echo Restarting    telemetry
pyros $1 restart   telemetry

echo ""
echo "Currently running processes:"
pyros $1 ps