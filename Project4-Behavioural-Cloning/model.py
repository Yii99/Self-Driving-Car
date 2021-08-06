import csv
import os
import cv2
import numpy as np
from keras.models import Sequential
from keras.models import Model
import matplotlib.pyplot as plt
from keras.layers import Flatten, Lambda, Cropping2D, Convolution2D, Dense, Dropout
import sklearn
import math



def read_csv(path):
    '''
    :param path: path stores the csv file
    :return: lines of the csv
    '''
    lines = []
    with open(path) as csvfile:
        reader = csv.reader(csvfile)
        for line in reader:
            lines.append(line)
    return lines


def read_images(csv_lines, image_path, correction=0.4):
    '''
    :param csv_lines: lines in csv file
    :param image_path: path of images
    :param correction: correction to create adjusted steering measurements
    :return: images and steering angles
    '''
    images = []
    measurements = []
    for line in csv_lines:
        for i in range(3):
            source_path = line[i]
            filename = source_path.split('/')[-1]
            current_path = os.path.join(image_path, filename)
            image = cv2.imread(current_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            images.append(image)
        measurement = line[3]  # center
        measurements.append(measurement)
        measurements.append(float(measurement) + correction)  # left image
        measurements.append(float(measurement) - correction)  # right image
    return images, measurements


def Model(input_shape):
    '''
    :param input_shape: shape of original image
    :return: model
    '''
    model = Sequential()
    model.add(Cropping2D(cropping=((50, 20), (0, 0)), input_shape=input_shape))  #
    model.add(Lambda(lambda x: x / 255.0 - 0.5))
    model.add(Convolution2D(24, 5, 5, border_mode="same", subsample=(2, 2), activation="relu"))
    model.add(Convolution2D(36, 5, 5, border_mode="same", subsample=(2, 2), activation="relu"))
    model.add(Convolution2D(48, 5, 5, border_mode="valid", subsample=(2, 2), activation="relu"))
    model.add(Convolution2D(64, 3, 3, border_mode="valid", activation='relu'))
    model.add(Convolution2D(64, 3, 3, border_mode="valid", activation='relu'))
    model.add(Flatten())
    model.add(Dense(100))
    model.add(Dropout(0.3))
    model.add(Dense(50))
    model.add(Dropout(0.3))
    model.add(Dense(10))
    model.add(Dropout(0.3))
    model.add(Dense(1))
    return model


def split_data(dataset, ratio=0.2):
    '''
    :param dataset: dataset
    :param val_ratio: split ratio of validation dataset
    :param test_ratio: split ratio of test dataset
    :return: training, validation and test dataset
    '''
    DATASET_SIZE = len(dataset)
    val_size = int(ratio * DATASET_SIZE)
    train_size = DATASET_SIZE - val_size

    training_files = dataset[:train_size]
    validation_files = dataset[train_size:train_size + val_size]
    return training_files, validation_files


def augmentation(x, y):
    '''
    :param x: images
    :param y: measurements
    :return: augmented data
    '''
    x_augmented = []
    y_augmented = []
    for image, measurement in zip(x, y):
        x_augmented.append(image)
        y_augmented.append(measurement)
        x_augmented.append(cv2.flip(image, 1))
        y_augmented.append(-1.0 * float(measurement))
    return x_augmented, y_augmented


def generator(dataset, image_path, augment=True, batch_size=32):
    '''
    :param dataset: dataset
    :param image_path: path of images
    :param augmentation: if True, apply data augmentation
    :return:
    '''
    x, y = read_images(dataset, image_path)
    if augment:
        x, y = augmentation(x, y)
    num_dataset = len(x)
    print(num_dataset)
    while 1:
        for offset in range(0, num_dataset, batch_size):
            batch_x = x[offset:offset+batch_size]
            batch_y = y[offset:offset+batch_size]
            x_train, y_train = np.array(batch_x), np.array(batch_y)
            yield sklearn.utils.shuffle(x_train, y_train)


lines = read_csv("../2016/driving_log.csv")
training_files, validation_files = split_data(lines, ratio=0.2)
train_generator = generator(training_files, "../2016/IMG", augment=True, batch_size=32)
validation_generator = generator(validation_files, "../2016/IMG", augment=True, batch_size=32)

batch_size = 32
input_shape = (160, 320, 3)
model = Model(input_shape)
model.compile(loss='mse', optimizer='adam')

history_object = model.fit_generator(train_generator,
                    steps_per_epoch=math.ceil(len(training_files) / batch_size),
                    validation_data=validation_generator,
                    validation_steps=math.ceil(len(validation_files) / batch_size),
                    epochs=10, verbose=1)
model.save('model.h5')

# print the keys contained in the history object
print(history_object.history.keys())

# plot the training and validation loss for each epoch
plt.plot(history_object.history['loss'])
plt.plot(history_object.history['val_loss'])
plt.title('model mean squared error loss')
plt.ylabel('mean squared error loss')
plt.xlabel('epoch')
plt.legend(['training set', 'validation set'], loc='upper right')
plt.savefig('loss.jpg')







