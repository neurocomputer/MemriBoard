"""
Окно ожидания
"""

# pylint: disable=E0611

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal

class Wait(QDialog):
    """
    Окно ожидания во время эксперимента
    """

    GUI_PATH = os.path.join("gui","uies","wait.ui")
    history: list
    stop_experiment = pyqtSignal()

    def __init__(self, opener=None, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.opener = opener
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        # доп настройки
        self.setModal(True)
        
    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("wait")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("window_title"))

    def closeEvent(self, event) -> None:
        self.stop_experiment.emit()
        if self.opener == 'new_ann':
            self.parent.new_ann_dialog.fill_table_weights()
            event.accept()
        elif self.opener == 'crossbar':
            event.accept()
        elif self.opener == 'rram':
            self.parent.rram_dialog.apply_tresh()
            event.accept()
