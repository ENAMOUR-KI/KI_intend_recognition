# python3.6

import random
import json
import numpy as np

from paho.mqtt import client as mqtt_client

# CONFIG
broker = 'localhost'
port = 12183

# MQTT TOPICS
MQTT_topicIntent = "hermes/intent/#"
MQTT_topicWW = "hermes/hotword/+/detected"

# MQTT PUBLISH
MQTT_startASR = "hermes/asr/startListening"
MQTT_stopASR = "hermes/asr/stopListening"

# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'


# username = 'user'
# password = '12345678'

# Session-Handling
isRecording = True
sessionID = 0


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global isRecording        
        global sessionID

		# Get topic from mqtt message
        topic = str(msg.topic)
        topic = topic.strip()

		# Handle mqtt message
        if "hermes/hotword/default/detected" in topic:
            startASR(client)
        elif "hermes/intent/" in topic:
            stopASR(client)
        elif "audioCaptured" in topic:
            pl = np.fromstring(msg.payload, np.int16)
            pl = pl.astype(np.float32, order='C') / 32768.0
            print(pl)
        else:
            # Should not happen...
            None

    # Subscripe to topics
    client.subscribe(MQTT_topicWW)
    client.subscribe(MQTT_topicIntent)


    client.on_message = on_message
    print("Listening to Intent")


def startASR(client):
    # Hotword -> Start ASR Session
    global isRecording    
    global sessionID
    isRecording = True
    print("Starting ASR...")
    client.publish(MQTT_startASR, json.dumps({'stopOnSilence': False, 'sessionId': str(sessionID), 'sendAudioCaptured': True}))
    client.subscribe("rhasspy/asr/default/" + str(sessionID) + "/audioCaptured")


def stopASR(client):
    # Intent -> Stop ASR Session
    global isRecording
    global sessionID
    isRecording = False
    print("Stopping ASR")
    client.publish(MQTT_stopASR)
    #client.unsubscribe("rhasspy/asr/default/" + str(sessionID) + "/audioCaptured")
    sessionID = sessionID + 1


def run():
    client = connect_mqtt()
    subscribe(client)        
    client.loop_forever()


if __name__ == '__main__':
    run()
