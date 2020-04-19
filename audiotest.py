#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pyaudio
import subprocess
import tempfile
import wave
import pdb

# Find my device
MyPyAudio=pyaudio.PyAudio()
num_devices = MyPyAudio.get_device_count()
print('Found {} PyAudio devices'.format(num_devices))
for i in range(num_devices):
    print("{} {}".format(i, MyPyAudio.get_device_info_by_index(i)['name']))
device_num=int(input("Select a device number: "))
device_name=MyPyAudio.get_device_info_by_index(device_num)['name']
print("Using device {}: {}".format(device_num, device_name))

# Use flite to create a test file
cmd = ['flite']
cmd.extend(['-voice', 'slt'])
cmd.extend(['-t', 'This is a test'])
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    fname = f.name
cmd.append(fname)
print(" ".join(cmd))
with tempfile.SpooledTemporaryFile() as out_f:
    subprocess.call(cmd, stdout=out_f, stderr=out_f)
    out_f.seek(0)
    output = out_f.read().strip()
    print("Output: {}".format(output))

print("Select a method:")
print("1) Play with aplay")
print("2) Play in one chunk")
print("3) Split file into chunks and play (Naomi method)")
choice=int(input("Select choice:"))
if(choice==1):
    # Play the file with aplay
    subprocess.call(['aplay', '-D', device_name, fname])
else:
    # Open the output stream
    with open(fname, 'rb') as f:
        w = wave.open(f, 'rb')
        channels = w.getnchannels()
        bits = w.getsampwidth() * 8
        rate = w.getframerate()
        chunksize=1024
        stream_kwargs = {
            'format': pyaudio.paInt16,
            'channels': channels,
            'rate': rate,
            'output': True,
            'input': False,
            'output_device_index': device_num,
            'frames_per_buffer': chunksize
        }
        print(stream_kwargs)
        stream = MyPyAudio.open(**stream_kwargs)
        # copy from data to stream

        if(choice==2):
            with open(fname, 'rb') as f:
                # Send the whole file as one chunk
                data = w.readframes(w._nframes)
                print("data length: {}".format(len(data)))
                if len(data) > 0:
                    print("Adding {} bytes".format(chunksize*2 - (len(data)%(chunksize*2))))
                    data += b'\00' * (chunksize*2 - (len(data)%(chunksize*2)))
                print("data length: {}".format(len(data)))
                count=0
                stream.write(data)
        else:
            data = w.readframes(chunksize)
            if len(data) > 0:
                print("Adding {} bytes".format(chunksize*2 - (len(data))))
                data += b'\00' * (chunksize*2 - len(data))
            count=0
            print("data len: {}".format(len(data)))
            while data:
                count+=1
                stream.write(data)
                print("count: {}".format(count))
                data = w.readframes(chunksize)
                print("data len={}".format(len(data)))
                if len(data) > 0:
                    print("Adding {} bytes".format(chunksize*2 - (len(data))))
                    data += b'\00' * (chunksize*2 - len(data))
                print("data len={}".format(len(data)))
        stream.close()
        w.close()

os.remove(fname)
