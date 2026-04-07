
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt

from gui.src import show_choose_window

class HTTPServer(QDialog):
    """
    Окно работы с http-сервером
    """

    GUI_PATH = os.path.join("gui","uies","http.ui")
    lang_pack: dict

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # загрузка ui
        self.setParent(parent, Qt.Window)
        self.parent = self.parent()
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(Qt.WindowModal)
        # кнопки
        self.button_disconnect.clicked.connect(self.disconnect)
        # прочее
        answer = show_choose_window(self, "Работать в режиме отправки данных?", rlj=self.parent.read_language_json)
        if answer:
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.tabBar().setEnabled(False)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.tabWidget.tabBar().setEnabled(False)

    def disconnect(self):
        """
        Отключение от сервера
        """
        self.close

    def closeEvent(self, event):
        """
        Выход из окна шорткатов
        """
        event.accept()