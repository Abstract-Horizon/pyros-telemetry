#!/bin/bash

PYROS_HOST_AND_PORT=$1

if [[ ( -z "PYROS_HOST_AND_PORT" ) ]]; then
    echo "Usage $0 <host[:port]>"
    exit 1
fi

pyros $PYROS_HOST_AND_PORT upload telemetry -e telemetry-library/telemetry/*
