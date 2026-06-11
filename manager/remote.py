import requests
from flask import jsonify

class RemoteConnect():
    uri: str

    def __init__(self):
        #self.uri = 'http://127.0.0.1:12345'
        self.uri = 'http://u3521007.isp.regruhosting.ru'

    def connect(self, address):
        """
        Подключиться к удаленному серверу
        """
        if not address:
            address = '127.0.0.1:12345'
        status = False
        try:
            #self.uri = f'http://{address}'
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

    def check_data(self, mode='result'):
        status = False
        print(self.uri + '/check_tasks_storage')
        try:
            if mode=='result':
                response = requests.get(self.uri + '/check_results_storage')
            elif mode =='task':
                response = requests.get(self.uri + '/check_tasks_storage')
            data = response.json()
            
            print(data)
            result = data.get('status')
            if result == 'ok':
                status = True
        except Exception as e:
            print(f'RemoteConnect.check_data: {e}')
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

    def get_task(self):
        status = False
        task = []
        try:
            response = requests.get(self.uri + '/get_task')
            if response.status_code == 200:
                data = response.json()
                task = data.get('data', [])
                print(task)
                status = True
        except Exception as e:
            print(f'RemoteConnect.get_task: {e}')
        return status, task
    
    def send_result(self, res):
        status = False
        try:
            data = {
                'result': list(res)
            }
            response = requests.post(self.uri + '/put_result', json=data)
            if response.status_code == 200:
                status = True
        except Exception as e:
            print(f'RemoteConnect.send_result: {e}')
        return status
