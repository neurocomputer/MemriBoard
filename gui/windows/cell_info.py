"""
Окно информации о ячейке
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

class CellInfo(QDialog):
    """
    Окно информации о ячейке
    """

    GUI_PATH = os.path.join("gui","uies","cell_info.ui")
    history: list

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # инфо
        self.fill_info()
        # обработчики кнопок
        self.ui.button_new_exp.clicked.connect(self.parent.show_exp_settings_dialog)
        self.ui.button_read_one_cells.clicked.connect(self.read_one_cell)
        self.ui.button_history.clicked.connect(lambda: self.parent.show_history_dialog(mode="single"))
        self.ui.button_cancel.clicked.connect(self.close)

    def read_one_cell(self):
        """
        Прочитать одну
        """
        self.ui.button_read_one_cells.setEnabled(False)
        self.parent.current_last_resistance = self.parent.read_cell(self.parent.current_wl,
                                                                    self.parent.current_bl)
        self.fill_info()
        self.ui.button_read_one_cells.setEnabled(True)

    def fill_info(self) -> None:
        """
        Заполнение информации
        """
        self.ui.label_bl.setText(f"BL = {self.parent.current_bl}")
        self.ui.label_wl.setText(f"WL = {self.parent.current_wl}")
        self.ui.label_resistance.setText(f"R = {self.parent.current_last_resistance} Ом")

    def set_up_init_values(self) -> None:
        """
        Задать начальные значения
        """
        self.parent.current_wl = None
        self.parent.current_bl = None
        self.parent.current_last_resistance = None

    def closeEvent(self, event):
        """
        Выход из окна ифнормации
        """
        self.parent.opener = None
        self.parent.fill_table()
        self.parent.color_table()
        self.set_up_init_values()
        event.accept()
