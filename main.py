import paho.mqtt.client as mqtt

# Use mosquitto as mqtt broker
localhost = '127.0.0.1'
port = 8883
timeout = 5
topic = '$SYS/broker/version'

def on_connect(client, userdata, flags, reason_code):
    print('bajojajo')
    print('error = ' + str(reason_code))
    client.subscribe(topic)

def on_message(client, userdata, msg):
    print('msg: ' + str(msg.payload))

def on_disconnect(client, userdata, reason_code):
    print('halo?')

client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

_ = client.connect(localhost, port, timeout)
_ = client.loop_forever()
