# MQTT Pipeline Inspection & Operation Protocol

The MPIOP provides a set of MQTT topics which can be used to inspect (and in the future operate) pipelines.

## Getting Pipeline Topology

### List Pipelines in a Container

Send `get` as the payload to:

```
c/{container_id}/topology/get
```

You will receive the topology by subscribing to:

```
c/{container_id}/topology
```

### List Components in a Pipeline

Send `get` as the payload to:

```
c/{container_id}/c/{pipeline_id}/topology/get
```

You will receive the topology by subscribing to:

```
c/{container_id}/c/{pipeline_id}/topology
```

## Subscribing to Events

To subscribe to events flowing through a given component, send:

```json
{
  "event_count": 200
}
```

To:

```
c/{container_id}/c/{pipeline_id}/events/subscribe
```

The next 200 events to flow out of that component will be sent to:

```
c/{container_id}/c/{pipeline_id}/events
```

## Use Cases

### Debugging

Monitor events flowing through specific pipeline components to debug processing issues.

### Monitoring

Track event throughput and identify bottlenecks in real-time.

### Testing

Subscribe to events during development to validate pipeline behavior.

## Example: Python MQTT Client

```python
import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, message):
    payload = message.payload.decode()
    print(f"Topic: {message.topic}")
    print(f"Payload: {payload}")

client = mqtt.Client()
client.on_message = on_message
client.connect("mqtt-broker", 1883)

# Subscribe to topology
container_id = "my-container"
client.subscribe(f"c/{container_id}/topology")

# Request topology
client.publish(f"c/{container_id}/topology/get", "get")

client.loop_forever()
```

## Configuration

Enable MQTT visibility in your BSPump application:

```ini
[mqtt:visibility]
enabled=true
broker=localhost
port=1883
```

## Security Considerations

1. **Authentication**: Use MQTT authentication to restrict access
2. **Authorization**: Limit which topics users can subscribe to
3. **Encryption**: Use TLS for MQTT connections in production
4. **Event filtering**: Be cautious about exposing sensitive data
