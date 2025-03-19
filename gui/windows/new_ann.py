"""
Окно для работы с ИНС
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
import copy
# import math
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import uic, QtWidgets
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
    cordinates: list = []
    current_resistances: list = [] # текущие сопротивления ячеек
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
    RESET_VOL_MIN = 0.4
    RESET_VOL_MAX = 1.2
    RESET_STEP = 0.01
    SET_VOL_MIN = 0.4
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
        # обработчики событий
        self.ui.spinbox_weights_scale.valueChanged.connect(self.update_target_values)
        self.ui.combo_mapping_type.currentIndexChanged.connect(self.update_target_values)
        self.ui.spinbox_min_weight.valueChanged.connect(self.update_target_values)
        self.ui.spinbox_max_weight.valueChanged.connect(self.update_target_values)
        self.ui.spinbox_tolerance.valueChanged.connect(self.update_target_values)
        # параметры таблицы
        self.ui.table_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_weights.setColumnCount(7)
        self.ui.table_weights.setHorizontalHeaderLabels(["BL", "WL", "Текущее R", "Текущий W", "Целевой W", "Целевое R", 'Статус'])
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.button_start_combination()

    def button_load_good_cells_clicked(self): #+
        """
        Загружены ячейки
        """
        filepath = open_file_dialog(self, file_types="CSV Files (*.csv)")
        if filepath:
            try:
                self.coordinates_all = []
                # self.weights_levels_count = 0
                wl_max = self.parent.man.col_num
                bl_max = self.parent.man.row_num
                self.coordinates_all, _ = choose_cells(filepath, wl_max, bl_max)
                # self.weights_levels_count = math.floor(math.log2(len(self.coordinates_all)))
                self.button_ready_combination()
            except Exception as er: # pylint: disable=W0718
                self.coordinates_all = []
                # self.weights_levels_count = 0
                print('button_load_good_cells_clicked',er)
                show_warning_messagebox('Не возможно загрузить ячейки или их нет!')
            self.fill_table_cells()

    def fill_table_cells(self):
        """
        Заполнение таблицы весов
        """
        # стираем данные
        self.current_resistances = []
        while self.ui.table_weights.rowCount() > 0:
            self.ui.table_weights.removeRow(0)
        for item in self.coordinates_all:
            # получаем из базы данные
            _, memristor_id = self.parent.man.db.get_memristor_id(item[0], item[1], self.parent.man.crossbar_id)
            _, resistance = self.parent.man.db.get_last_resistance(memristor_id)
            self.current_resistances.append(resistance)
            # вносим в таблицу
            row_position = self.ui.table_weights.rowCount()
            self.ui.table_weights.insertRow(row_position)
            self.ui.table_weights.setItem(row_position, 0, QTableWidgetItem(str(item[1])))
            self.ui.table_weights.setItem(row_position, 1, QTableWidgetItem(str(item[0])))
            self.ui.table_weights.setItem(row_position, 2, QTableWidgetItem(str(resistance)))
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.update_target_values()

    def update_table_resistances(self):
        """
        Обновление сопротивлений после записи
        """
        # стираем данные
        self.current_resistances = []
        for i, item in enumerate(self.coordinates_all):
            # получаем из базы данные
            _, memristor_id = self.parent.man.db.get_memristor_id(item[0], item[1], self.parent.man.crossbar_id)
            _, resistance = self.parent.man.db.get_last_resistance(memristor_id)
            self.current_resistances.append(resistance)
            # вносим в таблицу
            self.ui.table_weights.setItem(i, 2, QTableWidgetItem(str(resistance)))
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.update_target_values()

    def update_target_values(self):
        """
        Обновить целевые показатели
        """
        tolerance = self.ui.spinbox_tolerance.value()
        for i, item in enumerate(self.current_resistances):
            weight = r2w(self.parent.man.res_load, item)*self.ui.spinbox_weights_scale.value()
            self.ui.table_weights.setItem(i, 3, QTableWidgetItem(str(round(weight, 4))))
        self.ui.table_weights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

    def get_tolerance_ranges(self):
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
        if self.not_writen_cells:
            self.coordinates = copy.deepcopy(self.not_writen_cells)
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
            self.ui.progress_bar_mapping.setMaximum(len(self.coordinates_all))
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
        # подменяем значение
        self.counter += 1
        if self.counter < len(self.coordinates_all):
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
        self.update_table_resistances()

    def button_cancel_map_weights_clicked(self):
        """
        Прервать выполнение эксперимента
        """
        self.map_thread.need_stop = 1

    def set_up_init_values(self):
        """
        Закрытие окна
        """
        self.current_resistances = []
        self.coordinates_all = []
        self.application_status = 'stop'
        self.counter = 0
        self.data_for_plot_y = []
        self.target_resistances = []
        self.writen_cells = []
        self.not_writen_cells = []
        self.cordinates = []
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
        self.ui.button_map_weights.setEnabled(False)
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
        self.ui.button_map_weights.setEnabled(False)
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
