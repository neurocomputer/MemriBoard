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
    lang_pack: dict

    GUI_PATH = os.path.join("gui","uies","requests.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        # доп настройки
        self.setModal(True)
        # обработка кнопок
        self.ui.button_ok.clicked.connect(self.close)
        self.ui.button_save.clicked.connect(self.save_requests)
        # заполнение параметров
        self.fill_requests()

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("requests")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.button_ok.setText(self.lang_pack.get("ok"))
            self.ui.button_save.setText(self.lang_pack.get("save"))

    def fill_requests(self) -> None:
        """
        Заполнение запросов
        """
        text = ""
        for item in self.parent.exp_list:
            text += f"{self.lang_pack.get('ticket')}{item[0]}{self.lang_pack.get('tasks')}{item[2]}\n"
            for req in item[2]:
                text += gather(req[0])
        self.text_commands.appendPlainText(text)

    def save_requests(self) -> None:
        """
        Cохранение содержимого запроса
        """
        request = ""
        for item in self.parent.exp_list:
            request += f"{self.lang_pack.get('ticket')}{item[0]}{self.lang_pack.get('tasks')}{item[2]}\n"
            for req in item[2]:
                request += gather(req[0])
        if 0 < len(request):
            # открытие окна сохранения файла
            filepath, _ = QFileDialog.getSaveFileName()
            if filepath.endswith(".txt") is False:
                filepath = filepath + ".txt"
            with open (filepath, "w", encoding='utf-8') as file:
                file.write(request)
                file.close()
            show_warning_messagebox(parent=self, message=f'{self.lang_pack.get("saved_to")}{filepath}')
        else:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("empty"))
