"""
Окно для работы с ИНС
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
import copy
# import math
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5 import uic, QtWidgets, QtGui
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHeaderView, QFileDialog

from manager.service import r2a, a2v, r2w, w2r, d2v, a2r, v2d
from manager.service.plots import calculate_counts_for_ticket
from gui.src import show_warning_messagebox, choose_cells, open_file_dialog, write_csv_data
from gui.windows.apply import ApplyExp

class NewAnn(QDialog):
    """
    Окно для работы с ИНС
    """

    GUI_PATH = os.path.join("gui","uies","new_ann.ui")
    # weights_levels_count: int = 0 # количество уровней веса
    coordinates_all: list = [] # координаты ячеек
    coordinates_good: list = []
    weights_all = {} # все веса
    weight_max: int
    weight_min: int
    current_resistances: dict = {} # текущие сопротивления ячеек
    weights_target_raw: list = [] # веса целевые списком
    weights_target: dict = {} # словарь с весами целевыми
    
    target_resistances: list = []
    writen_cells: list = []
    not_writen_cells: list = []
    map_thread: ApplyExp
    counter: int # счетчик для прогрессбара
    data_for_plot_y: list
    xlabel_text: str = 'Отсчеты'
    ylabel_text: str = 'Сопротивление, Ом'
    ticket_image_name: str = "temp.png"
    application_status: str = 'stop'
    ticket = None

    # todo: сделать выбор по кнопке
    PROG_COUNT = 3
    RESET_VOL_MIN = 0.3
    RESET_VOL_MAX = 1.2
    RESET_STEP = 0.01
    SET_VOL_MIN = 0.3
    SET_VOL_MAX = 1.2
    SET_STEP = 0.01

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # нажатия кнопок
        self.ui.button_load_good_cells.clicked.connect(self.button_load_good_cells_clicked)
        self.ui.button_map_weights.clicked.connect(self.button_map_weights_clicked)
        self.ui.button_cancel_map_weights.clicked.connect(self.button_cancel_map_weights_clicked)
        self.ui.button_download.clicked.connect(self.button_download_clicked)
        self.ui.button_choose_weights.clicked.connect(self.button_choose_weights_clicked)

        self.ui.button_drop_cells.clicked.connect(self.button_drop_cells_clicked)
        self.ui.button_drop_weights.clicked.connect(self.button_drop_weights_clicked)
        # обработчики событий
        # self.ui.spinbox_weights_scale.valueChanged.connect(self.update_target_values)
        # self.ui.combo_mapping_type.currentIndexChanged.connect(self.update_target_values)
        # self.ui.spinbox_min_weight.valueChanged.connect(self.update_target_values)
        # self.ui.spinbox_max_weight.valueChanged.connect(self.update_target_values)
        # self.ui.spinbox_tolerance.valueChanged.connect(self.update_target_values)
        self.ui.spinbox_correction_weight.valueChanged.connect(self.on_spinbox_correction_weight_changed)
        self.ui.spinbox_r_min.valueChanged.connect(self.on_spinbox_correction_weight_changed)
        self.ui.spinbox_r_max.valueChanged.connect(self.on_spinbox_correction_weight_changed)
        # параметры таблицы table_weights
        self.ui.table_weights.setSortingEnabled(True) # Включаем сортировку
        self.ui.table_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_weights.setColumnCount(5)
        self.ui.table_weights.setHorizontalHeaderLabels(["BL", "WL", "Текущее R", "Текущий W", "Выбор"])
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # параметры таблицы table_match
        self.ui.table_match.setSortingEnabled(True) # Включаем сортировку
        self.ui.table_match.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_match.setColumnCount(7)
        self.ui.table_match.setHorizontalHeaderLabels(["id", "Целевой W", "Целевое R", "Ближайший R", "BL", "WL", "Статус"])
        self.ui.table_match.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # комбинация кнопок
        self.button_start_combination()
        # заполняем таблицу
        for bl in range(self.parent.man.row_num):
            for wl in range(self.parent.man.col_num):
                self.coordinates_all.append((wl, bl))
        self.fill_table_weights()
        self.update_good_cels()

    # методы для таблицы с сопротивлениями

    def fill_table_weights(self): # +
        """
        Заполнение таблицы весов
        """
        # стираем данные
        self.current_resistances = {}
        while self.ui.table_weights.rowCount() > 0:
            self.ui.table_weights.removeRow(0)
        for item in self.coordinates_all:
            # получаем из базы данные
            _, memristor_id = self.parent.man.db.get_memristor_id(item[0], item[1], self.parent.man.crossbar_id)
            _, resistance = self.parent.man.db.get_last_resistance(memristor_id)
            self.current_resistances[item] = resistance
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
        self.update_current_weights()

    def update_current_weights(self): # +
        """
        Обновить текущие веса
        """
        self.weights_all = {}
        for i, item in enumerate(self.coordinates_all):
            resistance = self.current_resistances[item]
            weight = r2w(self.parent.man.res_load, resistance)*self.ui.spinbox_correction_weight.value()
            self.weights_all[item] = weight
            qtable_item = QTableWidgetItem()
            qtable_item.setData(0, round(weight, 4)) # Устанавливаем числовые данные
            status, row = self.find_row_index_wl_bl(item[0], item[1])
            self.ui.table_weights.setItem(row, 3, qtable_item)
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.weight_max = max(self.weights_all.items())[1]
        self.weight_min = min(self.weights_all.items())[1]
        print(self.weight_min, self.weight_max)

    def button_load_good_cells_clicked(self): # +
        """
        Загружены ячейки
        """
        filepath = open_file_dialog(self, file_types="CSV Files (*.csv)")
        if filepath:
            try:
                self.coordinates_good = []
                # self.weights_levels_count = 0
                wl_max = self.parent.man.col_num
                bl_max = self.parent.man.row_num
                self.coordinates_good, _ = choose_cells(filepath, wl_max, bl_max)
                # self.weights_levels_count = math.floor(math.log2(len(self.coordinates_all)))
                # self.button_ready_combination()
            except Exception as er: # pylint: disable=W0718
                self.coordinates_good = []
                # self.weights_levels_count = 0
                print('button_load_good_cells_clicked',er)
                show_warning_messagebox('Не возможно загрузить ячейки или их нет!')
            self.update_good_cels()

    def update_good_cels(self): # +
        """
        Обновить статусы годных ячеек
        """
        if self.coordinates_good:
            for i, item in enumerate(self.coordinates_all):
                if item in self.coordinates_good:
                    status, row = self.find_row_index_wl_bl(item[0], item[1])
                    self.ui.table_weights.setItem(row, 4, QTableWidgetItem('выбрана'))
                    # self.ui.table_weights.item(row, 4).setBackground(QtGui.QColor(0,255,0))
                else:
                    status, row = self.find_row_index_wl_bl(item[0], item[1])
                    self.ui.table_weights.setItem(row, 4, QTableWidgetItem('не выбрана'))
        else:
            for i, item in enumerate(self.coordinates_all):
                self.ui.table_weights.setItem(i, 4, QTableWidgetItem('не задано'))
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def find_row_index_wl_bl(self, wl, bl): # +
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

    def button_drop_cells_clicked(self):
        """
        Убрать сопротивления
        """
        if self.coordinates_good:
            # todo: не удаляет эти веса из weights_target_raw
            for i, item in enumerate(self.coordinates_all):
                if item not in self.coordinates_good:
                    status, row = self.find_row_index_wl_bl(item[0], item[1])
                    self.ui.table_weights.removeRow(row)

    # методы для таблицы с весами

    def button_choose_weights_clicked(self):
        """
        Выбрать веса
        """
        self.weights_target_raw = [0.01, 0.1, 0.5, 0.7]

        # уникальные
        # округленные
        # проверить общее количество

        self.fill_table_match()

    def fill_table_match(self): # +
        """
        Функция заполнения таблицы с весами
        """
        # self.weights_target_raw_dict = {}
        # стираем данные
        while self.ui.table_match.rowCount() > 0:
            self.ui.table_match.removeRow(0)
        # for key, value in self.weights_target.items():
        for value in self.weights_target_raw:
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
            # self.weights_target_raw_dict[row_position] = value
            # Устанавливаем resistanse
            qtable_item = QTableWidgetItem()
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

    def on_spinbox_correction_weight_changed(self):
        """
        Изменение спинбокса коррекции весов
        """
        self.weights_status = {}
        weights_correction = self.ui.spinbox_correction_weight.value()
        res_min = self.ui.spinbox_r_min.value()
        res_max = self.ui.spinbox_r_max.value()
        for i, value in enumerate(self.weights_target_raw):
            status, row = self.find_row_index_weight_id(i)
            new_resistance = w2r(self.parent.man.res_load, value/weights_correction)
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

    def button_drop_weights_clicked(self):
        """
        Убрать веса
        """
        # todo: не удаляет эти веса из weights_target_raw
        for i, value in enumerate(self.weights_target_raw):
            status, row = self.find_row_index_weight_id(i)
            if self.weights_status[i] == 'не подходит':
                self.ui.table_match.removeRow(row)

    def find_close_value(self, target_value):
        """
        Найти ближайшее
        """
        min_diff = float('inf')
        closest_key = None
        closest_res = float('inf')
        for row_position in range(self.ui.table_weights.rowCount()):
            key = (self.ui.table_weights.item(row_position, 1).data(Qt.DisplayRole),
                   self.ui.table_weights.item(row_position, 0).data(Qt.DisplayRole))
            if key not in self.weights_target:
                # вытаскиваем сопротивление
                value = self.ui.table_weights.item(row_position, 2).data(Qt.DisplayRole)
                diff = abs(value - abs(target_value))
                if diff < min_diff:
                    min_diff = diff
                    closest_key = key
                    closest_res = value
        return closest_key, closest_res

    def update_table_resistances(self):
        """
        Обновление сопротивлений после записи
        """
        # стираем данные
        self.current_resistances = {}
        for i, item in enumerate(self.coordinates_all):
            # получаем из базы данные
            _, memristor_id = self.parent.man.db.get_memristor_id(item[0], item[1], self.parent.man.crossbar_id)
            _, resistance = self.parent.man.db.get_last_resistance(memristor_id)
            self.current_resistances[item] = resistance
            # вносим в таблицу
            self.ui.table_weights.setItem(i, 2, QTableWidgetItem(str(resistance)))
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.update_target_values()

    def update_target_values(self):
        """
        Обновить целевые показатели
        """
        tolerance = self.ui.spinbox_tolerance.value()
        all_levels_weights = len(self.coordinates_all)
        min_weight = self.ui.spinbox_min_weight.value()
        max_weight = self.ui.spinbox_max_weight.value()
        weight_type = self.ui.combo_mapping_type.currentText()
        weights = []
        if weight_type == "линейная":
            weights = np.linspace(min_weight, max_weight, all_levels_weights)
        elif weight_type == "квадратичная":
            square = lambda x: x ** 2
            weights = np.linspace(min_weight, max_weight, all_levels_weights)
            weights = square(weights)
        self.target_resistances = []
        self.writen_cells = []
        self.not_writen_cells = []
        for i, item in enumerate(weights):
            self.ui.table_weights.setItem(i, 4, QTableWidgetItem(str(round(item, 4))))
            target_resistance = w2r(self.parent.man.res_load, item/self.ui.spinbox_weights_scale.value())
            self.target_resistances.append(target_resistance)
            self.ui.table_weights.setItem(i, 5, QTableWidgetItem(str(round(target_resistance, 1))))
            if self.target_resistances[i] - self.target_resistances[i]*tolerance/100 <= self.current_resistances[i] <= self.target_resistances[i] + self.target_resistances[i]*tolerance/100:
                self.ui.table_weights.setItem(i, 6, QTableWidgetItem('Записано'))
                self.writen_cells.append(self.coordinates_all[i])
            else:
                self.ui.table_weights.setItem(i, 6, QTableWidgetItem('Не записано'))
                self.not_writen_cells.append(self.coordinates_all[i])
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # todo: добавить выгрузку записанных весов

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

    def button_map_weights_clicked(self):
        """
        Нажата кнопка записи
        """
        # ищем похожие
        self.weights_target = {}
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
            self.weights_target[closest_key] = target_resistance
        print(self.weights_target)
        self.coordinates = list(self.weights_target.keys()) # apply.py
        print(self.coordinates)
        self.target_resistances = list(self.weights_target.values())
        print(self.target_resistances)
        self.counter = 0
        self.application_status = 'work'
        self.button_work_combination()
        self.data_for_plot_y = []
        self.parent.exp_name = 'запись весов'
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

    def on_count_changed(self, value):
        '''
        Изменился счетчик
        '''
        # print('on_count_changed')
        pass

    def on_progress_finished(self, value):
        """
        Выполнились все тикеты в эксперименте для одной ячейки
        """
        # print(self.counter, self.current_resistances[self.counter], self.ticket['terminate']['value'])
        # чтобы успеть пока поток ApplyExp не начнет работать
        data_for_plot_y = copy.deepcopy(self.data_for_plot_y)
        # очищаем для потока ApplyExp
        self.data_for_plot_y = []
        # в таблицу 
        # Устанавливаем resistanse
        qtable_item = QTableWidgetItem()
        qtable_item.setData(0, data_for_plot_y[-1])
        self.ui.table_match.setItem(self.counter, 3, qtable_item)
        # todo: ставить статус запуска
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
        pass

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
        self.button_ready_combination()
        # self.update_table_resistances()

    def button_cancel_map_weights_clicked(self):
        """
        Прервать выполнение эксперимента
        """
        self.map_thread.need_stop = 1

    def set_up_init_values(self):
        """
        Закрытие окна
        """
        self.current_resistances = {}
        self.coordinates_all = []
        self.coordinates_good = []
        self.weight_min = None
        self.weight_max = None
        self.weights_all = {}
        self.application_status = 'stop'
        self.counter = 0
        self.data_for_plot_y = []
        self.target_resistances = []
        self.writen_cells = []
        self.not_writen_cells = []
        self.ticket = None

    def closeEvent(self, event) -> None:
        """
        Закрытие окна
        """
        if self.application_status == 'stop':
            # todo: сделать в parent функцию set_up_init_values()
            self.parent.fill_table()
            self.parent.color_table()
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

    def button_ready_combination(self):
        """
        Комбинация клавиш готовых для работы
        """
        self.ui.button_load_good_cells.setEnabled(True)
        self.ui.button_map_weights.setEnabled(True)
        self.ui.button_cancel_map_weights.setEnabled(False)

    def button_work_combination(self):
        """
        Комбинация клавиш готовых для работы
        """
        self.ui.button_load_good_cells.setEnabled(False)
        self.ui.button_map_weights.setEnabled(True)
        self.ui.button_cancel_map_weights.setEnabled(True)

    def button_download_clicked(self):
        """
        Выгрузить рабочие
        """
        folder = QFileDialog.getExistingDirectory(self)
        fname = os.path.join(folder, 'written_cells.csv')
        write_csv_data(fname, ['wl', 'bl'], copy.deepcopy(self.writen_cells))
        fname = os.path.join(folder, 'not_written_cells.csv')
        write_csv_data(fname, ['wl', 'bl'], copy.deepcopy(self.not_writen_cells))
        # todo: добавить выгрузку сводную
