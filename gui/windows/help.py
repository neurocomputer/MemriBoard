"""
Окно справки
"""
import os
from PyQt5 import uic
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QWidget


class Help(QWidget):
    """
    Help window
    """
    
    GUI_PATH = os.path.join("gui","uies","help.ui")
    lang_pack: dict
    
    def __init__(self, parent=None) -> None:
        super().__init__()
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        
    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("help")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.help_path = os.path.join(*self.lang_pack.get("path").split('/'))
            # Загрузка справки
            self.url = QUrl.fromLocalFile(self.help_path)
            self.ui.textBrowser.setSource(self.url)
            
    def closeEvent(self, event):
        self.parent.help_dialog = None
        event.accept()