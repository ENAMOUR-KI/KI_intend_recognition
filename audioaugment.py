#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date : 06/22/2022
# @Project: ENAMOUR
# @AUTHOR : Marcel Rinder

import os
import argparse
import random
import numpy as np
from scipy.io import wavfile
from scipy import signal
from pathlib import Path
import librosa
from tqdm import tqdm


def augment(input_folder, output_folder, num_samples=1000):
    # Check if input folder exists
    assert os.path.exists(input_folder), "Input folder not found"

    # Create output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop through all .wav files in input folder
    files = list(Path(input_folder).glob(*.wav'))
    num_files = len(files)
    augments_per_file = num_samples // num_files

    print(f'--- Input Folder: {input_folder} ---')
    print(f'Number of audiofiles   = {num_files}')
    print(f'Augmentations per file = {augments_per_file}')
    print()

    seed = 0
    for filepath in files:
        print(f'--- Augmenting {filepath} ---')
        samplerate, data = wavfile.read(filepath)
        data = data.astype(np.int16)
        original_data = data.astype(np.float32, order='C') / 32768.0

        output_filepath = os.path.join(output_folder, os.path.basename(filepath))

        # Write original audio to output folder
        wavfile.write(output_filepath.replace('.wav', f'-orig.wav'), samplerate, data)

        # Generate and apply random effects
        for i in tqdm(range(augments_per_file)):
            audio_data = original_data.copy()

            np.random.seed(seed)
            choices = np.zeros(3)
            while not np.sum(choices) > 0:
                choices = np.random.randint(0, 2, 3)

            # Random pitch
            if choices[0] == 1:
                audio_data = librosa.effects.pitch_shift(audio_data, sr=samplerate, n_steps=np.random.random() * 5)

            # Muffle effect
            if choices[1] == 1:
                b, a = signal.butter(3, np.random.random() * 0.1)
                audio_data = signal.lfilter(b, a, audio_data)

            # Change playback speed
            if choices[2] == 1:
                audio_data = librosa.resample(audio_data, orig_sr=samplerate, target_sr=samplerate + np.random.randint(-20000, 20000))

            
            # Write audio with applied effect to output folder
            write_data = np.array(audio_data * (12767)).astype(np.int16)
            wavfile.write(output_filepath.replace('.wav', f'-aug{i}.wav'), samplerate, write_data)
            seed += 1
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Augment audio dataset')
    parser.add_argument('-i', '--input-folder', type=str,
                        help='Input folder containing the audio samples')
    parser.add_argument('-o', '--output-folder', type=str,
                        help='Output folder where the augmented audio samples will be saved to')
    parser.add_argument('-n', '--num-samples', type=int,
                        help='Number of samples that will be generated')

    args = parser.parse_args()

    augment(args.input_folder, args.output_folder, num_samples=args.num_samples)


