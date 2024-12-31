"""
Окно истории
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
import csv
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHeaderView

from manager.service.saves import results_from_bytes
from manager.service import  d2v, a2r
from gui.src import show_warning_messagebox, bool_to_label

class History(QDialog):
    """
    Окно информации о ячейке
    """

    GUI_PATH = os.path.join("gui","uies","history.ui")
    experiments: list # эксперименты из базы
    tickets: list # тикеты из базы
    mode: str # режим открытия

    def __init__(self, parent=None, mode=None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # параметры таблицы table_history_experiments
        self.ui.table_history_experiments.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_history_experiments.setColumnCount(3)
        self.ui.table_history_experiments.setHorizontalHeaderLabels(["Дата", "Название", "Статус"])
        self.ui.table_history_experiments.itemClicked.connect(self.show_experiment_tickets)
        # параметры таблицы table_history_tickets
        self.ui.table_history_tickets.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_history_tickets.setColumnCount(3)
        self.ui.table_history_tickets.setHorizontalHeaderLabels(["Дата", "Тикет", "Статус"])
        # доп настройки
        self.setModal(True)
        # история
        self.experiments = []
        self.tickets = []
        self.fill_table_history_experiments()
        # обработчики кнопок
        self.ui.button_load.clicked.connect(self.load_experiment)
        self.ui.button_load_from_db.clicked.connect(self.export_ticket_from_db)
        self.ui.button_cancel.clicked.connect(self.close)
        self.ui.button_load.setDisabled(True)
        self.ui.button_load_from_db.setDisabled(True)

    def export_ticket_from_db(self) -> None:
        """
        Выгрузить данные по тикету из бд в csv
        """
        current_row = self.ui.table_history_tickets.currentRow()
        ticket_id = self.tickets[current_row][0]
        _, ticket_result = self.parent.man.db.get_ticket_from_id(ticket_id)
        all_raw_data = results_from_bytes(ticket_result[0][0])
        raw_dac = all_raw_data[0::2]
        raw_adc = all_raw_data[1::2]
        fname = f'{self.tickets[current_row][1]}_{self.tickets[current_row][2]}.csv'
        with open(fname,'w',newline='', encoding='utf-8') as file:
            file_wr = csv.writer(file, delimiter=";")
            file_wr.writerow(['dac', 'adc', 'vol', 'res'])
            for i,item in enumerate(raw_dac):
                file_wr.writerow([item,
                                  raw_adc[i],
                                  str(d2v(self.parent.man,item)).replace('.',','),
                                  str(a2r(self.parent.man,raw_adc[i])).replace('.',',')])
        show_warning_messagebox(f'Выгружено в файл {fname}')

    def load_experiment(self) -> None:
        """
        Загрузить эксперимент
        """
        current_row = self.ui.table_history_experiments.currentRow()
        experiment_id = self.experiments[current_row][0]
        self.parent.load_experiment(experiment_id)
        self.close()

    def fill_table_history_experiments(self) -> None:
        """
        Заполнить таблицу экспериментов
        """
        # стираем данные
        while self.ui.table_history_experiments.rowCount() > 0:
            self.ui.table_history_experiments.removeRow(0)
        if self.mode == "single":
            _, memristor_id = self.parent.man.db.get_memristor_id(self.parent.current_wl,
                                                                       self.parent.current_bl,
                                                                       self.parent.man.crossbar_id)
            _, self.experiments = self.parent.man.db.get_memristor_experiments(memristor_id)
        else:
            _, self.experiments = self.parent.man.db.get_experiments(self.parent.man.crossbar_id)
        # добавление инфы
        for item in self.experiments:
            #if not item[2] == 'measure':
            row_position = self.ui.table_history_experiments.rowCount()
            self.ui.table_history_experiments.insertRow(row_position)
            self.ui.table_history_experiments.setItem(row_position, 0, QTableWidgetItem(item[1]))
            self.ui.table_history_experiments.setItem(row_position, 1, QTableWidgetItem(item[2]))
            self.ui.table_history_experiments.setItem(row_position, 2, QTableWidgetItem(bool_to_label(item[3])))
        self.ui.table_history_experiments.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def show_experiment_tickets(self) -> None:
        """
        Показать тикеты эксперимента
        """
        # стираем данные
        while self.ui.table_history_tickets.rowCount() > 0:
            self.ui.table_history_tickets.removeRow(0)
        # определить experiment_id
        current_row = self.ui.table_history_experiments.currentRow()
        experiment_id = self.experiments[current_row][0]
        _, self.tickets = self.parent.man.db.get_experiment_tickets(experiment_id)
        # добавление инфы
        for item in self.tickets:
            row_position = self.ui.table_history_tickets.rowCount()
            self.ui.table_history_tickets.insertRow(row_position)
            self.ui.table_history_tickets.setItem(row_position, 0, QTableWidgetItem(item[1]))
            self.ui.table_history_tickets.setItem(row_position, 1, QTableWidgetItem(item[2]))
            self.ui.table_history_tickets.setItem(row_position, 2, QTableWidgetItem(bool_to_label(item[3])))
        self.ui.table_history_tickets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.button_load.setDisabled(False)
        self.ui.button_load_from_db.setDisabled(False)
        # поучаем рисунок
        status, image = self.parent.man.db.get_img_experiment(experiment_id)
        if status:
            pixmap = QPixmap()
            pixmap.loadFromData(image)
            self.ui.label_image.setPixmap(pixmap)

    def set_up_init_values(self) -> None:
        """
        Задать начальные значения
        """
        self.experiments = []
        self.tickets = []

    def closeEvent(self, event):
        """
        Выход из окна ифнормации
        """
        self.set_up_init_values()
        event.accept()
