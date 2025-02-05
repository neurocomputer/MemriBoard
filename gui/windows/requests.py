"""
Окно списка запросов
"""

# pylint: disable=E0611, C0103, R0903, W0212

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog
from manager.blanks import gather
from gui.src import show_warning_messagebox

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
        self.ui.button_save.clicked.connect(self.save_requests)
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

    def save_requests(self) -> None:
        # открытие окна сохранения файла
        filepath, _ = QFileDialog.getSaveFileName()
        if False == filepath.endswith(".txt"):
            filepath = filepath + ".txt"
        # сохранение содержимого запроса
        request = ""
        for item in self.parent.exp_list:
            request += f"Тикет:{item[0]}, задачи:{item[3]}\n"
            for req in item[2]:
                request += gather(req[0])
        with open (filepath, "w") as f:
            f.write(request)
            f.close()
        show_warning_messagebox(f'Выгружено в файл {filepath}')