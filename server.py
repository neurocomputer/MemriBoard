"""
Сервер для обмена тасками и данными
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

server = Flask(__name__)
tasks = []
results = []
CORS(server)  # разрешает все запросы

# Статусы
statuses = {
    "READY": 0, # готов к работе
    "PROCESSING": 1,   # таска в обработке
    "SUCCESS": 2,   # успешное завершение
    "ERROR": 3,  # ошибка выполнения таски (на стороне исполнителя)
    "FAILURE": 4 # неуказанная проблема
}

STATUS_READY = statuses["READY"]
STATUS_PROCESSING = statuses["PROCESSING"]
STATUS_SUCCESS = statuses["SUCCESS"]
STATUS_ERROR = statuses["ERROR"]
STATUS_FAILURE = statuses["FAILURE"]

# Сессии обмена данных
class Session:
    secret_key: str
    tasks: list
    results: list
    status: int

    def __init__(self, secret_key = "", status = 0):
        self.secret_key = secret_key
        self.status = status
        self.tasks = []
        self.results = []

    def compare_key(self, key=''):
        """
        Проверка тайного ключа
        """
        return self.secret_key == key
    
# хранилище сессий (id, Session)
sessions: dict[int, Session] = {}

def format_request(request):
    """
    Быстро разделить запрос на данные, получить ключ и проверить его.
    """
    try:
        data = request.get_json()
        session_id = data["session_id"]
        secret_key = data["secret_key"]
        status = sessions.get(session_id).compare_key(secret_key)
        return status, data
    except Exception as e:
        return False, e

@server.get("/")
def home():
    """
    Базовый минимум
    """
    return "Сервер готов к работе!"

@server.post("/start_session")
def start_session():
    ok, data = format_request(request)
    if ok:
        session = Session(data["secret_key"])
        sessions["session_id"] = session
        return jsonify({"status": STATUS_SUCCESS})
    return jsonify({"status": STATUS_FAILURE, "data": data})

@server.post("/ping")
def ping():
    """
    Пинг сервера
    """
    return jsonify({"status": STATUS_SUCCESS})

@server.post("/put_task")
def put_task():
    """
    Положить таску на сервер
    """
    ok, data = format_request(request)
    if ok:
        task = data["data"]
        sessions[data["session_data"]].tasks.append(task)
        return jsonify({"status": STATUS_SUCCESS})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/check_tasks_storage")
def check_tasks_storage():
    """
    Проверить, есть ли таски на сервере
    """
    ok, data = format_request(request)
    if ok:
        tasks_len = len(sessions[data["session_data"]].tasks)
        if tasks_len:
            return jsonify({"status": STATUS_SUCCESS})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/get_task")
def get_task():
    """
    Забрать таску с сервера
    """
    ok, data = format_request(request)
    if ok:
        task = sessions[data["session_data"]].tasks.pop()
        return jsonify({"status": STATUS_SUCCESS, "data": task})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/put_result")
def put_result():
    """
    Положить результат на сервер
    """
    ok, data = format_request(request)
    if ok:
        result = data["data"]
        sessions[data["session_data"]].results.append(result)
        return jsonify({"status": STATUS_SUCCESS})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/check_results_storage")
def check_results_storage():
    """
    Проверить, есть ли результаты на сервере
    """
    ok, data = format_request(request)
    if ok:
        res_len = len(sessions[data["session_data"]].results)
        if res_len:
            return jsonify({"status": STATUS_SUCCESS})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/get_result")
def get_result():
    """
    Забрать результат с сервера
    """
    ok, data = format_request(request)
    if ok:
        result = sessions[data["session_data"]].results.pop()
        return jsonify({"status": STATUS_SUCCESS, "data": result})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/clean_all")
def clean_all(): 
    """
    Очистить сервер
    """
    ok, data = format_request(request)
    if ok:
        sessions[data["session_data"]].tasks.clear()
        sessions[data["session_data"]].results.clear()
        return jsonify({"status": STATUS_SUCCESS})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/set_status")
def set_status():
    """
    Исполнитель устанавливает статус
    """
    ok, data = format_request(request)
    if ok:
        sessions[data["session_data"]].status = data["data"]
        return jsonify({"status": STATUS_SUCCESS})
    return jsonify({"status": STATUS_FAILURE})

@server.post("/get_status")
def get_status():
    """
    Получить статус исполнителя
    """
    ok, data = format_request(request)
    if ok:
        status = sessions[data["session_data"]].status
        return jsonify({"status": STATUS_SUCCESS, "data": status})
    return jsonify({"status": STATUS_FAILURE})

if __name__ == "__main__":
    server.run(host="127.0.0.1", port=12345)
