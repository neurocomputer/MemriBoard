"""
Полносвязный слой на мемристорах
"""

import numpy as np
from MemNet.componenets import Sequential, Dense, Conv2D, Flatten

def custom_matmul(inputs):
    return inputs @ weights[0]

# создание модели с одним слоем Dense
my_model = Sequential()
weights = [np.random.normal(size=(16,8)),]
dense_layer = Dense(weights=weights)
dense_layer.matmul = custom_matmul
my_model.add(dense_layer)

input_data = np.random.normal(size=(10, 16))

print(my_model.predict(input_data))
print()
print(input_data @ weights[0])
