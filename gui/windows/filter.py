"""
Терминал
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from gui.src import show_warning_messagebox

class Filter(QDialog):
    """
    Терминал
    """

    GUI_PATH = os.path.join("gui","uies","filter.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработчик нажатия
        self.ui.button_apply.clicked.connect(self.button_apply_clicked)
        self.ui.button_reset.clicked.connect(self.button_reset_clicked)
        # заполняем спинбоксы
        if not self.parent.filter_rmin is None:
            self.ui.spinbox_rmin.setValue(self.parent.filter_rmin)
        if not self.parent.filter_rmax is None:
            self.ui.spinbox_rmax.setValue(self.parent.filter_rmax)

    def button_apply_clicked(self):
        """
        Раскрасить ячейки
        """
        r_min = self.ui.spinbox_rmin.value()
        r_max = self.ui.spinbox_rmax.value()
        self.parent.filter_rmin = r_min
        self.parent.filter_rmax = r_max
        self.parent.color_table()

    def button_reset_clicked(self):
        """
        Очистить раскраску
        """
        self.parent.filter_rmin = None
        self.parent.filter_rmax = None
        self.parent.color_table()
