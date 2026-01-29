
import os
import time
import pickle
import numpy as np

from MemNet.componenets import load_model
from MemNet.matmul import ElementWiseMatMul

# todo: переделать на manager
from MemriCORE.rpi_modes import RPI_modes
import RPi.GPIO as gpio

gpio.setwarnings(False)

conn = RPI_modes()

model_path = 'PlaneDetection/[0.015907004475593567, 1.0]'
model_name = 'best_class.custom'
model = load_model(os.path.join(model_path, model_name))

# core_1 = ElementWiseMatMul(model_path)
# core_1.read_mem_weights()
# core_1.find_weights_model(model.layers[0].get_weights(), layer_id='0_Dense')

core_2 = ElementWiseMatMul(model_path, conn)
core_2.read_mem_weights()
core_2.find_weights_model(model.layers[2].get_weights(), layer_id='2_Conv2D')

# model.layers[0].matmul = core_1.process_layer
model.layers[2].matmul = core_2.process_layer

dataset_filename = 'PlaneDetection/[0.015907004475593567, 1.0]/train_test_data.pickle'
with open(dataset_filename, 'rb') as handle:
    train_test_data = pickle.load(handle)

test_images = train_test_data['test_images']
test_labels = train_test_data['test_labels']

start_time = time.time()
output_data_new = model.predict(test_images[0][np.newaxis, ...])
print('Время обработки', time.time() - start_time)
print(np.round(output_data_new, 2))
