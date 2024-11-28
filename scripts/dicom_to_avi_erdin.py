# David Ouyang 10/2/2019. Adapted by Erdin Tokmak 11/2024.
# Python code to iterate through a folder, including subfolders,
# and convert DICOM to AVI of a defined size (natively 224 x 224).

import re
import os
from os.path import splitext
import numpy as np
import shutil
from tqdm import tqdm
import time
import subprocess
import datetime
from datetime import date
import sys
import cv2
import matplotlib.pyplot as plt
from shutil import copy
import math
import pydicom as dicom
from pydicom.uid import UID, generate_uid
import rich

AllA4cNames = "/Users/erdin/coding/Kardiologie/tte_label_project/python/DICOM_to_AVI/breunig"
destinationFolder = "/Users/erdin/coding/Kardiologie/tte_label_project/python/DICOM_to_AVI/converted"

os.system('cls' if os.name == 'nt' else 'clear')

dataset = dicom.dcmread("/Users/erdin/coding/Kardiologie/tte_label_project/python/DICOM_to_AVI/breunig/patient_1/study_1/KXBHR4J5.dcm")
print(dataset)


# Clear the "converted" folder
if os.path.exists(destinationFolder):
    for file_name in os.listdir(destinationFolder):
        file_path = os.path.join(destinationFolder, file_name)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
else:
    os.makedirs(destinationFolder)
    print(f"Created folder: {destinationFolder}")

# Mask function
def mask(output):
    dimension = output.shape[0]
    m1, m2 = np.meshgrid(np.arange(dimension), np.arange(dimension))

    # Mask pixels outside of scanning sector
    mask = ((m1 + m2) > int(dimension / 2) + int(dimension / 10))
    mask *= ((m1 - m2) < int(dimension / 2) + int(dimension / 10))
    mask = np.reshape(mask, (dimension, dimension)).astype(np.int8)

    maskedImage = cv2.bitwise_and(output, output, mask=mask)
    print(maskedImage.shape)
    return maskedImage

# Function to create AVI videos
def makeVideo(fileToProcess, destinationFolder):
    try:
        # print(f"Processing file: {fileToProcess}")

        fileName = os.path.basename(fileToProcess)
        if os.path.exists(os.path.join(destinationFolder, fileName + '.avi')):
            print(f"{fileName} has already been processed.")
            return

        # Read the DICOM file
        dataset = dicom.dcmread(fileToProcess, force=True)

        # Ensure pixel data exists
        if 'PixelData' not in dataset:
            print(f"No pixel data found in {fileName}")
            return

        # Extract the pixel array
        testarray = dataset.pixel_array
        print(f"Pixel array shape: {testarray.shape}")

        if len(testarray.shape) != 4:
            print(f"{fileName} has {testarray.shape} shape, skipping.")
            return

        # No cropping logic is applied here, retain original shape
        print("Skipping cropping. Processing full images.")

        # Get dimensions and frame count
        frames, height, width, channels = testarray.shape

        # Extract frame rate
        fps = 30
        try:
            fps = dataset[(0x18, 0x40)].value
            print(f"Frame rate extracted: {fps}")
        except KeyError:
            print("Couldn't find frame rate, defaulting to 30 FPS.")

        # Set up video writer with original dimensions
        new_resolution = (width * 2, height * 2)  # Double resolution
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        video_filename = os.path.join(destinationFolder, fileName + '.avi')
        # print(f"Video file path: {video_filename}")
        out = cv2.VideoWriter(video_filename, fourcc, fps, new_resolution)

        # Process each frame with a loading bar
        with tqdm(total=frames, desc=f"Processing {fileName}", unit="frame") as pbar:
            for i in range(frames):
                outputA = testarray[i, :, :, 0]

                # Resize to double resolution
                output = cv2.resize(outputA, new_resolution, interpolation=cv2.INTER_CUBIC)

                # Optional mask function can be applied here
                # finaloutput = mask(output)

                finaloutput = cv2.merge([output, output, output])
                out.write(finaloutput)

                # Update the loading bar
                pbar.update(1)

        out.release()
        print(f"{fileName} ✅")
        
    except Exception as e:
        print(f"An error occurred while processing {fileToProcess}: {e}")
        if 'testarray' in locals():
            print(f"Array shape before error: {testarray.shape}")
        if 'mean' in locals():
            print(f"Mean values: {mean}")

    return 0

# Main script
count = 0
# cropSize = (224, 224)
subfolders = os.listdir(AllA4cNames)

for folder in subfolders:
    # print(folder)

    for content in os.listdir(os.path.join(AllA4cNames, folder)):
        for subcontent in os.listdir(os.path.join(AllA4cNames, folder, content)):
            count += 1

            VideoPath = os.path.join(AllA4cNames, folder, content, subcontent)
            # print(f"\n{count}\n{folder}\n{content} {subcontent}")
            print(f"\n{count}\n{content} {subcontent}")

            if not os.path.exists(os.path.join(destinationFolder, subcontent + ".avi")):
                makeVideo(VideoPath, destinationFolder)
            else:
                print("Already did this file", VideoPath)

print(f"\nTotal files processed: {count}")
