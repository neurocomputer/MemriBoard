"""
Окно списка запросов
"""

# pylint: disable=E0611, C0103, R0903, W0212

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from manager.blanks import gather

class RequestsList(QDialog):
    """
    Окно запросов
    """

    GUI_PATH = os.path.join("gui","uies","requests.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработка кнопок
        self.ui.button_ok.clicked.connect(self.close)
        # заполнение параметров
        self.fill_requests()

    def fill_requests(self) -> None:
        """
        Заполнение запросов
        """
        text = ""
        for item in self.parent.exp_list:
            text += f"Тикет:{item[0]}, задачи:{item[3]}\n"
            for req in item[2]:
                text += gather(req[0])
        self.text_commands.appendPlainText(text)
