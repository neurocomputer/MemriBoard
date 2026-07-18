"""
Окно справки
"""
import os
from typing import Union
from PyQt5 import uic
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMainWindow, QDialog


class Help(QDialog):
    """
    Help window
    """
    
    GUI_PATH = os.path.join("gui","uies","help.ui")
    lang_pack: dict
    current_section: str
    combo_indexes = ['manual', 'algorithms']
    
    def __init__(self, main_window: QMainWindow, parent=None, section: Union[str, None] = None) -> None:
        super().__init__(parent=parent)
        self.parent = parent
        self.main_window = main_window
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # Выбор раздела
        if section is None:
            self.current_section = 'manual'
        else:
            self.current_section = section
        self.change_language()
        # ComboBox
        self.ui.comboBox_section.currentIndexChanged.connect(self.on_section_change)
        
    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.main_window.read_language_json("help")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.label_section.setText(self.lang_pack.get("section"))
            self.paths = {
                'manual': os.path.join(*self.lang_pack.get("manual_path").split('/')),
                'algorithms': os.path.join(*self.lang_pack.get("algorithms_path").split('/'))
            }
            # ComboBox
            self.ui.comboBox_section.clear()
            self.ui.comboBox_section.addItems([
                self.lang_pack.get('manual'),
                self.lang_pack.get('algorithms')
            ])
            self.ui.comboBox_section.setCurrentText(self.lang_pack.get(self.current_section))
            # Загрузка справки
            self.update_text_browser()
            
    def update_text_browser(self) -> None:
        """Обновление справки"""
        url = QUrl.fromLocalFile(self.paths[self.current_section])
        self.ui.textBrowser.setSource(url)
        
    def on_section_change(self) -> None:
        """Изменение раздела справки"""
        self.current_section = self.combo_indexes[self.ui.comboBox_section.currentIndex()]
        self.update_text_browser()
            
    def closeEvent(self, event):
        self.main_window.help_dialog = None
        event.accept()