import os
import cv2
import json
import torch
import csv
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
import time
from PIL import Image
import matplotlib.pyplot as plt
import glob
import sys
from scipy import signal
import random
import soundfile as sf
import librosa
import pdb
import matplotlib.pyplot as plt
import copy


def time_shift_spectrogram(spectrogram):
    nb_cols = spectrogram.shape[1]
    nb_shifts = np.random.randint(0, nb_cols)

    return np.roll(spectrogram, nb_shifts, axis=1)


class AVDataset(Dataset):

    def __init__(self, args, mode='train', transforms=None):
        classes = []
        data = []
        data2class = {}

        with open(args.csv_path + 'stat.csv') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                classes.append(row[0])

        with open(args.csv_path + args.test) as f:

            csv_reader = csv.reader(f)
            for item in csv_reader:

                if item[2] in classes and os.path.exists(
                        args.audio_path + '/' + item[0] + '_' + item[1] + '.wav') and os.path.exists(
                        args.visual_path + '/' + item[0] + '_' + item[1]):

                    data.append(item[0] + '_' + item[1])
                    data2class[item[0] + '_' + item[1]] = item[2]

        # print(args.csv_path + args.test)
        print('data load over')
        print(len(data))
        self.audio_path = args.audio_path
        self.visual_path = args.visual_path
        self.mode = 'train' if len(data)>50000 else 'test'
        self.transforms = transforms
        self.classes = sorted(classes)

        print(self.classes)
        self.data2class = data2class


        self._init_atransform()

        self.av_files = []
        for item in data:
            self.av_files.append(item)
        print('# of files = %d ' % len(self.av_files))
        print('# of classes = %d' % len(self.classes))


    def _init_atransform(self):
        self.aid_transform = transforms.Compose([transforms.ToTensor()])

    def __len__(self):
        return len(self.av_files)

    def __getitem__(self, idx):
        av_file = self.av_files[idx]

        # Audio
        '''
        samples, samplerate = sf.read(self.audio_path + '/'+ av_file + '.wav')
        resamples = np.tile(samples, 10)[:160000]
        resamples[resamples > 1.] = 1.
        resamples[resamples < -1.] = -1.
        frequencies, times, spectrogram = signal.spectrogram(resamples, samplerate, nperseg=512, noverlap=353)
        spectrogram = np.log(spectrogram + 1e-7)
        #spectrogram = time_shift_spectrogram(spectrogram)
        mean = np.mean(spectrogram)
        std = np.std(spectrogram)
        spectrogram = np.divide(spectrogram - mean, std + 1e-9)
        np.save('/home/xiaokang_peng/vggtry/vggall/' + self.mode + '/audio_np/' + av_file + '.npy', spectrogram)
        '''



        spectrogram = np.load('/home/xiaokang_peng/vggtry/vggall/' + self.mode + '/audio_np/' + av_file + '.npy')



        #Visual
        path = self.visual_path + '/' + av_file
        file_num = len([lists for lists in os.listdir(path)])

        transf = transforms.Compose([
            transforms.Resize(size=(300, 300)),
            transforms.RandomCrop(224),
            # transforms.RandomHorizontalFlip(p=0.3),
            transforms.ToTensor()
        ])

        pick_num = 3
        seg = int(file_num/pick_num)
        path1 = []
        image = []
        image_arr = []
        t = [0]*pick_num

        for i in range(pick_num):
            t[i] = random.randint(i*seg+1,i*seg+seg) if file_num > 6 else 1
            path1.append('frame_0000'+ str(t[i]) + '.jpg')
            image.append(Image.open(path + "/" + path1[i]).convert('RGB'))
            image_arr.append(transf(image[i]))
            image_arr[i] = image_arr[i].unsqueeze(1).float()
            if i==0:
                image_n = copy.copy(image_arr[i])
            else:
                image_n = torch.cat((image_n, image_arr[i]), 1)

        return spectrogram, image_n, self.classes.index(self.data2class[av_file]), av_file