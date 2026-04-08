
from flask import Flask, jsonify
import requests

class RemoteConnect:
    uri: str

    def __init__(self):
        self.uri = 'http://127.0.0.1:5000'
    
    def connect(self, address, port):
        """
        Подключиться к удаленному серверу
        """
        if not address:
            address = '127.0.0.1'
        if not port:
            port = '5000'
        status = False
        try:
            self.uri = f'http://{address}:{port}'
            response = requests.get(self.uri + '/ping')
            if response.status_code == 200:
                status = True
        except Exception as e:
            print(f'RemoteConnect.connect: {e}')
        return status
    
    def send_task(self, task):
        status = False
        try:
            response = requests.post(self.uri + '/put_task', json=task)
            if response.status_code == 200:
                status = True
        except Exception as e:
            print(f'RemoteConnect.send_task: {e}')
        return status

    def get_result(self):
        status = False
        result = []
        try:
            response = requests.get(self.uri + '/get_result')
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', [])
                status = True
        except Exception as e:
            print(f'RemoteConnect.get_result: {e}')
        return status, result
