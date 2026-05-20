from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import time
import requests
import os
import threading

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from manager.service.converters import convert_dac_to_volt, convert_adc_to_current
from manager import Manager

app = Flask(__name__)
CORS(app)

script_dir = os.path.dirname(os.path.abspath(__file__))
server_address = 'http://127.0.0.1:12345'
current_result = None
is_processing = False
man = Manager()

@app.route('/')
def index():
    return send_from_directory(script_dir, 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory(script_dir, 'style.css')

@app.route('/logo.svg')
def logo():
    return send_from_directory(script_dir, 'logo.svg')

@app.route('/start_measurement', methods=['POST'])
def start_measurement():
    global current_result, is_processing
    
    if is_processing:
        return jsonify({"status": "busy"})
    
    is_processing = True
    current_result = None
    
    def process():
        global current_result, is_processing
        file_path = os.path.join(script_dir, 'iv-curve.txt')
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                v = line.split(',')
                task_data = {
                    'mode_flag': int(v[0]) if v[0] else 7,
                    'vol': int(v[1]) if len(v) > 1 else 0,
                    't_ms': int(v[2]) if len(v) > 2 else 0,
                    't_us': int(v[3]) if len(v) > 3 else 0,
                    'sign': int(v[4]) if len(v) > 4 else 0,
                    'id': int(v[5]) if len(v) > 5 else 0,
                    'wl': int(v[6]) if len(v) > 6 else 0,
                    'bl': int(v[7]) if len(v) > 7 else 0
                }
                try:
                    requests.post(f'{server_address}/put_task', json=task_data, timeout=2)
                except:
                    pass
                timeout_start = time.time()
                timeout = 3
                result = None
                
                while time.time() - timeout_start < timeout:
                    try:
                        r = requests.get(f'{server_address}/get_result', timeout=2)
                        if r.status_code == 200:
                            data = r.json()
                            if data.get('data'):
                                result = data['data']
                                break
                    except:
                        pass
                    time.sleep(0.2)
                
                if result is None:
                    print(f"Таймаут ожидания результата")
                    continue
                current_result = {
                    'voltage': convert_dac_to_volt(dac_bit=man.dac_bit, vol_ref_dac=man.vol_ref_dac, dac_value=task_data['vol'], sign=task_data['sign']),
                    'current': convert_adc_to_current(man.dac_bit,
                                                        man.vol_ref_dac,
                                                        man.gain,
                                                        man.res_load,
                                                        man.vol_read,
                                                        man.adc_bit,
                                                        man.vol_ref_adc,
                                                        man.res_switches,
                                                        int(result[0]),
                                                        task_data['vol'],
                                                        task_data['sign'])
                }
                wait_start = time.time()
                while current_result is not None and time.time() - wait_start < 5:
                    time.sleep(0.1)
                current_result = None
            
        is_processing = False
        current_result = None
    
    thread = threading.Thread(target=process, daemon=True)
    thread.start()
    return jsonify({"status": "ok"})

@app.route('/get_result', methods=['GET'])
def get_result():
    global current_result
    if current_result is not None:
        res = current_result.copy()
        current_result = None
        return jsonify({"data": res})
    return jsonify({"data": None})

@app.route('/check_status', methods=['GET'])
def check_status():
    return jsonify({"is_processing": is_processing})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)