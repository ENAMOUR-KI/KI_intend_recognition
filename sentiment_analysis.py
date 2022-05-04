import flair
from typing import List, DefaultDict
import os
from collections import defaultdict


def get_sentences_from_txt(filepath: str) -> List[str]:
    """extract sentences from a "sentences.ini" file to get the test sentences

    :param filepath: filepath where the dataset is saved
    :return: List that contains the extracted sentences from the dataset file (removed intents, white spacey, empty lines
    """
    result = []
    with open(filepath, 'r') as file:
        for line in file:
            if "[" not in line:
                temp = line.rstrip()
                if not temp == '':
                    result.append(temp)
    return result


def predict_sentiments(data: List[str], model) -> DefaultDict:
    """predict the sentiments for the data with a pretrained flair model

    :param data: Data for that the sentiments should be predicted
    :param model: Flair Text Classifier model that is used for sentiment analysis
    :return: Dictionary with the sentences as key and the predicted sentiment as value
    """
    res_dict = defaultdict(list)

    for sentence in data:
        s = flair.data.Sentence(sentence)
        model.predict(s)
        pred_value = s.labels[0].to_dict()['value']
        confidences = s.labels[0].to_dict()['confidence']
        result = [pred_value, confidences]
        res_dict[sentence] = result

    return res_dict


def write_dict_to_json(sentiments: DefaultDict, save_path: str):
    """writes a dictionary into a json file

    :param sentiments: dictionary that contains the sentences with its sentiments and confidence
    :param save_path: path from the json file
    :return:
    """
    with open(save_path, "w") as file:
        for key, value in sentiments.items():
            file.write(f"{key} \n sentiment: {value[0]} \t confidence. {value[1]}\n\n\n")


if __name__ == "__main__":
    """
    Configurations
    """

    root_path = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(root_path, "dataset/sentences.ini")
    save_path = os.path.join(root_path, 'dataset/sentiments.json')

    # define pretrained flair model
    flair_sentiment = flair.models.TextClassifier.load('en-sentiment')

    """
    Data generation and prediction
    """

    data = get_sentences_from_txt(dataset_path)

    sentiments = predict_sentiments(data, flair_sentiment)

    write_dict_to_json(sentiments, save_path)

    x = 5
