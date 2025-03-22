"""
Окно ожидания
"""

# pylint: disable=E0611

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

class Wait(QDialog):
    """
    Окно информации о ячейке
    """

    GUI_PATH = os.path.join("gui","uies","wait.ui")
    history: list

    def __init__(self, opener=None, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.opener = opener
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)

    def closeEvent(self, event) -> None:
        if self.opener == 'new_ann':
            self.new_ann_dialog.fill_table_weights()
            event.accept()
        elif self.opener == 'crossbar':
            event.accept()
