"""
Терминал
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

class Filter(QDialog):
    """
    Терминал
    """

    GUI_PATH = os.path.join("gui","uies","filter.ui")
    lang_pack: dict

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        # доп настройки
        self.setModal(True)
        # обработчик нажатия
        self.ui.button_apply.clicked.connect(self.button_apply_clicked)
        self.ui.button_reset.clicked.connect(self.button_reset_clicked)
        # заполняем спинбоксы
        if self.parent.filter_rmin is not None:
            self.ui.spinbox_rmin.setValue(self.parent.filter_rmin)
        if self.parent.filter_rmax is not None:
            self.ui.spinbox_rmax.setValue(self.parent.filter_rmax)
            
    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("filter")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.button_apply.setText(self.lang_pack.get("apply"))
            self.ui.button_reset.setText(self.lang_pack.get("clear"))

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
