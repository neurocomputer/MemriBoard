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
    lang_pack: dict

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        # доп настройки
        self.setModal(True)
        # обработчик нажатия
        self.ui.button_send.clicked.connect(self.send_command)

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("terminal")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.button_send.setText(self.lang_pack.get("send"))
            if self.parent.man.driver_attr['custom_impact'] is None:
                self.ui.textEdit_answer.setPlainText(self.lang_pack.get("terminal_unavailable"))

    def send_command(self):
        """
        Послать команду
        """
        command = self.ui.lineedit_command.text()
        if command == '100':
            status, info = self.parent.man.conn.get_tech_info()
            if status:
                self.ui.textEdit_answer.setPlainText(str(info))
        else:
            if self.parent.man.driver_attr['custom_impact'] == 'visa':  # VISA instruments
                res = self.parent.man.conn.custom_impact(command, 0, 0)
                if res.startswith('ERROR'):
                    show_warning_messagebox(parent=self, message=self.lang_pack.get('error_occurred') + '\n' + res)
                else:
                    self.ui.textEdit_answer.setPlainText(res)
            elif self.parent.man.driver_attr['custom_impact'] == 'arduino':
                command = command.replace("-", "")
                res = self.parent.man.conn.custom_impact(command + '\n', 0.01, 10)
                if ',' in command:
                    if ''.join(command.strip().split(',')).isdigit():
                        res = self.parent.man.conn.custom_impact(command + '\n', 0.01, 10)
                        if len(res) == 2:
                            self.ui.textEdit_answer.setPlainText(f'adc: {res[0]}, id: {res[1]}')
                        else:
                            self.ui.textEdit_answer.setPlainText(self.lang_pack.get("no_answer"))
                    else:
                        show_warning_messagebox(parent=self, message=self.lang_pack.get("req_inc"))
                else:
                    show_warning_messagebox(parent=self, message=self.lang_pack.get("req_inc"))
            else:
                show_warning_messagebox(parent=self, message=self.lang_pack.get("terminal_unavailable"))
