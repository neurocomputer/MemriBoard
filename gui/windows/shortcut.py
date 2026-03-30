
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

class Shortcut(QDialog):
    """
    Окно информации о шорткатах
    """

    GUI_PATH = os.path.join("gui","uies","shortcut.ui")
    lang_pack: dict

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # кнопки
        self.ui.button_close.clicked.connect(self.close)
        # прочее
        self.change_language()
        
    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("shortcut")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.label.setText(self.lang_pack.get("name"))
            self.ui.label_3.setText(self.lang_pack.get("ctrlT"))
            self.ui.label_5.setText(self.lang_pack.get("ctrlM"))
            self.ui.label_7.setText(self.lang_pack.get("ctrlI"))
            self.ui.label_10.setText(self.lang_pack.get("ctrlB"))
            self.ui.label_11.setText(self.lang_pack.get("ctrlU"))
            self.ui.label_13.setText(self.lang_pack.get("ctrlF"))
            self.ui.button_close.setText(self.lang_pack.get("close"))

    def closeEvent(self, event):
        """
        Выход из окна шорткатов
        """
        event.accept()