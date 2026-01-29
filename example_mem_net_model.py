"""
Запуск работы нейросети
"""

import pickle
from MemNet.componenets import load_model

model_path = 'PlaneDetection/best_class.custom'
model = load_model(model_path)

dataset_filename = 'PlaneDetection/[0.015907004475593567, 1.0]/train_test_data.pickle'
with open(dataset_filename, 'rb') as handle:
    train_test_data = pickle.load(handle)

test_images = train_test_data['test_images']
test_labels = train_test_data['test_labels']

output_data = model.predict(test_images)
print(output_data)

print(model.layers[0].biases)
print(model.layers[1].biases)
print(model.layers[2].biases)