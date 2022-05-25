# Set Rhasspy MQTT to External

import os
import json
import time
import wave
import paho.mqtt.client as mqtt             # pip install paho-mqtt


class Broker:
    ALL_SITE_ID                = 'all'
    ON_HOTWORD_DETECTED        = 'hermes/hotword/+/detected'
    ON_TTS_SAY                 = 'hermes/tts/say'
    ON_TTS_SAY_FINISHED       = 'hermes/tts/sayFinished'
    ON_ASR_TEXT_CAPTURED       = 'hermes/asr/textCaptured'
    ON_ASR_START_LISTENING     = 'hermes/asr/startListening'
    ON_ASR_ERROR               = 'hermes/error/asr'
    ON_HOTWORD_TOGGLE_ON       = 'hermes/hotword/toggleOn'
    ON_INTENT_DETECTED         = 'hermes/intent/#'
    ON_INTENT_NOT_RECOGNIZED   = 'hermes/nlu/intentNotRecognized'
    ON_INTENT_RECOGNIZED       = 'hermes/nlu/intentParsed'
    ON_AUDIO_PLAY_FINISHED      = 'hermes/audioServer/{}/playFinished'
    ON_VOLUME_SET            = 'hermes/volume/set'


    def __init__(self, user, password, host='localhost', port=1883, site_id='default') -> None:
        self.connected = False
        self.user = user
        self.host = host
        self.port = port
        self.site_id = site_id
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

        self.test_log = {}


    def on_connect(self, client, userdata, flags, rc):
        """
        client.subscribe('hermes/intent/#')
        client.subscribe('hermes/nlu/intentNotRecognized')
        client.subscribe('hermes/error/asr')
        client.subscribe('hermes/asr/textCaptured')
        """

        time.sleep(0.1)
        self.client.subscribe([
			(self.ON_HOTWORD_DETECTED, 0),
            (self.ON_INTENT_DETECTED, 0),
			(self.ON_TTS_SAY, 0),
			(self.ON_ASR_TEXT_CAPTURED, 0),
			(self.ON_ASR_START_LISTENING, 0),
            (self.ON_ASR_ERROR, 0),
			(self.ON_AUDIO_PLAY_FINISHED, 0),
			(self.ON_TTS_SAY_FINISHED, 0),
			(self.ON_INTENT_NOT_RECOGNIZED, 0),
			(self.ON_INTENT_RECOGNIZED, 0),
			(self.ON_VOLUME_SET, 0),
		])
        
        if rc == 0:
                print('Connected succeeded')
                self.connected = True
        else:
            print('Connection failed')
        

    def on_disconnect(self, client, userdata, flags, rc):
        '''Called when disconnected from MQTT broker.'''
        client.reconnect()


    def on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        '''Called each time a message is received on a subscribed topic.'''

        payload = {}
        if hasattr(msg, 'payload') and msg.payload: 
            payload = json.loads(msg.payload.decode('UTF-8'))

        siteId = payload.get('siteId')
        isForMe = siteId == self.site_id

        if not isForMe:
            print('Message received but was not for me')
            return False

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


    def __loop_start(self):
        self.client.loop_start()
        
        while self.connected != True:
            print('Waiting for connection...')
            time.sleep(0.1)


    def evaluation_loop(self, path='./data/', chunksize=1000000):
        self.__loop_start()
        time.sleep(0.1)

        for i, file in enumerate(os.listdir(path)):
            session_id = f'session{i}'

            if file.endswith('.mp3') or file.endswith('.wav') or file.endswith('.ogg'):
                self.target_intent = file.split('-')[1]

                self.current_file = os.path.join(path, file)
                with open(self.current_file, 'rb') as f:
                    print("\nTesting:\t", self.current_file)
                    wavbytes = f.read()

                    self.client.publish('hermes/asr/startListening', json.dumps({'siteId': self.site_id, 'sessionId': session_id, 'stopOnSilence': False, 'sendAudioCaptured': True}))
                    time.sleep(0.1)

                    self.client.publish(f'hermes/audioServer/{self.site_id}/audioFrame', wavbytes)
                    time.sleep(0.1)

                    self.client.publish('hermes/asr/stopListening', json.dumps({'siteId': self.site_id, 'sessionId': session_id}))
                    
                    while not self.intent_received:
                        time.sleep(0.05)
                    self.intent_received = False


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

mqtt_user = input('Please enter your MQTT username: ')
mqtt_pw = input('Please enter your MQTT password: ')
brkr = Broker(mqtt_user, mqtt_pw)
# brkr.message_loop()
brkr.evaluation_loop(path='./data/02-M/')
print('\nAccuracy:', brkr.accuracy())
