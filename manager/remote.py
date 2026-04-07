
from flask import Flask, jsonify
import requests

class RemoteConnect:
    
    def connect(self, address, port):

        """
        Подключиться к удаленному серверу
        """
        # address = self.ui.lineedit_address.text()
        if not address:
            address = '0.0.0.0'
        # port = self.ui.lineedit_port.text()
        if not port:
            port = '5000'
        status = False
        try:
            self.uri = f'http://{address}:{port}'
            # self.ui.text_log.append(f"Подключаемся к {uri}")
            # пинг
            # data = {"text": ""}
            response = requests.get(self.uri + '/ping')
            if response.status_code == 200:
                status = True
                # self.ui.text_log.append(f"Подключение успешно.")
                # self.parent.show_http_dialog()
            # else:
            #     self.ui.text_log.append(f"Ошибка сервера: {response.status_code}")
            #     self.ui.text_log.append(response.text)
        # except requests.exceptions.ConnectionError:
            # self.ui.text_log.append(f"Ошибка: Не удалось подключиться к серверу по адресу {uri}")
        except Exception as e:
            print(e)
            # self.ui.text_log.append(f"Ошибка при подключении к http-серверу: {e}")
        return status
    
    def send_task(self, task):
        response = requests.post(self.uri + '/put_task', task)
        return response

    def get_answer(self):
        response = requests.get(self.uri + '/get_result')
        return response.text
