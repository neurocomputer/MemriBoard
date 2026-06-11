"""
Сайт для работы с мемристором
"""

import os
import csv
import time
import logging
import random
from logging.handlers import TimedRotatingFileHandler
from threading import Lock
from datetime import datetime
import requests
from typing import Union
from flask import Flask, render_template, jsonify, request, Response, stream_with_context

BOARD_ADRES = '127.0.0.1:12345' # адрес сервера для работы с платой
REQUESTS_TIMEOUT = 3 # таймаут в запросах requests
TIME_SLEEP = 10 # пауза между запросом и ответом
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, 'history.csv')
EXTERNAL_BOARD_SERVER = False

tasks = []
results = []

application = Flask(__name__)
server_lock = Lock()

# Циклический логгер по времени (ежедневная ротация)
log_handler = TimedRotatingFileHandler(
    os.path.join(SCRIPT_DIR, 'server.log'),      # Имя файла
    when='midnight',   # Ротация в полночь
    interval=1,        # Каждый 1 день
    backupCount=7,     # Хранить 7 дней
    encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

def convert_dac_to_volt(dac_bit: int, vol_ref_dac: float, dac_value: int, **kwargs) -> float:
    """
    Конвертация числа для ЦАП в напряжение

    Arguments:
        dac_value -- число для ЦАП
        kwargs -- знак напряжения

    Returns:
        vol_value -- значение в вольтах
    """
    vol_value = round(dac_value/((2**dac_bit-1)/vol_ref_dac),3)
    if 'sign' in kwargs:
        if kwargs['sign']: # если есть знак
            vol_value = -vol_value
    return vol_value

def convert_adc_to_res(gain: float,
                       res_load: float,
                       vol_read: float,
                       adc_bit: int,
                       vol_ref_adc: float,
                       res_switches: float,
                       adc_value: Union[str, int]) -> float:
    """
    Функция для перевода из АЦП в сопротивление. Если значение АЦП
    равно 0, то возвращает 2 МОм. Если с АЦП пришло не корректное
    значение и сопротивление получается отрицательное то оно заменяется
    на 1 Ом.

    Arguments:
        adc_value -- значение с АЦП

    Returns:
        res -- сопротивление мемристора
    """
    adc_value = int(adc_value)
    if adc_value < 20:
        adc_value = 20 # todo: это лучше вынести в настройки
    try:
        res = (gain*res_load*vol_read*(2**adc_bit))/ \
            (adc_value*vol_ref_adc) - res_switches - res_load
        res = round(res, 2)
    except ZeroDivisionError:
        res = 2000000 # todo: эта ветка больше не должна работать
    if res <= 0:
        res = 0.00000001
    return res

# Создание файла истории
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'request_type'])  # <-- меняем заголовок

def save_to_history(iv_data):
    """
    Сохраняет страну в CS
    """
    # todo: добавить сохранение вольтамперки
    with open(HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if iv_data:
            writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(len(iv_data))])
        else:
            writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Плата не подключена'])

def convert_command_to_task(command):
    command = command.strip()
    v = command.split(',')
    task_data = {
        'mode_flag': int(v[0]) if v[0] else 7,
        'vol': int(v[1]) if len(v) > 1 else 0,
        't_ms': int(v[2]) if len(v) > 2 else 0,
        't_us': int(v[3]) if len(v) > 3 else 0,
        'sign': int(v[4]) if len(v) > 4 else 0,
        'id': int(v[5]) if len(v) > 4 else 0,
        'wl': int(v[6]) if len(v) > 6 else 0,
        'bl': int(v[7]) if len(v) > 7 else 0
        }
    return task_data

def send_command(command, request_id):
    '''
    Послать команды на плату
    '''
    try:
        task_data = convert_command_to_task(command)
        task_data['id'] = request_id
        try:
            if EXTERNAL_BOARD_SERVER:
                requests.post(f'http://{BOARD_ADRES}/put_task', json=task_data, timeout=REQUESTS_TIMEOUT)
            else:
                put_task(task_data)
        except Exception as e:
            logger.error(f'Ошибка отправки таски: {e}')
    except Exception as e:
            logger.error(f'Ошибка формирования таски: {e}')

