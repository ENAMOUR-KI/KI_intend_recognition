
from broker import Broker
from sentiment import EmotionAnalyser


def callback(audio):
    emotion = ea.predict(signal=audio)
    print('Emotion:\t', emotion.capitalize())

    # send emotion over MQTT
    json_msg = {
      "entities": [],
      "intent": {
          "confidence": 1,
          "name": emotion
      },
      "raw_text": emotion,
      "raw_tokens": [
          emotion
      ],
      "recognize_seconds": 0.0,
      "slots": {},
      "speech_confidence": 1,
      "text": emotion,
      "tokens": [
          emotion
      ],
      "wakeword_id": None
    } 

    broker.send_message(json_msg)


if __name__ == '__main__':
    ea = EmotionAnalyser(categorial_output=True, show_confidence=False)
    broker = Broker(audio_callback=callback)
    broker.evaluation_loop(path='./data/02-M/')
    print('\nAccuracy:', broker.accuracy())