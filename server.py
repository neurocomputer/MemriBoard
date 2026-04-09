from flask import Flask, request, jsonify
from random import randint

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
    Положить данные на сервер
    """
    data = request.get_json()
    tasks.append(data)

    #results.append((randint(0, 2**14-1), 1))

    return jsonify({"status": "saved"})

@server.route('/check_tasks_storage', methods=['GET'])
def check_tasks_storage():
    """
    Проверить, есть ли данные на сервере
    """
    if tasks:
        return jsonify({"status": "ok"})
    return jsonify({"status":"empty"})

@server.route('/get_task', methods=['GET'])
def get_task():
    """
    Забрать все данные с сервера
    """
    return jsonify({"data": tasks.pop()})

@server.route('/put_result', methods=['POST'])
def put_answer():
    """
    Положить данные на сервер
    """
    data = request.get_json()
    results.append(data.get('result'))
    return jsonify({"status": "saved"})

@server.route('/check_results_storage', methods=['GET'])
def check_answers_storage():
    """
    Проверить, есть ли данные на сервере
    """
    if results:
        return jsonify({"status": "ok"})
    return jsonify({"status":"empty"})

@server.route('/get_result', methods=['GET'])
def get_answer():
    """
    Забрать все данные с сервера
    """
    return jsonify({"data": results.pop()})

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)