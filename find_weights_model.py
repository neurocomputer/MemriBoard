import os
import copy
import pickle
import numpy as np

model_path = 'models/model_pid_8'

with open(os.path.join(model_path, 'new_weights.pkl'), 'rb') as fp:
    weights = pickle.load(fp)

with open(os.path.join(model_path, 'all_mem_weights.pkl'), 'rb') as fp:
    all_weights = pickle.load(fp)

num_layers = 2
counter_params = 0

mem_weights_coordinates = []
mem_weights_scales = []

for i in range(num_layers):
    ann_weights = weights[counter_params]
    counter_params += 1

    ann_biases = weights[counter_params]
    counter_params += 1

    #1. опредиляем скеил
    scale_w = 0.96 / np.max(np.abs(ann_weights))
    scale_b = 0.96 / np.max(np.abs(ann_biases))

    print(f'scale_w {scale_w}')
    
    #2 скейлм веса
    ann_weights_scaled = np.abs(copy.deepcopy(ann_weights)*scale_w)
    ann_biases_scaled = np.abs(copy.deepcopy(ann_biases)*scale_b)

    #3 ищим ближайшие занчения

    HARD_WEIGHTS = []

    for i in range(ann_weights_scaled.shape[0]):
        temp_HARD_WEIGHTS = [] 
        for j in range(ann_weights_scaled.shape[1]):
            temp_w = np.abs(copy.deepcopy(all_weights)-ann_weights_scaled[i][j])         
            wl_bl = np.unravel_index(np.argmin(temp_w),temp_w.shape)
            print(f'wl {wl_bl[1]} bl {wl_bl[0]} Wo = {ann_weights[i][j]} Ws = {ann_weights_scaled[i][j]} Wm = {all_weights[wl_bl[0]][wl_bl[1]]} ')
            temp_HARD_WEIGHTS.append({'wl': wl_bl[1], 'bl': wl_bl[0]})
        HARD_WEIGHTS.append(temp_HARD_WEIGHTS)

    print(f'scale_b {scale_b}')

    HARD_BIASES = []

    for i in range(len(ann_biases_scaled)):
        temp_b = np.abs(copy.deepcopy(all_weights)-ann_biases_scaled[i])
        wl_bl = np.unravel_index(np.argmin(temp_b),temp_b.shape)
        print(f'wl {wl_bl[1]} bl {wl_bl[0]} Bo = {ann_biases[i]} Bs = {ann_biases_scaled[i]} Bm = {all_weights[wl_bl[0]][wl_bl[1]]}')
        HARD_BIASES.append({'wl': wl_bl[1], 'bl': wl_bl[0]})

    mem_weights_coordinates.append(np.transpose(HARD_WEIGHTS))
    mem_weights_coordinates.append(HARD_BIASES)
    mem_weights_scales.append(scale_w)
    mem_weights_scales.append(scale_b)

with open(os.path.join(model_path, 'all_mem_weights_coordinates.pkl'), 'wb') as fp:
    pickle.dump([mem_weights_coordinates, mem_weights_scales], fp)
