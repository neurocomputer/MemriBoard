import os
import csv
import time
import datetime
import pickle
import numpy as np
from sklearn.metrics import classification_report

from MemriCORE.rpi_modes import RPI_modes
import RPi.GPIO as gpio

model_path = 'models/model_pid_8'

# создаем папку для сохранения результата
now = datetime.datetime.now()
formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
result_dir = os.path.join(model_path, f'experiment_{formatted_date}')
os.mkdir(result_dir)

num_layers = 2

def softmax(vec):
    exponential = np.exp(vec)
    probabilities = exponential / np.sum(exponential)
    return probabilities

with open(os.path.join(model_path, 'new_weights.pkl'), 'rb') as fp:
    weights = pickle.load(fp)

with open(os.path.join(model_path, 'new_test_data.pkl'), 'rb') as fp:
    test_data = pickle.load(fp)

with open(os.path.join(model_path, 'all_mem_weights_coordinates.pkl'), 'rb') as fp:
    all_mem_weights_coordinates_data = pickle.load(fp)
    mem_weights_coordinates = all_mem_weights_coordinates_data[0]
    mem_weights_scales = all_mem_weights_coordinates_data[1]

X_test = test_data[0]
y_test = test_data[1]

#activations = [lambda x: x if x>0 else 0,
#               lambda x: x]

activations = [lambda x: np.tanh(x),
               lambda x: x]

gpio.setwarnings(False)
conn = RPI_modes()

def a2v(adc_value:int):
    _vol_ref_adc = 5
    _adc_bit = 14
    _gain = 11.11
    vol_value = round(((adc_value * _vol_ref_adc)/((2 ** _adc_bit) - 1)) / _gain, 5)
    return vol_value

outputs = []
outputs_mem = []

all_times = []

# создаем файл для сохранения результата общего
now = datetime.datetime.now()
formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
fname_io_result = os.path.join(result_dir, f'IO_{formatted_date}.csv')
with open(fname_io_result,'w', newline='', encoding='utf-8') as file:
    file_wr = csv.writer(file, delimiter=",")
    file_wr.writerow(['inputs0', 'inputs1', 'outputs', 'outputs_mem'])

for inputs in X_test:
    

    # создаем файл для сохранения результата умножения
    now = datetime.datetime.now()
    formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
    fname_mac_result = os.path.join(result_dir, f'mac_{formatted_date}.csv')
    with open(fname_mac_result,'w', newline='', encoding='utf-8') as file:
        file_wr = csv.writer(file, delimiter=",")
        file_wr.writerow(['lay', 'neur', 'syn', 'wl', 'bl', 'dac', 'adc', 'res', 'truth'])

    start_time = time.time()
    counter_params = 0
    inputs_mem = inputs
    # print(inputs.shape)
    result_log = []
    result_log.append(inputs[0])
    result_log.append(inputs[1])
    scale_x = np.max(np.abs(inputs))
    for i in range(num_layers):
        #print(inputs_mem)
        inputs_mem = list(map(lambda x: round(abs(x)/scale_x*0.3*4096/5), inputs_mem))
        layer_weights = weights[counter_params]
        HARD_WEIGHTS = mem_weights_coordinates[counter_params]
        SCALE_W = mem_weights_scales[counter_params]
        counter_params += 1
        layer_biases = weights[counter_params]
        HARD_BIASES = mem_weights_coordinates[counter_params]
        SCALE_B = mem_weights_scales[counter_params]
        counter_params += 1
        neurons_model = []
        neurons_mem = []
        for neuron in range(layer_weights.shape[1]):
            mac_model = 0
            mac_mem = 0
            for synapse in range(layer_weights.shape[0]):
                mul_model = layer_weights[synapse][neuron] * inputs[synapse]
                mac_model += mul_model
                # мэмристоры
                wl = HARD_WEIGHTS[neuron][synapse]['wl']
                bl = HARD_WEIGHTS[neuron][synapse]['bl']
                res = conn.mode_9(inputs_mem[synapse], 0, wl, bl)[0]
                mul = a2v(res)
                sign_w = np.sign(layer_weights[synapse][neuron])
                sign_i = np.sign(inputs[synapse])
                mul_res = mul * sign_i * sign_w / SCALE_W / 0.3 * scale_x
                mac_mem += mul_res
                # пишем результат mac
                with open(fname_mac_result,'a', newline='', encoding='utf-8') as file:
                    file_wr = csv.writer(file, delimiter=",")
                    file_wr.writerow([i, neuron, synapse, wl, bl, inputs_mem[synapse], res, mul_res, mul_model])
            mac_model += layer_biases[neuron]
            mac_model = activations[i](mac_model)
            # мэмристоры
            wl = HARD_BIASES[neuron]['wl']
            bl = HARD_BIASES[neuron]['bl']
            res = conn.mode_9(246, 0, wl, bl)[0]
            mul = a2v(res)
            sign = np.sign(layer_biases[neuron])
            mul_res = mul * sign / SCALE_B / 0.3
            mac_mem += mul_res
            # пишем результат mac
            with open(fname_mac_result,'a', newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=",")
                file_wr.writerow([i, neuron, 'b', wl, bl, 246, res, mul_res, layer_biases[neuron]])
            mac_mem = activations[i](mac_mem)
            neurons_model.append(mac_model)
            neurons_mem.append(mac_mem)
        inputs = np.array(neurons_model)
        inputs_mem = np.array(neurons_mem)
        # scale_x = np.max(np.abs(inputs_mem))
        scale_x = 1
    outputs.append(np.argmax(softmax(neurons_model)))
    outputs_mem.append(np.argmax(softmax(neurons_mem)))
    # пишем в файл общий результат
    result_log.append(outputs[-1])
    result_log.append(outputs_mem[-1])
    with open(fname_io_result,'a', newline='', encoding='utf-8') as file:
        file_wr = csv.writer(file, delimiter=",")
        file_wr.writerow(result_log)

    all_times.append(time.time()-start_time)

print(f'Среднее время обработки одного вектора: {round(np.mean(all_times), 4)} с')

# оценка точности классификации
print(classification_report(outputs, y_test))
print(classification_report(outputs_mem, y_test))
