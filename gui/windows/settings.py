"""
Окно настроек
"""

# pylint: disable=E0611, C0103, R0903, W0212

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

class Settings(QDialog):
    """
    Окно настроек
    """

    GUI_PATH = os.path.join("gui","uies","settings.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработка кнопок
        self.ui.button_save.clicked.connect(self.save_settings)
        self.ui.button_cancel.clicked.connect(self.close)
        self.ui.button_update.clicked.connect(self.update_settings)
        # заполнение параметров
        self.fill_settings()

    def fill_settings(self) -> None:
        """
        Заполнение основных настроек
        """
        self.ui.choose_adc_bit.setCurrentText(str(self.parent.man._adc_bit))
        self.ui.choose_gain.setValue(self.parent.man._gain)
        self.ui.choose_software_cc.setValue(self.parent.man.soft_cc)

    def save_settings(self) -> None:
        """
        Сохранение настроек
        """
        self.parent.man.save_settings(adc_bit = self.ui.choose_adc_bit.currentText(),
                                      gain = str(self.ui.choose_gain.value()),
                                      soft_cc = str(self.ui.choose_software_cc.value()))
        self.close()

    def update_settings(self) -> None:
        """
        Считать настройки из файла и обновить
        """
        self.parent.man.read_settings()
        self.fill_settings()

    def closeEvent(self, event):
        """
        Закрытие
        """
        event.ignore()
        self.hide()
