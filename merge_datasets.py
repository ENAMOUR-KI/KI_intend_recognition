import os
import random
from typing import List
from sentiment_analysis import get_sentences_from_txt


def get_neutral_sentences(pos_path: str, neg_path: str, sent_path: str, new_path: str):
    """get the neutral sentences from sentences.ini -> all sentences in sentences.ini without the positive and
    negative sentences

    :param pos_path: path of the dataset with positive sentences
    :param neg_path: path of the dataset with negative sentences
    :param sent_path: path of the dataset with all sentences (neg, pos, neutral)
    :param new_path: path where the new dataset should be saved
    """
    pos = get_sentences_from_txt(pos_path)
    neg = get_sentences_from_txt(neg_path)
    all_sent = get_sentences_from_txt(sent_path)

    pos.extend(neg)

    for elem in pos:
        for i, elem_2 in enumerate(all_sent):
            new = elem_2
            if "(" in elem_2:
                index = elem_2.index("(")
                new = elem_2[:index].strip()
                all_sent[i] = new
            if elem == new:
                all_sent.remove(elem_2)

    neutral_sentences = random.sample(all_sent, 180)

    with open(new_path, 'w') as file:
        for element in neutral_sentences:
            file.write('%s\n' % element)


def create_labelled_data(pos_path: str, neg_path: str, neutral_path: str, new_path: str, labels: List[str]):
    """

    :param neutral_path:
    :param labels:
    :param pos_path:
    :param neg_path:
    :param new_path:
    :return:
    """

    pos = get_sentences_from_txt(pos_path)
    neg = get_sentences_from_txt(neg_path)
    neutral = get_sentences_from_txt(neutral_path)

    neg_label = labels[0]
    neutral_label = labels[1]
    pos_label = labels[2]

    with open(new_path, 'w') as file:
        for elem in neg:
            file.write(f'{neg_label}, {elem}\n')
        for elem in neutral:
            file.write(f'{neutral_label}, {elem}\n')
        for elem in pos:
            file.write(f'{pos_label}, {elem}\n')


if __name__ == "__main__":
    root_path = os.path.dirname(__file__)

    positive_path = os.path.join(root_path, "dataset/positive.ini")
    negative_path = os.path.join(root_path, "dataset/negative.ini")

    sentences_path = os.path.join(root_path, "dataset/sentences.ini")

    merged_path_name = os.path.join(root_path, "dataset/neutral.txt")
    get_neutral_sentences(positive_path, negative_path, sentences_path, merged_path_name)

    final_dataset_path = os.path.join(root_path, "dataset/labelled_data.txt")
    label = ["0", "1", "2"]
    create_labelled_data(positive_path, negative_path, merged_path_name, final_dataset_path, label)
