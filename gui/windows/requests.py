"""
Окно списка запросов
"""

# pylint: disable=E0611, C0103, R0903, W0212

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog
from manager.blanks import gather
from gui.src import show_warning_messagebox
from manager.service.plots import calculate_counts_for_one_ticket

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
        self.text_commands.appendPlainText(self.get_requests())

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("requests")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.button_ok.setText(self.lang_pack.get("ok"))
            self.ui.button_save.setText(self.lang_pack.get("save"))
            
    def get_requests_for_ticket(self, ticket: dict) -> str:
        """Get requests string for one ticket"""
        count = calculate_counts_for_one_ticket(self.parent.man, ticket)
        text = f"{self.lang_pack.get('ticket')}{ticket['name']}{self.lang_pack.get('tasks')}{count}\n"
        task_gen = self.parent.man.menu[ticket['mode']]
        for req in task_gen(ticket['params'], ticket['terminate'], self.parent.man.blank_type):
            text += gather(req[0])
        return text

    def get_requests(self) -> str:
        """
        Заполнение запросов
        """
        text = ""
        for item in self.parent.exp_list:
            if item[1]['mode'] == 'algorithm':
                for ticket_exp in item[1]['tickets'].values():  # Ticket or experiment
                    if 'mode' in ticket_exp:  # Its a ticket
                        text += self.get_requests_for_ticket(ticket_exp)
                    else:  # Its an experiment
                        for ticket in ticket_exp.values():
                            text += self.get_requests_for_ticket(ticket)
            else:  # Standart ticket
                text += self.get_requests_for_ticket(item[1])
        return text

    def save_requests(self) -> None:
        """
        Cохранение содержимого запроса
        """
        request = self.get_requests()
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
