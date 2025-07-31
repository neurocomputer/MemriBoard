"""
Окно для работы с ИНС
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
import copy
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHeaderView, QFileDialog

from manager.service import r2a, r2w, w2r, a2r, v2d, d2v
from manager.service.plots import calculate_counts_for_ticket
from manager.service.global_settings import TICKET_PATH
from gui.src import show_warning_messagebox, choose_cells, open_file_dialog, write_csv_data
from gui.windows.apply import ApplyExp

class NewAnn(QDialog):
    """
    Окно для работы с ИНС
    """

    GUI_PATH = os.path.join("gui","uies","new_ann.ui")
    cells_coordinates_all: list = [] # координаты ячеек (wl, bl)
    cells_coordinates_choosen: list = [] # координаты ячеек (wl, bl)
    cells_weights_all = {} # все веса
    cells_resistances_all: dict = {} # текущие сопротивления ячеек (wl, bl):res
    weights_target_all: list = [] # веса целевые списком
    weights_status: dict = {} # статусы весов
    target_cells_resistances: dict = {} # словарь с сопротивлениями целевыми и ячейками
    target_resistances: list = []
    counter: int # счетчик для прогрессбара
    data_for_plot_y: list # данные для отрисовки (сопротивления)
    xlabel_text: str = 'Отсчеты'
    ylabel_text: str = 'Сопротивление, Ом'
    ticket_image_name: str = "temp.png"
    application_status: str = 'stop'
    ticket = None
    coordinates: list = [] # координаты для окна ApplyExp
    written_cells: list = []
    not_writen_cells: list = []
    written_weights: list = []
    not_written_weights: list = []
    map_thread: ApplyExp

    # значения по умолчанию для сигнала записи
    PROG_COUNT = 3
    RESET_VOL_MIN = 0.3
    RESET_VOL_MAX = 1.2
    RESET_STEP = 0.01
    SET_VOL_MIN = 0.3
    SET_VOL_MAX = 1.2
    SET_STEP = 0.01

    def __init__(self, parent=None, mode=None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # начальные значения
        self.set_up_init_values()
        # нажатия кнопок вкладка Веса
        self.ui.button_load_good_cells.clicked.connect(self.button_load_good_cells_clicked)
        self.ui.button_map_weights.clicked.connect(self.button_map_weights_clicked)
        self.ui.button_cancel_map_weights.clicked.connect(self.button_cancel_map_weights_clicked)
        self.ui.button_download.clicked.connect(self.button_download_clicked)
        self.ui.button_choose_weights.clicked.connect(self.button_choose_weights_clicked)
        self.ui.button_drop_cells.clicked.connect(self.button_drop_cells_clicked)
        self.ui.button_drop_weights.clicked.connect(self.button_drop_weights_clicked)
        self.ui.button_update_cells.clicked.connect(self.button_update_cells_clicked)
        # нажатия кнопок вкладка Сеть
        # self.ui.table_ann_weights.setSortingEnabled(True) # Включаем сортировку
        # self.ui.table_ann_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # self.ui.table_ann_weights.setColumnCount(6)
        # self.ui.table_ann_weights.setHorizontalHeaderLabels(["W", "BL", "WL", "Rm (Ом)", "Rt (Ом)", "Статус"])
        # self.ui.table_ann_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # обработчики событий
        self.ui.spinbox_correction_weight.valueChanged.connect(self.on_spinbox_correction_weight_changed)
        self.ui.spinbox_r_min.valueChanged.connect(self.on_spinbox_correction_weight_changed)
        self.ui.spinbox_r_max.valueChanged.connect(self.on_spinbox_correction_weight_changed)
        # параметры таблицы table_weights
        # self.ui.table_weights.setSortingEnabled(True) # Включаем сортировку
        self.ui.table_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_weights.setColumnCount(5)
        self.ui.table_weights.setHorizontalHeaderLabels(["BL", "WL", "Rm (Ом)", "W", "Статус"])
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # параметры таблицы table_match
        # self.ui.table_match.setSortingEnabled(True) # Включаем сортировку
        self.ui.table_match.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_match.setColumnCount(7)
        self.ui.table_match.setHorizontalHeaderLabels(["id", "W", "Rt (Ом)", "Rm (Ом)", "BL", "WL", "Статус"])
        self.ui.table_match.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # заполняем таблицу
        for bl in range(self.parent.man.row_num):
            for wl in range(self.parent.man.col_num):
                self.cells_coordinates_all.append((wl, bl))
        self.fill_table_weights()
        # комбинация кнопок
        self.button_start_combination()
        if self.parent.opener == 'math':
            self.ui.button_load_good_cells.setEnabled(False)
            self.ui.button_drop_cells.setEnabled(False)
            self.ui.button_drop_weights.setEnabled(False)
        # загружаем тикет
        ticket_name = self.parent.man.ap_config['gui']['program_ticket']
        self.ticket = self.parent.read_ticket_from_disk(ticket_name)
        # меняем параметры тикета
        self.ticket['params']['v_dir_strt_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.RESET_VOL_MIN)
        self.ticket['params']['v_dir_stop_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.RESET_VOL_MAX)
        self.ticket['params']['v_dir_step_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.RESET_STEP)
        self.ticket['params']['v_rev_strt_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.SET_VOL_MIN)
        self.ticket['params']['v_rev_stop_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.SET_VOL_MAX)
        self.ticket['params']['v_rev_step_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.SET_STEP)
        self.ticket['params']['count'] = self.PROG_COUNT
        # привязываем к кнопке
        self.ui.button_signal_parameters.clicked.connect(self.change_signal_parameters)
        self.ui.button_random_weights.clicked.connect(self.generate_random_weights)

    def generate_random_weights(self):
        """
        Сгенерировать рандомные веса
        """
        # получаем с интерфейса сопротивления
        res_min = self.ui.spinbox_r_min.value()
        res_max = self.ui.spinbox_r_max.value()
        random_res = np.random.uniform(res_min, res_max, size=(self.parent.man.row_num*self.parent.man.col_num,))
        if self.mode == 'matmul':
            random_weights = map(lambda x: self.parent.man.sum_gain/float(x), random_res)
        else:
            random_weights = map(lambda x: r2w(self.parent.man.res_load, float(x)), random_res)
        self.weights_target_all = list(random_weights)
        #print(self.weights_target_all)
        self.fill_table_match()

    def change_signal_parameters(self):
        """
        Изменить параметры сигнала записи
        """
        self.parent.show_signal_dialog(self.ticket, "edit_for_programming")

    def apply_edit_to_prog_ticket(self):
        """
        Обмен тикетом через диск
        """
        self.ticket = self.parent.read_ticket_from_disk("temp.json")
        os.remove(os.path.join(TICKET_PATH,"temp.json"))
        self.RESET_VOL_MIN = d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.ticket['params']['v_dir_strt_inc'])
        self.RESET_VOL_MAX = d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.ticket['params']['v_dir_stop_inc'])
        self.RESET_STEP = d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.ticket['params']['v_dir_step_inc'])
        self.SET_VOL_MIN = d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.ticket['params']['v_rev_strt_inc'])
        self.SET_VOL_MAX = d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.ticket['params']['v_rev_stop_inc'])
        self.SET_STEP = d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.ticket['params']['v_rev_step_inc'])
        self.PROG_COUNT = self.ticket['params']['count']

    # методы для таблицы с сопротивлениями

    def fill_table_weights(self): # +
        """
        Заполнение таблицы весов
        """
        # стираем данные
        self.cells_resistances_all = {}
        while self.ui.table_weights.rowCount() > 0:
            self.ui.table_weights.removeRow(0)
        for item in self.cells_coordinates_all:
            # получаем из базы данные
            _, memristor_id = self.parent.man.db.get_memristor_id(item[0], item[1], self.parent.man.crossbar_id)
            _, resistance = self.parent.man.db.get_last_resistance(memristor_id)
            self.cells_resistances_all[item] = resistance
            # вносим в таблицу
            row_position = self.ui.table_weights.rowCount()
            self.ui.table_weights.insertRow(row_position)
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, item[1]) # Устанавливаем BL
            self.ui.table_weights.setItem(row_position, 0, qtable_item)
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, item[0]) # Устанавливаем WL
            self.ui.table_weights.setItem(row_position, 1, qtable_item)
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, resistance) # Устанавливаем текущее сопротивление
            self.ui.table_weights.setItem(row_position, 2, qtable_item)
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.update_weights_table_weights()
        self.update_good_cels()

    def update_weights_table_weights(self): # +
        """
        Обновить текущие веса
        """
        weights_correction = self.ui.spinbox_correction_weight.value()
        self.cells_weights_all = {}
        for _, item in enumerate(self.cells_coordinates_all):
            resistance = self.cells_resistances_all[item]
            if self.mode == 'matmul':
                weight = self.parent.man.sum_gain/resistance * weights_correction
            else:
                weight = r2w(self.parent.man.res_load, resistance) * weights_correction
            self.cells_weights_all[item] = weight
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, round(weight, 4)) # Устанавливаем числовые данные
            _, row = self.find_row_index_wl_bl_table_weight(item[0], item[1])
            self.ui.table_weights.setItem(row, 3, qtable_item)
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def button_load_good_cells_clicked(self): # +
        """
        Загружены ячейки
        """
        filepath = open_file_dialog(self, file_types="CSV Files (*.csv)")
        if filepath:
            try:
                self.cells_coordinates_choosen = []
                wl_max = self.parent.man.col_num
                bl_max = self.parent.man.row_num
                self.cells_coordinates_choosen, _ = choose_cells(filepath, wl_max, bl_max)
            except Exception as er: # pylint: disable=W0718
                self.cells_coordinates_choosen = []
                print('button_load_good_cells_clicked',er)
                show_warning_messagebox('Не возможно загрузить ячейки или их нет!')
            self.update_good_cels()

    def update_good_cels(self): # +
        """
        Обновить статусы годных ячеек
        """
        if self.cells_coordinates_choosen:
            for i, item in enumerate(self.cells_coordinates_all):
                if item in self.cells_coordinates_choosen:
                    _, row = self.find_row_index_wl_bl_table_weight(item[0], item[1])
                    self.ui.table_weights.setItem(row, 4, QTableWidgetItem('выбрана'))
                    # self.ui.table_weights.item(row, 4).setBackground(QtGui.QColor(0,255,0))
                else:
                    _, row = self.find_row_index_wl_bl_table_weight(item[0], item[1])
                    self.ui.table_weights.setItem(row, 4, QTableWidgetItem('не выбрана'))
        else:
            for i, item in enumerate(self.cells_coordinates_all):
                self.ui.table_weights.setItem(i, 4, QTableWidgetItem('не задано'))
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def find_row_index_wl_bl_table_weight(self, wl, bl): # +
        """
        Поиск индекса строки
        """
        status = False
        row = 0
        for row in range(self.ui.table_weights.rowCount()):
            wl_cur = self.table_weights.item(row, 1)
            wl_cur = int(wl_cur.data(Qt.DisplayRole))
            bl_cur = self.table_weights.item(row, 0)
            bl_cur = int(bl_cur.data(Qt.DisplayRole))
            if wl_cur == wl and bl_cur == bl:
                status = True
                break
        return status, row

    def button_drop_cells_clicked(self): # +
        """
        Убрать сопротивления из таблицы
        """
        if self.cells_coordinates_choosen:
            self.cells_coordinates_all = copy.deepcopy(self.cells_coordinates_choosen)
            self.fill_table_weights()
            self.update_good_cels()

    # методы для таблицы с весами

    def button_choose_weights_clicked(self): # +
        """
        Выбрать веса
        """
        self.weights_target_all = []
        filepath = open_file_dialog(self, file_types="Text Files (*.txt)")
        if filepath:
            status_open = False
            with open(filepath, 'r', encoding='utf-8') as file:
                try:
                    self.weights_target_all = file.readlines()
                    status_open = True
                except Exception as ex: # pylint: disable=W0718
                    show_warning_messagebox(f'{ex}')
            if status_open:
                try:
                    self.weights_target_all = list(map(lambda x: float(x.rstrip()), self.weights_target_all))
                    # уникальные абсолютные округленные
                    if self.mode != 'matmul':
                        self.weights_target_all = list(map(float, np.round(np.unique(np.abs(self.weights_target_all)), 4)))
                        if 0. in self.weights_target_all:
                            self.weights_target_all.remove(0.)
                    self.fill_table_match()
                except Exception as ex: # pylint: disable=W0718
                    show_warning_messagebox(f'{ex}')

    def fill_table_match(self): # +
        """
        Функция заполнения таблицы с весами
        """
        # стираем данные
        while self.ui.table_match.rowCount() > 0:
            self.ui.table_match.removeRow(0)
        # заполняем таблицу
        for value in self.weights_target_all:
            # вносим в таблицу
            row_position = self.ui.table_match.rowCount()
            self.ui.table_match.insertRow(row_position)
            # id веса
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, row_position)
            self.ui.table_match.setItem(row_position, 0, qtable_item)
            # Устанавливаем целевой вес
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, value)
            self.ui.table_match.setItem(row_position, 1, qtable_item)
            # Устанавливаем resistanse
            qtable_item = QTableWidgetItem()
            if self.mode == 'matmul':
                qtable_item.setData(0, self.parent.man.sum_gain/value)
            else:
                qtable_item.setData(0, w2r(self.parent.man.res_load, value))
            self.ui.table_match.setItem(row_position, 2, qtable_item)
        self.on_spinbox_correction_weight_changed()

    def find_row_index_weight_id(self, weight_id): # +
        """
        Найти вес по айди
        """
        status = False
        row = 0
        for row in range(self.ui.table_match.rowCount()):
            weight_id_cur = self.table_match.item(row, 0)
            weight_id_cur = int(weight_id_cur.data(Qt.DisplayRole))
            if weight_id_cur == weight_id:
                status = True
                break
        return status, row

    def on_spinbox_correction_weight_changed(self): # +
        """
        Изменение спинбокса коррекции весов
        """
        self.weights_status = {}
        weights_correction = self.ui.spinbox_correction_weight.value()
        res_min = self.ui.spinbox_r_min.value()
        res_max = self.ui.spinbox_r_max.value()
        for i, weight in enumerate(self.weights_target_all):
            _, row = self.find_row_index_weight_id(i)
            if self.mode == 'matmul':
                new_resistance = self.parent.man.sum_gain/(weight/weights_correction)
            else:
                new_resistance = w2r(self.parent.man.res_load, weight/weights_correction)
            # Устанавливаем resistanse
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, new_resistance)
            self.ui.table_match.setItem(row, 2, qtable_item)
            # Проверяем статус
            if res_min <= new_resistance <= res_max:
                self.weights_status[i] = 'подходит'
                self.ui.table_match.setItem(row, 6, QTableWidgetItem('подходит'))
            else:
                self.weights_status[i] = 'не подходит'
                self.ui.table_match.setItem(row, 6, QTableWidgetItem('не подходит'))
        self.update_weights_table_weights()

    def button_drop_weights_clicked(self): # +
        """
        Убрать веса
        """
        if self.weights_status:
            weights_target_all_new = []
            for i, weight in enumerate(self.weights_target_all):
                if self.weights_status[i] == 'подходит':
                    weights_target_all_new.append(weight)
            self.weights_target_all = copy.deepcopy(weights_target_all_new)
            self.fill_table_match()

    def find_close_value(self, target_value): # +
        """
        Найти ближайшее
        """
        min_diff = float('inf')
        closest_key = None
        closest_res = float('inf')
        for row_position in range(self.ui.table_weights.rowCount()):
            key = (self.ui.table_weights.item(row_position, 1).data(Qt.DisplayRole),
                   self.ui.table_weights.item(row_position, 0).data(Qt.DisplayRole))
            if key not in self.target_cells_resistances:
                # вытаскиваем сопротивление
                value = self.ui.table_weights.item(row_position, 2).data(Qt.DisplayRole)
                diff = abs(value - abs(target_value))
                if diff < min_diff:
                    min_diff = diff
                    closest_key = key
                    closest_res = value
        return closest_key, closest_res

    def get_tolerance_ranges(self): # +
        """
        Получить значения допуска
        """
        tolerance = self.ui.spinbox_tolerance.value()
        shutdown_min = self.target_resistances[self.counter] - self.target_resistances[self.counter]*tolerance/100
        shutdown_max = self.target_resistances[self.counter] + self.target_resistances[self.counter]*tolerance/100
        term_values = [r2a(self.parent.man.gain,
                            self.parent.man.res_load,
                            self.parent.man.vol_read,
                            self.parent.man.adc_bit,
                            self.parent.man.vol_ref_adc,
                            self.parent.man.res_switches,
                            shutdown_min),
                        r2a(self.parent.man.gain,
                            self.parent.man.res_load,
                            self.parent.man.vol_read,
                            self.parent.man.adc_bit,
                            self.parent.man.vol_ref_adc,
                            self.parent.man.res_switches,
                            shutdown_max)]
        term_values.sort()
        # print(term_values)
        return copy.deepcopy(term_values)

    def find_row_index_wl_bl_table_match(self, wl, bl): # +
        """
        Поиск индекса строки
        """
        status = False
        row = 0
        for row in range(self.ui.table_match.rowCount()):
            wl_cur = self.table_match.item(row, 5)
            wl_cur = int(wl_cur.data(Qt.DisplayRole))
            bl_cur = self.table_match.item(row, 4)
            bl_cur = int(bl_cur.data(Qt.DisplayRole))
            if wl_cur == wl and bl_cur == bl:
                status = True
                break
        return status, row

    def button_map_weights_clicked(self): # +
        """
        Нажата кнопка записи
        """
        if self.weights_target_all:
            if len(self.cells_coordinates_all) >= len(self.weights_target_all):
                if 'не подходит' not in list(self.weights_status.values()):
                    if self.mode == 'matmul':
                        self.target_cells_resistances = {}
                        row_position = 0
                        for _ in range(self.parent.man.col_num):
                            for _ in range(self.parent.man.row_num):
                                # вытаскиваем сопротивление
                                target_resistance = self.ui.table_match.item(row_position, 2).data(Qt.DisplayRole)
                                current_resistance = self.ui.table_weights.item(row_position, 2).data(Qt.DisplayRole)
                                # вытаскиваем wl, bl
                                wl = self.ui.table_weights.item(row_position, 1).data(Qt.DisplayRole)
                                bl = self.ui.table_weights.item(row_position, 0).data(Qt.DisplayRole)
                                # Устанавливаем wl
                                qtable_item = QTableWidgetItem()
                                qtable_item.setData(0, wl)
                                self.ui.table_match.setItem(row_position, 5, qtable_item)
                                # Устанавливаем bl
                                qtable_item = QTableWidgetItem()
                                qtable_item.setData(0, bl)
                                self.ui.table_match.setItem(row_position, 4, qtable_item)
                                # Устанавливаем resistanse
                                qtable_item = QTableWidgetItem()
                                qtable_item.setData(0, current_resistance)
                                self.ui.table_match.setItem(row_position, 3, qtable_item)
                                self.target_cells_resistances[(wl,bl)] = target_resistance
                                row_position += 1
                    else:
                        # ищем похожие
                        self.target_cells_resistances = {}
                        # цикл по табличке
                        for row_position in range(self.ui.table_match.rowCount()):
                            # вытаскиваем сопротивление
                            target_resistance = self.ui.table_match.item(row_position, 2).data(Qt.DisplayRole)
                            # ищем wl bl ближайшего сопротивления и записываем в эту таблицу
                            closest_key, closest_resistance = self.find_close_value(target_resistance)
                            # Устанавливаем wl
                            qtable_item = QTableWidgetItem()
                            qtable_item.setData(0, closest_key[0])
                            self.ui.table_match.setItem(row_position, 5, qtable_item)
                            # Устанавливаем bl
                            qtable_item = QTableWidgetItem()
                            qtable_item.setData(0, closest_key[1])
                            self.ui.table_match.setItem(row_position, 4, qtable_item)
                            # Устанавливаем resistanse
                            qtable_item = QTableWidgetItem()
                            qtable_item.setData(0, closest_resistance)
                            self.ui.table_match.setItem(row_position, 3, qtable_item)
                            self.target_cells_resistances[closest_key] = target_resistance
                    self.not_writen_cells = list(self.target_cells_resistances.keys())
                    self.not_written_weights = list(map(lambda x: r2w(self.parent.man.res_load, x), list(self.target_cells_resistances.values())))
                    self.written_cells = []
                    self.written_weights = []
                    self.coordinates = list(self.target_cells_resistances.keys()) # apply.py
                    self.target_resistances = list(self.target_cells_resistances.values())
                    self.counter = 0
                    self.application_status = 'work'
                    self.button_work_combination()
                    self.data_for_plot_y = []
                    self.parent.exp_name = 'запись весов'
                    # ticket_name = self.parent.man.ap_config['gui']['program_ticket']
                    # self.ticket = self.parent.read_ticket_from_disk(ticket_name)
                    # # меняем параметры тикета
                    # self.ticket['params']['v_dir_strt_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.RESET_VOL_MIN)
                    # self.ticket['params']['v_dir_stop_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.RESET_VOL_MAX)
                    # self.ticket['params']['v_dir_step_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.RESET_STEP)
                    # self.ticket['params']['v_rev_strt_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.SET_VOL_MIN)
                    # self.ticket['params']['v_rev_stop_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.SET_VOL_MAX)
                    # self.ticket['params']['v_rev_step_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.SET_STEP)
                    # self.ticket['params']['count'] = self.PROG_COUNT
                    self.ticket['terminate']['type'] = "><"
                    self.ticket['terminate']['value'] = self.get_tolerance_ranges()
                    # заполняем список экспериментов
                    task_list, count = calculate_counts_for_ticket(self.parent.man, self.ticket.copy())
                    self.parent.exp_list_params['total_tickets'] += 1
                    self.parent.exp_list_params['total_tasks'] += count
                    self.parent.exp_list = [(self.ticket["name"], self.ticket.copy(), task_list.copy(), count)]
                    # параметры прогресс бара
                    self.ui.progress_bar_mapping.setValue(0)
                    self.ui.progress_bar_mapping.setMaximum(len(self.target_resistances))
                    # параметры потока
                    self.map_thread = ApplyExp(parent=self)
                    self.map_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
                    self.map_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
                    self.map_thread.value_got.connect(self.on_value_got) # при получении каждого измеренного
                    self.map_thread.ticket_finished.connect(self.on_ticket_finished) # при получении каждого измеренного
                    self.map_thread.finished_exp.connect(self.on_finished_exp) # закончился прогон
                    self.map_thread.start()
                else:
                    show_warning_messagebox('Дропните не подходящие веса!')
            else:
                show_warning_messagebox('Весов больше чем ячеек!')
                # todo: двойной клик для удаления
        else:
            show_warning_messagebox('Нечего записать!')

    def on_count_changed(self, value): # +
        '''
        Изменился счетчик
        '''
        # print('on_count_changed')

    def on_progress_finished(self, _):
        """
        Выполнились все тикеты в эксперименте для одной ячейки
        """
        # print(self.counter, self.cells_resistances_all[self.counter], self.ticket['terminate']['value'])
        # чтобы успеть пока поток ApplyExp не начнет работать
        data_for_plot_y = copy.deepcopy(self.data_for_plot_y)
        # очищаем для потока ApplyExp
        self.data_for_plot_y = []
        # в таблицу
        # устанавливаем resistanse в таблицу
        qtable_item = QTableWidgetItem()
        qtable_item.setData(0, data_for_plot_y[-1])
        wl = self.coordinates[self.counter][0]
        bl = self.coordinates[self.counter][1]
        _, row = self.find_row_index_wl_bl_table_match(wl, bl)
        self.ui.table_match.setItem(row, 3, qtable_item)
        # устанавливаем статус в таблицу
        tolerance = self.ui.spinbox_tolerance.value()
        shutdown_min = self.target_resistances[self.counter] - self.target_resistances[self.counter]*tolerance/100
        shutdown_max = self.target_resistances[self.counter] + self.target_resistances[self.counter]*tolerance/100
        if shutdown_min <= data_for_plot_y[-1] <= shutdown_max:
            self.ui.table_match.setItem(row, 6, QTableWidgetItem('записано'))
            self.written_cells.append(self.coordinates[self.counter])
            self.written_weights.append(r2w(self.parent.man.res_load, self.target_resistances[self.counter]))
            self.not_writen_cells.remove(self.coordinates[self.counter])
            self.not_written_weights.remove(r2w(self.parent.man.res_load, self.target_resistances[self.counter]))
        else:
            self.ui.table_match.setItem(row, 6, QTableWidgetItem('не записано'))
        # подменяем значение
        self.counter += 1
        if self.counter < len(self.target_resistances):
            self.ticket['terminate']['value'] = self.get_tolerance_ranges()
            self.parent.exp_list = [(self.ticket["name"], self.ticket.copy(), self.parent.exp_list[0][2].copy(), self.parent.exp_list[0][3])]
        # рисунок для базы в matplotlib
        plt.clf()
        plt.plot(data_for_plot_y, marker='o', linewidth=0.5)
        plt.xlabel(self.xlabel_text)
        plt.ylabel(self.ylabel_text)
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        plt.savefig(self.ticket_image_name, dpi=100)
        plt.close()
        self.map_thread.setup_image_saved(True)
        # прогрессбар
        self.ui.progress_bar_mapping.setValue(self.counter)

    def on_value_got(self, value):
        """
        Получили значение из тикета
        """
        value = value.split(",")
        adc_value = int(value[1])
        self.data_for_plot_y.append(a2r(self.parent.man.gain,
                                        self.parent.man.res_load,
                                        self.parent.man.vol_read,
                                        self.parent.man.adc_bit,
                                        self.parent.man.vol_ref_adc,
                                        self.parent.man.res_switches,
                                        adc_value))

    def on_ticket_finished(self, value):
        '''
        Закончился тикет
        '''
        # print('on_finished_exp')

    def on_finished_exp(self, value):
        """
        Закончился весь эксперимент
        """
        value = value.split(",")
        exp_status = int(value[0])
        flag_soft_cc = int(value[1])
        # блочим запуск
        if exp_status == 1:
            show_warning_messagebox("Эксперимент выполнен!")
        elif exp_status == 2:
            show_warning_messagebox("Эксперимент прерван!")
        elif exp_status == 3:
            show_warning_messagebox('Подозрительно высокое напряжение на АЦП, проверьте подключение!')
        if flag_soft_cc:
            show_warning_messagebox("Срабатывало программное ограничение!")
        self.application_status = 'stop'
        self.button_after_combination()
        self.ui.progress_bar_mapping.setValue(0)

    def button_cancel_map_weights_clicked(self):
        """
        Прервать выполнение эксперимента
        """
        self.map_thread.need_stop = 1

    def set_up_init_values(self):
        """
        Закрытие окна
        """
        self.cells_coordinates_all = []
        self.cells_coordinates_choosen = []
        self.cells_weights_all = {}
        self.cells_resistances_all = {}
        self.weights_target_all = []
        self.weights_status = {}
        self.target_resistances = []
        self.counter = 0
        self.data_for_plot_y = []
        self.application_status = 'stop'
        self.ticket = None
        self.coordinates = []
        self.written_cells = []
        self.not_writen_cells = []
        self.written_weights = []
        self.not_written_weights = []

    def closeEvent(self, event) -> None:
        """
        Закрытие окна
        """
        if self.application_status == 'stop':
            # todo: сделать в parent функцию set_up_init_values()
            self.parent.fill_table()
            self.parent.color_table()
            if self.parent.opener == 'math':
                self.parent.math_dialog.on_weights_written(copy.deepcopy(self.weights_target_all),
                                                           self.ui.spinbox_correction_weight.value())
            self.set_up_init_values()
            event.accept()
        elif self.application_status == 'work':
            show_warning_messagebox('Дождитесь или прервите!')
            event.ignore()

    def button_start_combination(self):
        """
        Комбинация клавиш во время открытия окна
        """
        self.ui.button_load_good_cells.setEnabled(True)
        self.ui.button_map_weights.setEnabled(True)
        self.ui.button_cancel_map_weights.setEnabled(False)
        self.ui.button_download.setEnabled(False)
        self.ui.button_choose_weights.setEnabled(True)
        self.ui.button_drop_cells.setEnabled(True)
        self.ui.button_drop_weights.setEnabled(True)

    def button_ready_combination(self):
        """
        Комбинация клавиш готовых для работы
        """
        self.ui.button_load_good_cells.setEnabled(True)
        self.ui.button_map_weights.setEnabled(True)
        self.ui.button_cancel_map_weights.setEnabled(False)
        self.ui.button_download.setEnabled(False)
        self.ui.button_choose_weights.setEnabled(True)
        self.ui.button_drop_cells.setEnabled(True)
        self.ui.button_drop_weights.setEnabled(True)

    def button_work_combination(self):
        """
        Комбинация клавиш готовых для работы
        """
        self.ui.button_load_good_cells.setEnabled(False)
        self.ui.button_map_weights.setEnabled(False)
        self.ui.button_cancel_map_weights.setEnabled(True)
        self.ui.button_download.setEnabled(False)
        self.ui.button_choose_weights.setEnabled(False)
        self.ui.button_drop_cells.setEnabled(False)
        self.ui.button_drop_weights.setEnabled(False)

    def button_after_combination(self):
        """
        Комбинация клавиш готовых для работы
        """
        self.ui.button_load_good_cells.setEnabled(True)
        self.ui.button_map_weights.setEnabled(True)
        self.ui.button_cancel_map_weights.setEnabled(False)
        self.ui.button_download.setEnabled(True)
        self.ui.button_choose_weights.setEnabled(True)
        self.ui.button_drop_cells.setEnabled(True)
        self.ui.button_drop_weights.setEnabled(True)

    def button_download_clicked(self):
        """
        Выгрузить рабочие
        """
        folder = QFileDialog.getExistingDirectory(self)
        fname = os.path.join(folder, 'written_cells.csv')
        write_csv_data(fname, ['wl', 'bl'], copy.deepcopy(self.written_cells))
        fname = os.path.join(folder, 'not_written_cells.csv')
        write_csv_data(fname, ['wl', 'bl'], copy.deepcopy(self.not_writen_cells))
        # todo: добавить выгрузку записанных и не записанных весов

    def button_update_cells_clicked(self):
        """
        Прочитать все ячейки
        """
        self.parent.read_cell_all('new_ann')
