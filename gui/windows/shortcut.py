
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt

class Shortcut(QDialog):
    """
    Окно информации о шорткатах
    """

    GUI_PATH = os.path.join("gui","uies","shortcut.ui")
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
        self.button_close.clicked.connect(self.close)
        # прочее
        self.change_language()
        
    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("shortcut")
        if ok:
            self.setWindowTitle(self.lang_pack.get("name"))
            self.label.setText(self.lang_pack.get("name"))
            self.label_3.setText(self.lang_pack.get("ctrlT"))
            self.label_5.setText(self.lang_pack.get("ctrlM"))
            self.label_7.setText(self.lang_pack.get("ctrlI"))
            self.label_10.setText(self.lang_pack.get("ctrlB"))
            self.label_11.setText(self.lang_pack.get("ctrlU"))
            self.label_13.setText(self.lang_pack.get("ctrlF"))
            self.button_close.setText(self.lang_pack.get("close"))

    def closeEvent(self, event):
        """
        Выход из окна шорткатов
        """
        event.accept()