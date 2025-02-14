"""
Окно информации о кроссбаре
"""

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem
from PyQt5 import QtWidgets
from gui.src import show_warning_messagebox

class Cb_info(QDialog):
    """
    Информация о кроссбаре
    """

    GUI_PATH = os.path.join("gui","uies","cb_info.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработчик нажатия
        self.ui.button_close.clicked.connect(self.close)
        # заполнение параметров
        self.fill_table()

    def fill_table(self):
        """
        Заполнить таблицу
        """
        # разметка таблицы
        self.ui.table_cb_info.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_cb_info.setRowCount(6)
        self.ui.table_cb_info.setColumnCount(1)
        self.ui.table_cb_info.setVerticalHeaderLabels(["Серийный номер кроссбара", "Комментарий", "Количество BL", "Количество WL", "Количество экспериментов", "Последний эксперимент"])
        self.ui.table_cb_info.setHorizontalHeaderLabels(["Данные"])
        # заполнение данных
        _, cb_info = self.parent.man.db.get_cb_info(self.parent.man.crossbar_id)
        for row in range (0, 4):
            self.ui.table_cb_info.setItem(row, 0, QTableWidgetItem(str(cb_info[0][row+1])))
        _, experiments = self.parent.man.db.get_experiments(self.parent.man.crossbar_id)
        last = experiments[0][1]
        for experiment in experiments:
            if experiment[1] <= last:
                last = experiment[1]
        self.ui.table_cb_info.setItem(4, 0, QTableWidgetItem(str(len(experiments))))
        self.ui.table_cb_info.setItem(5, 0, QTableWidgetItem(last))
        # ресайз таблицы
        self.ui.table_cb_info.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.table_cb_info.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
