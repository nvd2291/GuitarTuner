"""
Author: Naveed Naeem
Date: 12/31/2023
Title: Tuner.py
Description: This class is used to read in the audio from the device's 
microphone and then based on the fundamental frequency of the sample, display
the associated note on the standard music scale. Additionally it can optionally
display the FFT data and/or time data of the input samples
References:
    https://pages.mtu.edu/~suits/notefreqs.html

"""

import numpy as np
import sounddevice as sd
import sys
import queue
import time
from notes import notes
from matplotlib import pyplot as plt
from scipy import signal
from scipy.fft import fft, fftfreq
from math import floor, log10, sqrt

class Tuner:

    #notes dictionary where key = Frequency, value = Note
    __notes = notes
    __sampling_rates = (44100, 48000, 96000, 192000)
    def __init__(self, sample_rate = 96000, chunk_size = 10240):
        if sample_rate not in self.__sampling_rates:
            self.fs = self.__sampling_rates[0]
        else:
            self.fs = sample_rate
        
        devices = sd.query_devices()
        inputs = []
        for device in devices:
            if device["max_input_channels"] > 0:
                inputs.append(device)

        self.input_devices = inputs
        self.current_device = inputs[0]
        self.chunk_size = chunk_size
        self.q = queue.Queue()
        self.setup_audio_stream()
    
    def audio_callback(self, indata, frames, time, status):
        """
        This is taken from an example in the sounddevice reference doc
        """
        if status:
            print(status, file = sys.stderr)
        
        self.q.put(indata[::,0])

    def get_mic_data(self):
        while True:
            try:
                return self.q.get_nowait()
                
            except queue.Empty:
                return []

    def get_note(self):
        data = self.get_mic_data()
        if len(data) == 0:
            return
        fft_bin_size = self.fs/len(data)
        fft_data = fft(data)/len(data)
        one_sided_sample_limit = len(data)//2

        fft_data_one_sided = (fft_data[0:one_sided_sample_limit]) * 2

        #Remove DC Bin
        fft_data_one_sided = np.delete(fft_data_one_sided, 0)

        #Generate the FFT Bins
        fft_bins = np.arange(1, one_sided_sample_limit) * fft_bin_size

        #Computer the FFT Magnitude
        fft_mag = 20 * np.log10(fft_data_one_sided)

        max_value_index = np.argmax(fft_mag)

        note = round(fft_bins[max_value_index],2)
        print(f"Note Frequency is {note}")

    def setup_audio_stream(self):
        self.stream = sd.InputStream(device = self.current_device["index"],
                                     channels = self.current_device["max_input_channels"],
                                     samplerate= self.fs,
                                     blocksize = self.chunk_size,
                                     callback = self.audio_callback)
        self.stream.start()
    

    
myTuner = Tuner()

while True:
    myTuner.get_note()
    time.sleep(0.5)