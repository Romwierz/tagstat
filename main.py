import sys, time
import paho.mqtt.client as mqtt

# Use mosquitto as mqtt broker
host = 'broker.hivemq.com'
port = 1883
timeout = 60
topic = 'test/subtest'
mode = 'subscribe'
Qos = 0
message_payload = '{"msg": "17.2"}'

if len(sys.argv) > 1:
    if sys.argv[1] == 'publish':
        mode = 'publish'

def on_connect(client, userdata, flags, reason_code, properties):
    print('bajojajo')
    print('error = ' + str(reason_code))
    client.subscribe(topic)

def on_message(client, userdata, msg):
    print('msg: ' + str(msg.payload))

def on_disconnect(client, userdata, flags, reason_code, properties):
    print('halo?')

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

_ = client.connect(host, port, timeout)

if mode == 'subscribe':
    _ = client.loop_forever()
elif mode == 'publish':
    _ = client.publish(topic, message_payload, 0)
    time.sleep(4)
    _ = client.disconnect()
