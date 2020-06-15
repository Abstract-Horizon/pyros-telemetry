# Telemetry

PyROS aimed telemetry client. This library gives definition of telemetry concepts:

- stream (logger, stream definition): TelemetryLogger, TelemetryStreamDefinition...
- client: TelemetryClient
- storage: TelemetryStorage, 

and implementaions.

## Stream

Stream represents concept of well formed data (fixed len byte record) logged by source app, service or program;
that contains data of interest. Stream can be defined using subclass of TelemetryStreamDefinition:

- MQTTLocalPipeTelemetryLogger provides all-in-one client to start logging your data to local server over local unix pipe
  (it is expected server to be already running locally). It uses MQTT to negotiate creation of stream from given definition.

- In telemetry-server package check SocketTelemetryServer class which allows you to get instance of TelemetryLogger
  to start logging to locally running TCP server.
  
Example:
```python

logger = MQTTLocalPipeTelemetryLogger('test-stream', host="172.24.1.185", port=1883)
logger.add_byte('some-status')
logger.add_double('x-coordinate')
logger.add_double('y-coordinate')
logger.init()

# ...

logger.log(1, 55, 0.0, 0.0)  # first argument is timestamp
logger.log(1.23, 0, 2.1, 0.0)
logger.log(1.90, 0, 2.2, 1.0)
```

## Client

Client provides way of accessing telemetry data. For instance:
```python

client = MQTTTelemetryClient(host=host, port=port, topic=topic)

test_stream = None
test_stream_data = None

def receive_stream_def(received_stream):
    global test_stream
    test_stream = received_stream

def receive_test_stream_data(received_records):
    global test_stream_data
    test_stream_data = received_records


client.getStreamDefinition('test-stream', process_stream_def)

while test_stream is None:
    time.sleep(0.01)

# second argument is start timestamp, third end timestamp and last callback method to deliver data
client.retrieve(test_stream, 0, time.time(), receive_test_stream_data)
```

Client functions operate with callbacks. Methods would request data but result is delivered asynchronously.

## Storage

Storage is mostly used internally by client and server implementations