def get_result_command(command, request_id):
    """
    Получить результат команды
    """
    voltage = None
    current = None
    try:
        task_data = convert_command_to_task(command)
        task_data['id'] = request_id
        timeout = 1000
        while timeout:
            #if EXTERNAL_BOARD_SERVER:
            #    r = requests.get(f'http://{BOARD_ADRES}/get_result', timeout=REQUESTS_TIMEOUT)
            #    if r.status_code == 200:
            #        data = r.json()
            #        if data.get('data'):
            #            result = data['data']
            #            break
            #else:
            data = get_result()
            result = data['data']
            if result is not None:
                break
            timeout -= 1
        if result[1] == request_id:
            voltage = convert_dac_to_volt(12,
                                        5,
                                        #task_data['vol'],
                                        result[1], # напряжение берем из ответа
                                        sign=task_data['sign'])
            resistance = convert_adc_to_res(11,
                    3000,
                    0.3,
                    14,
                    5,
                    10,
                    result[0])
            current = 0
            if resistance != 0:
                current = voltage/resistance
    except Exception as e:
        logger.error(f'Ошибка получения ответа: {e}')            
    return voltage, current

def get_history():
    """
    Читает историю из CSV
    """
    history = []
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            history.append({'timestamp': row['timestamp'], 'request_type': row['request_type']})
    return history

def ping_board_server():
    """
    Пингануть сервак с платой
    """
    status = 0
    try:
        url = f'http://{BOARD_ADRES}/put_task'
        response = requests.get(url, timeout=100) # todo: разобраться с таймаутом
        if response.status_code == 200:
            status = 1
    except Exception as e:
        logger.error(f'Ошибка пинга сервера платы: {e}')
    return status

@application.route('/')
def index():
    client_ip = request.remote_addr
    logger.info(f'Загрузка страницы от {client_ip}')
    return render_template('index.html')

@application.route('/history', methods=['GET'])
def history():
    return jsonify(get_history())

@application.route('/measure-stream', methods=['POST'])
def measure_stream():
    """
    Создание SSE потока для получения данных
    """
    client_ip = request.remote_addr
    logger.info(f'Запрос на измерение от {client_ip}')
    # пинг
    if EXTERNAL_BOARD_SERVER:
        status = ping_board_server()
        if not status:
            logger.warning(f'Отклонён запрос от {client_ip} - плата не подключена')
            return jsonify({'error': 'Плата не подключена'}), 409
    # блокировка для очереди
    if not server_lock.acquire(blocking=False):
        logger.warning(f'Отклонён запрос от {client_ip} - сервер занят')
        return jsonify({'error': 'Сервер занят, подождите'}), 409

    iv_data = []
    
    tasks.clear()
    results.clear()

    def generate():
        """
        Генератор данных
        """
        logger.info(f'Начато измерение для {client_ip}')
        try:
            # читаем команды
            file_path = os.path.join(SCRIPT_DIR, 'static', 'iv-curve.txt')
            with open(file_path, 'r') as file:
                commands = file.readlines()
            # отправляем все команды в очередь команд в надежде что их заберет плата
            for request_id, command in enumerate(commands):
                send_command(command, request_id)
            time.sleep(TIME_SLEEP)
            # запрашиваем все результаты
            for request_id, command in enumerate(commands):
                voltage, current = get_result_command()
                iv_data.append((voltage, current))
                yield f"data: {voltage},{current}\n\n"
        except Exception as e:
            logger.error(f'Ошибка снятия ВАХ для {client_ip}: {e}')
        finally:
            yield f"data: DONE\n\n"
            save_to_history(iv_data)
            server_lock.release()

    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # Отключаем буферизацию nginx
    return Response(generate(), mimetype='text/event-stream')

############################## Эндпоинты сервера обмена данными

def put_task(data):
    """
    Положить таску на сервер
    """
    tasks.append(data)

@application.route('/ping', methods=['GET'])
def ping():
    """
    Пинг сервера
    """
    return jsonify({"status": "ok"})

@application.route('/check_tasks_storage', methods=['GET'])
def check_tasks_storage():
    """
    Проверить, есть ли таски на сервере
    """
    if tasks:
        return jsonify({"status": "ok"})
    return jsonify({"status":"empty"})

@application.route('/get_task', methods=['GET'])
def get_task():
    """
    Забрать таску с сервера
    """
    if len(tasks) == 0:
        return jsonify({"data": None})
    return jsonify({"data": tasks.pop(0)})

@application.route('/put_result', methods=['POST'])
def put_result():
    """
    Положить результат на сервер
    """
    data = request.get_json()
    results.append(data.get('result'))
    return jsonify({"status": "saved"})

def get_result():
    """
    Забрать результат с сервера
    """
    if len(results) == 0:
        return {"data": None}
    return {"data": results.pop(0)}

@application.route('/clean_all', methods=['POST'])
def clean_all(): 
    """
    Очистить сервер
    """
    tasks.clear()
    results.clear()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    application.run(host='127.0.0.1', debug=False, threaded=True)
