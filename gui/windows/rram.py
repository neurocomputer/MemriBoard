"""
Окно работы с rram
"""

import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog

class Rram(QDialog):
    """
    Работа с rram
    """

    GUI_PATH = os.path.join("gui","uies","rram.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # значения по умолчанию
        self.set_up_init_values()
        # обработчики кнопок
        self.ui.button_apply_tresh.clicked.connect(self.apply_tresh)
        self.ui.button_read.clicked.connect(self.parent.read_cell_all)

    def set_up_init_values(self) -> None:
        """
        Установка значений по умолчанию
        """
        self.ui.button_interrupt.setEnabled(False)
        self.ui.text_write.clear()
        self.ui.text_read.clear()
        self.parent._snapshot("rram")
        self.ui.label_rram_img.setPixmap(QPixmap(os.path.join("gui","uies","rram.png")))

    def apply_tresh(self) -> None:
        """
        Применение порога
        """
        tresh = self.ui.spin_tresh_read.value()
        self.parent._snapshot("rram_update", tresh)
        self.ui.label_rram_img.setPixmap(QPixmap(os.path.join("gui","uies","rram.png")))