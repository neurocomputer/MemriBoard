"""
Сервер для обмена тасками и данными
"""

from random import randint
from flask import Flask, request, jsonify

server = Flask(__name__)
tasks = []
results = []

@server.route('/')
def home():
    """
    Базовый минимум
    """
    return 'Сервер готов к работе!'

@server.route('/get_all', methods=['GET'])
def get_all():
    """
    Получить все таски и результаты (для отладки)
    """
    return jsonify({
        'data': (tasks, results)
    })

@server.route('/ping', methods=['GET'])
def ping():
    """
    Пинг сервера
    """
    return jsonify({"status": "ok"})

@server.route('/put_task', methods=['POST'])
def put_task():
    """
    Положить таску на сервер
    """
    data = request.get_json()
    tasks.append(data)
    #results.append((randint(0, 2**14-1), 1))
    return jsonify({"status": "saved"})

@server.route('/check_tasks_storage', methods=['GET'])
def check_tasks_storage():
    """
    Проверить, есть ли таски на сервере
    """
    if tasks:
        return jsonify({"status": "ok"})
    return jsonify({"status":"empty"})

@server.route('/get_task', methods=['GET'])
def get_task():
    """
    Забрать таску с сервера
    """
    return jsonify({"data": tasks.pop()})

@server.route('/put_result', methods=['POST'])
def put_result():
    """
    Положить результат на сервер
    """
    data = request.get_json()
    results.append(data.get('result'))
    return jsonify({"status": "saved"})

@server.route('/check_results_storage', methods=['GET'])
def check_results_storage():
    """
    Проверить, есть ли данные на сервере
    """
    if results:
        return jsonify({"status": "ok"})
    return jsonify({"status":"empty"})

@server.route('/get_result', methods=['GET'])
def get_result():
    """
    Забрать результат с сервера
    """
    return jsonify({"data": results.pop()})

if __name__ == '__main__':
    server.run(host='127.0.0.1', port=12345)
