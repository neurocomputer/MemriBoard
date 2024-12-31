"""
Терминал
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from gui.src import show_warning_messagebox

class Terminal(QDialog):
    """
    Терминал
    """

    GUI_PATH = os.path.join("gui","uies","terminal.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработчик нажатия
        self.ui.button_send.clicked.connect(self.send_command)

    def send_command(self):
        """
        Послать команду
        """
        command = self.ui.lineedit_command.text()
        if command == '100':
            status, info = self.parent.man.conn.get_tech_info()
            if status:
                self.ui.label_answer.setText(str(info))
        else:
            command = command.replace("-", "")
            res = self.parent.man.conn.custom_impact(command + '\n', 0.01, 10)
            if ',' in command:
                if ''.join(command.strip().split(',')).isdigit():
                    res = self.parent.man.conn.custom_impact(command + '\n', 0.01, 10)
                    if len(res) == 2:
                        self.ui.label_answer.setText(f'adc: {res[0]}, id: {res[1]}')
                    else:
                        self.ui.label_answer.setText('Ответ не получен!')
                else:
                    show_warning_messagebox("Не корректный запрос!")
            else:
                show_warning_messagebox("Не корректный запрос!")
