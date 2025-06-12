import os
import csv
import time
import pickle
import datetime
import socket
import numpy as np

from MemriCORE.rpi_modes import RPI_modes
import RPi.GPIO as gpio

def parse_request(request):
    """
    Функция для разбора запроса
    """
    request = request.decode('unicode-escape')
    ampl_len = 5
    ref_len = 5
    if request [1] == '-':
        ampl_len += 1
    if request[8] == '-' or request[7] == '-':
        ref_len +=1
    ampl = request[1:ampl_len]
    ref = request[ampl_len+2:ampl_len+ref_len+2]
    ampl = float(ampl)
    ref = float(ref)
    return ampl, ref

def pack_answer(data):
    """
    Подготовка ответа
    """
    answer = r':{:.3f};/n'.format(data)
    return answer

activations = [lambda x: x if x>0 else 0,
               lambda x: x]

model_path = 'models/model_pid_2'
num_layers = 2

def softmax(vec):
    exponential = np.exp(vec)
    probabilities = exponential / np.sum(exponential)
    return probabilities

with open(os.path.join(model_path, 'new_weights.pkl'), 'rb') as fp:
    weights = pickle.load(fp)

with open(os.path.join(model_path, 'all_mem_weights_coordinates.pkl'), 'rb') as fp:
    all_mem_weights_coordinates_data = pickle.load(fp)
    mem_weights_coordinates = all_mem_weights_coordinates_data[0]
    mem_weights_scales = all_mem_weights_coordinates_data[1]

classes = [-0.05, -0.035, -0.012, 0.012, 0.035, 0.075, 0.125, 0.175, 0.225, 0.25]

scale_x = 1.76636

gpio.setwarnings(False)
conn = RPI_modes()

def a2v(adc_value:int):
    _vol_ref_adc = 5
    _adc_bit = 14
    _gain = 11.11
    vol_value = round(((adc_value * _vol_ref_adc)/((2 ** _adc_bit) - 1)) / _gain, 5)
    return vol_value

def process(inputs):

    # создаем файл для сохранения результата умножения
    now = datetime.datetime.now()
    formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
    fname_mac_result = os.path.join(result_dir, f'mac_{formatted_date}.csv')
    with open(fname_mac_result,'w', newline='', encoding='utf-8') as file:
        file_wr = csv.writer(file, delimiter=",")
        file_wr.writerow(['wl', 'bl', 'dac', 'adc', 'res', 'truth'])

    counter_params = 0
    inputs_mem = inputs
    result_log = []
    result_log.append(inputs[0])
    result_log.append(inputs[1])
    for i in range(num_layers):
        inputs_mem = list(map(lambda x: round(x/scale_x*0.3*4096/5), inputs_mem))
        layer_weights = weights[counter_params]
        HARD_WEIGHTS = mem_weights_coordinates[counter_params]
        counter_params += 1
        layer_biases = weights[counter_params]
        HARD_BIASES = mem_weights_coordinates[counter_params]
        counter_params += 1
        neurons_model = []
        neurons_mem = []
        SCALE = mem_weights_scales[i]
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
                sign = np.sign(layer_weights[synapse][neuron])
                mul_res = mul * sign * SCALE / 0.3 * scale_x
                mac_mem += mul_res
                # пишем результат mac
                with open(fname_mac_result,'a', newline='', encoding='utf-8') as file:
                    file_wr = csv.writer(file, delimiter=",")
                    file_wr.writerow([wl, bl, inputs_mem[synapse], res, mul_res, mul_model])
                #print(mul_model, mul_res)
            mac_model += layer_biases[neuron]
            mac_model = activations[i](mac_model)
            # мэмристоры
            wl = HARD_BIASES[neuron]['wl']
            bl = HARD_BIASES[neuron]['bl']
            res = conn.mode_9(246, 0, wl, bl)[0]
            mul = a2v(res)
            sign = np.sign(layer_biases[neuron])
            mul_res = mul * sign * SCALE
            mac_mem += mul_res
            # пишем результат mac
            with open(fname_mac_result,'a', newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=",")
                file_wr.writerow([wl, bl, 246, res, mul_res, layer_biases[neuron]])
            mac_mem = activations[i](mac_mem)
            neurons_model.append(mac_model)
            neurons_mem.append(mac_model)
        inputs = np.array(neurons_model)
        inputs_mem = np.array(neurons_mem)
    # пишем в файл общий результат
    result_log.append(np.argmax(softmax(neurons_model)))
    result_log.append(np.argmax(softmax(neurons_mem)))
    with open(fname_io_result,'a', newline='', encoding='utf-8') as file:
        file_wr = csv.writer(file, delimiter=",")
        file_wr.writerow(result_log)

    print(f'Модель TF: {classes[int(np.argmax(softmax(neurons_model)))]}, Мемристоры: {classes[int(np.argmax(softmax(neurons_mem)))]}')
    return classes[int(np.argmax(softmax(neurons_mem)))]
    # return classes[int(np.argmax(softmax(neurons_model)))]

# создаем папку для сохранения результата
now = datetime.datetime.now()
formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
result_dir = os.path.join(model_path, f'experiment_{formatted_date}')
os.mkdir(result_dir)

# создаем файл для сохранения результата общего
now = datetime.datetime.now()
formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
fname_io_result = os.path.join(result_dir, f'IO_{formatted_date}.csv')
with open(fname_io_result,'w', newline='', encoding='utf-8') as file:
    file_wr = csv.writer(file, delimiter=",")
    file_wr.writerow(['inputs0', 'inputs1', 'outputs', 'outputs_mem'])

s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)

s.bind (('192.168.218.223', 50000))

print('Connecting to Master @ 192.168.218.223:50000')

count = 0

while True:
    print()
    data_recieved, client = s.recvfrom (21)
    ref, ampl = parse_request(data_recieved)
    print(f'Получены значния: {ampl}, {ref} от {client[0]}:{client[1]}')
    output = process(np.array([ampl, ref]))
    answer = pack_answer(output)
    s.sendto(answer.encode('ascii'), ('192.168.218.29', 61556))
    count += 1
    answer = answer.encode('ascii')
    print(f'Отправлен ответ №{count}: {answer}')
    time.sleep(0.1)
