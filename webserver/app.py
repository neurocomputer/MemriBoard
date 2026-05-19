from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import threading
import time
import requests

app = Flask(__name__)
results = []
CORS(app)

def fetch_results():
    while True:
        try:
            r = requests.get('http://127.0.0.1:12345/get_result', timeout=2)
            if r.status_code == 200:
                data = r.json()
                if data.get('data'):
                    results.append(data['data'])
        except:
            pass
        time.sleep(0.5)

threading.Thread(target=fetch_results, daemon=True).start()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory('.', 'style.css')

@app.route('/logo.svg')
def logo():
    return send_from_directory('.', 'logo.svg')

@app.route('/iv-curve.txt')
def iv():
    return send_from_directory('.', 'iv-curve.txt')

@app.route('/put_task', methods=['POST'])
def put_task():
    data = request.get_json()
    try:
        requests.post('http://127.0.0.1:12345/put_task', json=data, timeout=2)
    except:
        pass
    return jsonify({"status": "ok"})

@app.route('/get_result', methods=['GET'])
def get_result():
    if results:
        return jsonify({"data": results.pop(0)})
    return jsonify({"data": None})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)