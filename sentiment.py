"""
Source: wav2vec 2.0 for speech emotion recognition
"""

import os
import json
import audb
import audeer
import audonnx
import audformat
import audinterface
import pandas as pd
import pickle
import paho.mqtt.client as mqtt             # pip install paho-mqtt

from broker import Broker


class EmotionAnalyser:
    def __init__(self, categorial_output=True, show_confidence=True, model_root='model', cache_root='cache', sampling_rate=16000, num_workers=1):
        self.model_root = model_root
        self.cache_root = cache_root
        self.sampling_rate = sampling_rate
        self.categorial_output = categorial_output
        self.num_workers = num_workers
        self.show_confidence = show_confidence

        self.model = self.__load_model()
        self.interface = self.__load_interface()
        self.classifier = self.__load_classifier() if self.categorial_output else None

        self.logits = ('arousal', 'dominance', 'valence')
        self.emotions = ('anger', 'boredom', 'disgust', 'fear', 'happiness', 'neutral', 'sadness')


    def __cache_path(self, file):
        return os.path.join(self.cache_root, file)

    def __load_model(self):
        audeer.mkdir(self.cache_root)

        url = 'https://zenodo.org/record/6221127/files/w2v2-L-robust-12.6bc4a7fd-1.1.0.zip'
        dst_path = self.__cache_path('model.zip')

        if not os.path.exists(dst_path):
            audeer.download_url(
                url, 
                dst_path, 
                verbose=True,
            )
            
        if not os.path.exists(self.model_root):
            audeer.extract_archive(
                dst_path, 
                self.model_root, 
                verbose=True,
            )

        return audonnx.load(self.model_root)

    def __load_interface(self):
        if self.categorial_output:
            return audinterface.Feature(
                self.model.outputs['hidden_states'].labels,
                process_func=self.model,
                process_func_args={
                    'output_names': 'hidden_states',
                },
                sampling_rate=16000,    
                resample=True,
                num_workers=self.num_workers,
                verbose=True,
            )

        else:
            return audinterface.Feature(
                self.model.outputs['logits'].labels,
                process_func=self.model,
                process_func_args={
                    'output_names': 'logits',
                },
                sampling_rate=self.sampling_rate,
                resample=True,    
                num_workers=self.num_workers,
                verbose=True,
            )

    def __load_classifier(self):
        path = self.__cache_path('emotion_categorial_model.pkl')
        if os.path.exists(path):
            with open(path, 'rb') as f:
                clf = pickle.load(f)
                self.emotions = tuple(clf.classes_)
                return clf
        else:
            raise RuntimeError('No categorial model found! File cache/emotion_categorial_model.pkl required')

    def predict(self, signal=None, file=None):
        if signal is None:
            features = self.interface.process_file(file)
        else:
            features = self.interface.process_signal(signal, sampling_rate=16000)
        if self.categorial_output:
            if self.show_confidence:
                proba = dict(zip(self.emotions, self.classifier.predict_proba(features)[0]))
                pred = max(proba, key=proba.get)
                return {"emotion": pred, "confidence": proba[pred]}
            else:
                return self.classifier.predict(features)[0]
        else:
            return dict(zip(self.logits, features.values.tolist()[0]))


if __name__ == '__main__':
    import glob

    files = glob.glob("data/02-M/*.wav")
    ea = EmotionAnalyser(categorial_output=True, show_confidence=True)

    broker = Broker()

    for file in files:
        emotion = ea.predict(file=file)
        print('Emotion:', emotion)

        # send emotion over MQTT
        json_msg = {
        "entities": [],
        "intent": {
            "confidence": 0,
            "name": ""
        },
        "emotion": {
            "name": emotion.get('emotion', 'neutral'),
            "confidence": emotion.get('confidence', 0)
        },
        "raw_text": "",
        "raw_tokens": [
            ""
        ],
        "recognize_seconds": 0,
        "slots": {},
        "speech_confidence": 1,
        "text": "",
        "tokens": [
            ""
        ],
        "wakeword_id": None
        }
        broker.send_message(json_msg)
