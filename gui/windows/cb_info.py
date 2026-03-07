"""
Окно информации о кроссбаре
"""

# pylint: disable=I1101,E0611

import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem
from PyQt5 import QtWidgets

class CbInfo(QDialog):
    """
    Информация о кроссбаре
    """

    GUI_PATH = os.path.join("gui","uies","cb_info.ui")
    lang_pack: dict

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # заполнение параметров
        self.fill_table()

    def fill_table(self):
        """
        Заполнить таблицу
        """
        ok, self.lang_pack = self.parent.read_language_json("cb_info")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            # разметка таблицы
            self.ui.table_cb_info.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.ui.table_cb_info.setRowCount(6)
            self.ui.table_cb_info.setColumnCount(1)
            self.ui.table_cb_info.setVerticalHeaderLabels([self.lang_pack.get("serial"),
                                                        self.lang_pack.get("comm"),
                                                        self.lang_pack.get("bl_am"),
                                                        self.lang_pack.get("wl_am"),
                                                        self.lang_pack.get("exp_am"),
                                                        self.lang_pack.get("last")])
            self.ui.table_cb_info.setHorizontalHeaderLabels([self.lang_pack.get("data")])
            # заполнение данных
            _, cb_info = self.parent.man.db.get_cb_info(self.parent.man.crossbar_id)
            for row in range (0, 4):
                self.ui.table_cb_info.setItem(row, 0, QTableWidgetItem(str(cb_info[0][row+1])))
            _, experiments = self.parent.man.db.get_experiments(self.parent.man.crossbar_id)
            if len(experiments) == 0:
                self.ui.table_cb_info.setItem(4, 0, QTableWidgetItem(self.lang_pack.get("no_exps")))
                self.ui.table_cb_info.setItem(5, 0, QTableWidgetItem(self.lang_pack.get("no_exps")))
            else:
                self.ui.table_cb_info.setItem(4, 0, QTableWidgetItem(str(len(experiments))))
                self.ui.table_cb_info.setItem(5, 0, QTableWidgetItem(experiments[0][1]))
            # ресайз таблицы
            self.ui.table_cb_info.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.ui.table_cb_info.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
