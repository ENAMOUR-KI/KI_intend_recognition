# Set Rhasspy MQTT to External

import os
import json
import time
import wave
import paho.mqtt.client as mqtt             # pip install paho-mqtt
import numpy as np


class Broker:
    ALL_SITE_ID                = 'all'
    ON_HOTWORD_DETECTED        = 'hermes/hotword/+/detected'
    ON_INTENT_DETECTED         = 'hermes/intent/#'
    ON_TTS_SAY                 = 'hermes/tts/say'
    ON_TTS_SAY_FINISHED        = 'hermes/tts/sayFinished'
    ON_ASR_TEXT_CAPTURED       = 'hermes/asr/textCaptured'
    ON_ASR_START_LISTENING     = 'hermes/asr/startListening'
    ON_ASR_STOP_LISTENING      = 'hermes/asr/stopListening'
    ON_ASR_ERROR               = 'hermes/error/asr'
    ON_ASR_AUDIO_CAPTURED      = 'rhasspy/asr/{siteId}/{sessionId}/audioCaptured'
    ON_HOTWORD_TOGGLE_ON       = 'hermes/hotword/toggleOn'
    ON_INTENT_NOT_RECOGNIZED   = 'hermes/nlu/intentNotRecognized'
    ON_INTENT_RECOGNIZED       = 'hermes/nlu/intentParsed'
    ON_AUDIO_PLAY              = 'hermes/audioServer/{siteId}/playBytes/{requestId}'
    ON_AUDIO_PLAY_FINISHED     = 'hermes/audioServer/{siteId}/playFinished'
    ON_VOLUME_SET              = 'hermes/volume/set'


    def __init__(self, host='localhost', port=1883, site_id='default', audio_callback=None, user='', password='') -> None:
        self.connected = False
        self.user = user
        self.host = host
        self.port = port
        self.site_id = site_id
        self.request_id = 'request-1'
        self.session_id = 'session-1'
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        self.client.username_pw_set(user, password=password)
        self.client.connect(host, port)

        self.current_file = ""
        self.current_sentence = ""
        self.current_intent = ""
        self.target_intent = ""
        self.intent_received = False
        self.is_recording = False

        self.test_log = {}
        self.audio_callback = audio_callback


    def on_connect(self, client, userdata, flags, rc):
        time.sleep(0.1)
        self.client.subscribe([
			(self.ON_HOTWORD_DETECTED, 0),
            (self.ON_INTENT_DETECTED, 0),
			(self.ON_TTS_SAY, 0),
			(self.ON_ASR_TEXT_CAPTURED, 0),
			(self.ON_ASR_START_LISTENING, 0),
            (self.ON_ASR_AUDIO_CAPTURED.format(siteId=self.site_id, sessionId=self.session_id), 0),
            (self.ON_ASR_ERROR, 0),
			(self.ON_AUDIO_PLAY_FINISHED.format(siteId=self.site_id), 0),
			(self.ON_TTS_SAY_FINISHED, 0),
			(self.ON_INTENT_NOT_RECOGNIZED, 0),
			(self.ON_INTENT_RECOGNIZED, 0),
			# (self.ON_VOLUME_SET, 0),
		])
        
        if rc == 0:
            print('Connection succeeded')
            self.connected = True
        else:
            print('Connection failed')
        

    def on_disconnect(self, client, userdata, flags, rc):
        '''Called when disconnected from MQTT broker.'''
        client.reconnect()


    def on_message(self, client, userdata, msg: mqtt.MQTTMessage, show_not_for_me=False):
        '''Called each time a message is received on a subscribed topic.'''
        payload = {}
        topic = str(msg.topic).strip()

        if hasattr(msg, 'payload') and msg.payload:
            try:
                siteId = payload.get('siteId')
                is_for_me = siteId == self.site_id

                if not is_for_me:
                    if show_not_for_me:
                        print('Message received but was not for me')
                    return False

                payload = json.loads(msg.payload.decode('UTF-8'))

            except UnicodeDecodeError:
                # Payload contains audio data
                pass
                # payload = np.fromstring(msg.payload, np.int16)
                # payload = payload.astype(np.float32, order='C') / 32768.0
                # if callable(self.audio_callback):
                #     self.audio_callback(payload)
                

        if msg.topic == self.ON_INTENT_RECOGNIZED:
            self.current_intent = payload['intent']['intentName']
            self.intent_received = True

            if self.target_intent is not None:
                print('Target: \t', self.target_intent)
            print('Predicted:\t', self.current_intent)

            if self.target_intent is not None:
                self.test_log[self.current_file] = (self.current_sentence, self.current_intent, self.target_intent)
                
        elif msg.topic == self.ON_INTENT_NOT_RECOGNIZED:
            print('Error: intent not recognized')
            self.intent_received = True

        elif msg.topic == self.ON_ASR_TEXT_CAPTURED:
            self.current_sentence = payload['text']
            print('Recognized:\t', self.current_sentence)

            self.client.publish('hermes/nlu/query', json.dumps({'input': self.current_sentence, 'siteId': self.site_id}))

        elif "hermes/hotword/default/detected" in topic:
            self.start_asr()

        elif "hermes/intent/" in topic:
            self.stop_asr()

        elif "audioCaptured" in topic:
            pl = np.fromstring(msg.payload, np.int16)
            pl = pl.astype(np.float32, order='C') / 32768.0
            if callable(self.audio_callback):
                self.audio_callback(pl)


    def __loop_start(self):
        self.client.loop_start()
        
        while not self.connected:
            print('Waiting for connection...')
            time.sleep(0.1)

    def evaluation_loop(self, path='./data/', chunksize=1000000):
        self.__loop_start()
        
        time.sleep(0.1)
        for i, file in enumerate(os.listdir(path)):
            # self.session_id = f'session{i}'

            if file.endswith('.mp3') or file.endswith('.wav') or file.endswith('.ogg'):
                self.target_intent = file.split('-')[1]

                self.current_file = os.path.join(path, file)
                with open(self.current_file, 'rb') as f:
                    print("\nTesting:\t", self.current_file)
                    wavbytes = f.read()

                    self.client.publish(self.ON_ASR_START_LISTENING, json.dumps({'siteId': self.site_id, 'sessionId': self.session_id, 'stopOnSilence': False, 'sendAudioCaptured': True}))
                    time.sleep(0.1)

                    self.client.publish(f'hermes/audioServer/{self.site_id}/audioFrame', wavbytes)
                    time.sleep(0.1)

                    self.client.publish(self.ON_ASR_STOP_LISTENING, json.dumps({'siteId': self.site_id, 'sessionId': self.session_id}))
                    
                    for i in range(500):
                        if self.intent_received:
                            break
                        time.sleep(0.05)
                    if not self.intent_received:
                        print('No intent - time out!')
                    self.intent_received = False

    def loop(self):
        self.client.loop_forever()

    def message_loop(self):
        self.__loop_start()
        try:
            while True:
                message = input('Send message: ')
                self.client.publish('hermes/nlu/query', json.dumps({'input': message, 'siteId': self.site_id}))
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.client.disconnect()
            self.client.loop_stop()

    def accuracy(self):
        total = len(self.test_log)
        correct = 0
        incorrect = 0
        for key, value in self.test_log.items():
            sentence, prediction, target = value
            if prediction.lower() == target.lower():
                correct += 1
            else:
                incorrect += 1
        return correct / total

    def send_message(self, message):
        self.client.publish('hermes/nlu/query', json.dumps({'input': message, 'siteId': self.site_id}))

    def start_asr(self):
        # Hotword -> Start ASR Session
        self.is_recording = True
        print("Starting ASR...")
        self.client.publish(self.ON_ASR_START_LISTENING, json.dumps({'stopOnSilence': False, 'sessionId': self.session_id, 'sendAudioCaptured': True}))
        self.client.subscribe(f"rhasspy/asr/default/{self.session_id}/audioCaptured")

    def stop_asr(self):
        # Intent -> Stop ASR Session
        self.is_recording = False
        print("Stopping ASR...")
        self.client.publish(self.ON_ASR_STOP_LISTENING)
        # client.unsubscribe("rhasspy/asr/default/" + str(sessionID) + "/audioCaptured")
        self.session_id += 1


if __name__ == '__main__':
    brkr = Broker()
    # brkr.message_loop()
    brkr.evaluation_loop(path='./data/02-M/')
    print('\nAccuracy:', brkr.accuracy())
