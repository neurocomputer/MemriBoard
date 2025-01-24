"""
Карта кроссбара
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem
from PyQt5 import QtWidgets

from manager.service import r2w

class Map(QDialog):
    """
    Карта кроссбара
    """

    GUI_PATH = os.path.join("gui","uies","map.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработчик нажатия
        self.ui.table_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # стираем предыдущий выбор
        self.parent.current_wl = None
        self.parent.current_bl = None
        self.parent.current_last_resistance = None

    def enable_cell_choosing(self):
        """
        Разрешить выбор ячейки
        """
        self.ui.table_weights.itemDoubleClicked.connect(self.choose_cell)

    def choose_cell(self):
        """
        Выбрать ячейку
        """
        self.parent.current_bl = self.ui.table_weights.currentRow()
        self.parent.current_wl = self.ui.table_weights.currentColumn()
        self.parent.update_current_cell_info()
        self.close()

    def fill_table(self, mode='weights'):
        """
        Заполнить таблицу
        """
        # row count
        self.ui.table_weights.setRowCount(self.parent.man.row_num)
        # column count
        self.ui.table_weights.setColumnCount(self.parent.man.col_num)
        # table will fit the screen horizontally
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # заполнение весами
        if mode == 'weights':
            for i in range(self.parent.man.row_num):
                for j in range(self.parent.man.col_num):
                    if self.parent.all_resistances[i][j] == 0:
                        self.ui.table_weights.setItem(i,j, QTableWidgetItem('-'))
                    else:
                        self.ui.table_weights.setItem(i,j, QTableWidgetItem(str(round(r2w(self.parent.man.res_load, self.parent.all_resistances[i][j]),2))))
        # todo: можно добавить остальные варианты для вызова из других окон
        self.ui.table_weights.setHorizontalHeaderLabels([str(i) for i in range(self.parent.man.col_num)])
        self.ui.table_weights.setVerticalHeaderLabels([str(i) for i in range(self.parent.man.row_num)])

    def set_prompt(self, message):
        """
        Установить приветствие
        """
        self.ui.label_prompt.setText(message)

    def closeEvent(self, event):
        """
        Закрытие окна
        """
        self.set_prompt('')
        if self.parent.opener == 'mapping':
            if not self.parent.current_bl is None:
                self.parent.show_exp_settings_dialog()
        # todo: можно добавить остальные варианты для вызова из других окон
        event.accept()
