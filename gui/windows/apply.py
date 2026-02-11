"""
Окно выполнения эксперимента
https://stackforgeeks.com/blog/what-is-the-easiest-way-to-achieve-realtime-plotting-in-pyqtgraph
https://ru.stackoverflow.com/questions/1091615/%D0%9A%D0%B0%D0%BA-%D0%B2%D1%81%D1%82%D1%80%D0%BE%D0%B8%D1%82%D1%8C-%D0%B3%D1%80%D0%B0%D1%84%D0%B8%D0%BA-%D0%B2-%D1%84%D0%BE%D1%80%D0%BC%D1%83-%D0%B2-qt-designer
https://ru.stackoverflow.com/questions/1003750/%D0%9A%D0%B0%D0%BA-%D0%BF%D0%B5%D1%80%D0%B5%D0%B4%D0%B0%D1%82%D1%8C-%D1%87%D0%B5%D1%80%D0%B5%D0%B7-%D1%81%D0%B8%D0%B3%D0%BD%D0%B0%D0%BB-%D0%B2-%D0%BF%D0%BE%D1%82%D0%BE%D0%BA-pyqt5
"""

# pylint: disable=W0611,E0611,R0902,C0301,C0103

from __future__ import annotations

import os
import time
import pickle
import pyqtgraph as pg
# import plotly.express as px
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, QMutex

from manager.service import d2v, a2r, a2c, r2a, a2v
from manager.service.saves import save_list_to_bytearray, init_csv_apply
import csv
from gui.src import show_choose_window, show_warning_messagebox

class Apply(QWidget):
    """
    Окно выполнения эксперимента
    """

    GUI_PATH = os.path.join("gui","uies","apply.ui")
    start_thread: ApplyExp # поток выполнения
    graph_result: pg.PlotWidget # осциллограмма
    application_status: str # статус выполнения (старт, стоп, пауза)
    total_impacts: int # счетчик тасков
    # списки данных и терминаторов
    _term_left_for_plot_y: list
    _term_left_for_plot_x: list
    _term_right_for_plot_y: list
    _term_right_for_plot_x: list
    data_for_plot_y: list
    data_for_plot_x: list
    coordinates: list
    ticket_image_name: str = "temp.png"
    lang_pack: dict

    def __init__(self, parent=None) -> None:
        """
        Инициализация
        """
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.ui.change_language()
        # доп настройки
        self.ui.setWindowFlags(Qt.Window)
        # область графика
        self.graph_result = pg.PlotWidget()
        self.graph_result.setBackground('w')
        layout = QVBoxLayout()
        layout.addWidget(self.graph_result)
        self.ui.widgetplot.setLayout(layout)
        # выбор осей
        self.ui.xaxes_combobox.activated.connect(self.init_plot)
        self.ui.yaxes_combobox.activated.connect(self.init_plot)
        self.ui.plot_type_combobox.activated.connect(self.init_plot)
        self.ui.plot_type_combobox.setCurrentText('звездочки') # звездочки
        self.ui.graph_checkbox.clicked.connect(self.need_plot)
        self.ui.graph_checkbox.setCheckState(2) # отобразить график
        self.need_plot() # нужно рисовать график
        self.init_plot() # начальный график
        # обработчики кнопок
        self.ui.button_start.clicked.connect(self.start_exp)
        self.ui.button_pause.clicked.connect(self.pause_exp)
        self.ui.button_stop.clicked.connect(self.stop_exp)
        self.ui.button_graph_settings.clicked.connect(self.plot_settings)
        self.block_buttons([False, False, True, True])
        # обнулить прогрессбар
        self.ui.exp_progress.setValue(0)
        # обновить значение лейбла "Остаток задач"
        self.total_impacts = self.parent.exp_list_params['total_tasks'] # декрементируем
        self.update_label_total_count()
        # флаг состояния
        self.application_status = "stop"
        # обновить значение лейбла информации о мемристоре
        self.update_label_mem_id()

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("apply")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.groupBox_2.setTitle(self.lang_pack.get("visual"))
            self.ui.label_2.setText(self.lang_pack.get("axisx"))
            self.ui.label_3.setText(self.lang_pack.get("axisy"))
            self.ui.xaxes_combobox.setItemText(0, self.lang_pack.get("counting"))
            self.ui.xaxes_combobox.setItemText(1, self.lang_pack.get("voltage"))
            self.ui.yaxes_combobox.setItemText(0, self.lang_pack.get("res_k"))
            self.ui.yaxes_combobox.setItemText(1, self.lang_pack.get("res"))
            self.ui.yaxes_combobox.setItemText(2, self.lang_pack.get("adc_c"))
            self.ui.yaxes_combobox.setItemText(3, self.lang_pack.get("amp_m"))
            self.ui.yaxes_combobox.setItemText(4, self.lang_pack.get("amp_mc"))
            self.ui.graph_checkbox.setText(self.lang_pack.get("view"))
            self.ui.plot_type_combobox.setItemText(0, self.lang_pack.get("line"))
            self.ui.plot_type_combobox.setItemText(1, self.lang_pack.get("dot"))
            self.ui.plot_type_combobox.setItemText(2, self.lang_pack.get("star"))
            self.ui.button_graph_settings.setText(self.lang_pack.get("settings"))
            self.ui.groupBox.setTitle(self.lang_pack.get("exec_main"))
            self.ui.button_start.setText(self.lang_pack.get("start"))
            self.ui.button_stop.setText(self.lang_pack.get("stop"))
            self.ui.button_pause.setText(self.lang_pack.get("pause"))

    def need_plot(self) -> None:
        """
        Поднять флаг рисования
        """
        if self.ui.graph_checkbox.isChecked():
            self._plot_flag = True
        else:
            self._plot_flag = False

    def init_plot(self) -> None:
        """
        Инициализация графика
        """
        self.graph_result.clear()
        # массивы данных для отображения результатов
        self.data_for_plot_y = []
        self.data_for_plot_x = []
        # массивы данных для отображения терминаторов
        self._term_left_for_plot_y = []
        self._term_left_for_plot_x = []
        self._term_right_for_plot_y = []
        self._term_right_for_plot_x = []
        # остальные параметры
        self.xlabel_text = self.ui.xaxes_combobox.currentText()
        self.ylabel_text = self.ui.yaxes_combobox.currentText()
        self.graph_result.getPlotItem().setLabel('left', self.ylabel_text)
        self.graph_result.getPlotItem().setLabel('bottom', self.xlabel_text)
        self.graph_result.showGrid(x=True, y=True)
        plt_type = self.ui.plot_type_combobox.currentText()
        if plt_type == self.lang_pack.get("line"):
            self.data_line = self.graph_result.plot(self.data_for_plot_x,
                                                    self.data_for_plot_y,
                                                    pen=pg.mkPen(width=3, color = (0, 128, 255)))
        elif plt_type == self.lang_pack.get("dot"):
            self.data_line = self.graph_result.plot(self.data_for_plot_x,
                                                    self.data_for_plot_y,
                                                    symbol='o')
        elif plt_type == self.lang_pack.get("star"):
            self.data_line = self.graph_result.plot(self.data_for_plot_x,
                                                    self.data_for_plot_y,
                                                    symbol='star')

        self.termline_left = self.graph_result.plot(self._term_left_for_plot_x,
                                                    self._term_left_for_plot_y,
                                                    pen=pg.mkPen(width=3, color = (255, 0, 0)))
        self.termline_right = self.graph_result.plot(self._term_right_for_plot_x,
                                                     self._term_right_for_plot_y,
                                                     pen=pg.mkPen(width=3, color = (255, 0, 0)))
        # задание функции для отрисовки осей
        if self.ylabel_text == self.lang_pack.get("res_k"):
            self.y_value_process = lambda y,vol,sign: a2r(self.parent.man.gain,
                                                          self.parent.man.res_load,
                                                          self.parent.man.vol_read,
                                                          self.parent.man.adc_bit,
                                                          self.parent.man.vol_ref_adc,
                                                          self.parent.man.res_switches,
                                                          y)/1000
        elif self.ylabel_text == self.lang_pack.get("res"):
            self.y_value_process = lambda y,vol,sign: a2r(self.parent.man.gain,
                                                          self.parent.man.res_load,
                                                          self.parent.man.vol_read,
                                                          self.parent.man.adc_bit,
                                                          self.parent.man.vol_ref_adc,
                                                          self.parent.man.res_switches,
                                                          y)
        elif self.ylabel_text == self.lang_pack.get("adc_c"):
            self.y_value_process = lambda y,vol,sign: y
        elif self.ylabel_text == self.lang_pack.get("amp_mc"):
            self.y_value_process = lambda y,vol,sign: a2c(self.parent.man.dac_bit,
                                                          self.parent.man.vol_ref_dac,
                                                          self.parent.man.gain,
                                                          self.parent.man.res_load,
                                                          self.parent.man.vol_read,
                                                          self.parent.man.adc_bit,
                                                          self.parent.man.vol_ref_adc,
                                                          self.parent.man.res_switches,
                                                          y,
                                                          vol,
                                                          sign)*1e6
        elif self.ylabel_text == self.lang_pack.get("amp_m"):
            self.y_value_process = lambda y,vol,sign: a2c(self.parent.man.dac_bit,
                                                          self.parent.man.vol_ref_dac,
                                                          self.parent.man.gain,
                                                          self.parent.man.res_load,
                                                          self.parent.man.vol_read,
                                                          self.parent.man.adc_bit,
                                                          self.parent.man.vol_ref_adc,
                                                          self.parent.man.res_switches,
                                                          y,
                                                          vol,
                                                          sign)*1e3
        if self.xlabel_text == self.lang_pack.get("voltage"):
            self.x_value_process = lambda vol,sign,count: d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,vol,sign=sign)
        elif self.xlabel_text == self.lang_pack.get("counting"):
            self.x_value_process = lambda vol,sign,count: count
        self.update_label_mem_id()

    def start_exp(self) -> None:
        """
        Начать эксперимент
        когда остановилось то можем еще раз запустить сначала
        """
        if self.application_status == "stop": # не работает
            self.application_status = "start" # запускаем
            self.start_start_thread()
        elif self.application_status == "pause":
            self.application_status = "start"
            self.start_thread.need_pause = False
        self.block_buttons([True, True, False, False]) # пауза остановить
        self.block_comdo(True)

    def pause_exp(self) -> None:
        """
        Поставить эксперимент на паузу
        """
        if self.application_status == "start": # работает
            self.application_status = "pause"
            self.start_thread.need_pause = True
            self.block_buttons([False, True, True, False]) # запустить остановить

    def stop_exp(self) -> None:
        """
        Остановить эксперимент
        """
        if self.application_status == "start" or "pause": # работает
            self.start_thread.need_stop = True
            self.application_status = "stop"
        self.block_buttons([False, False, True, True])
        self.block_comdo(False)
        self.total_impacts = self.parent.exp_list_params['total_tasks']
        self.update_label_total_count()

    def plot_settings(self) -> None:
        """
        Окно настройки графика
        """
        show_warning_messagebox(self.lang_pack.get("not_done"), self.parent.read_language_json)

    def update_label_total_count(self) -> None:
        """
        Обновление лейбла
        """
        self.ui.label_total_count.setText(f"{self.lang_pack.get('tasks_left')}{self.total_impacts}")

    def update_label_mem_id(self) -> None:
        """
        Обновление лейбла
        """
        mem_id = self.parent.man.db.get_memristor_id(self.parent.current_wl, self.parent.current_bl, self.parent.man.crossbar_id)
        self.ui.label_mem_id.setText(f"{self.lang_pack.get('mem_id')} wl={self.parent.current_wl}, bl={self.parent.current_bl}, id={mem_id[1]}")

    def block_comdo(self, block_type: bool) -> None:
        """
        Функция длокировки виджетов на время выполнения
        """
        self.ui.xaxes_combobox.setDisabled(block_type)
        self.ui.yaxes_combobox.setDisabled(block_type)
        self.ui.plot_type_combobox.setDisabled(block_type)

    def block_buttons(self, flags: list) -> None:
        """
        Блокировка кнопок
        """
        self.ui.button_start.setDisabled(flags[0])
        self.ui.button_graph_settings.setDisabled(flags[1])
        self.ui.button_pause.setDisabled(True)
        self.ui.button_stop.setDisabled(flags[3])

    def closeEvent(self, event):
        """
        Закрытие
        """
        if self.application_status in ["start", "pause"]: # работает
            answer = show_choose_window(self, self.lang_pack.get("stop_exp"), rlj=self.parent.read_language_json)
            if answer:
                self.stop_exp()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def start_start_thread(self) -> None:
        """
        Запуск потока обработки
        """
        self.init_plot()
        # параметры прогресс бара
        self.ui.exp_progress.setValue(0)
        self.ui.exp_progress.setMaximum(self.total_impacts)
        # ячейка для эксперимента
        self.coordinates = [(self.parent.current_wl, self.parent.current_bl)]
        # параметры потока
        # mt = QMutex()
        self.start_thread = ApplyExp(parent=self)
        # self.start_thread._mutex = mt
        self.start_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
        self.start_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
        self.start_thread.value_got.connect(self.on_value_got) # при получении каждого измеренного
        self.start_thread.ticket_finished.connect(self.on_ticket_finished) # при получении каждого измеренного
        self.start_thread.finished_exp.connect(self.on_finished_exp) # закончился прогон
        self.start_thread.start()

    def on_finished_exp(self, value: int) -> None:
        """
        Завершили эксперимент
        """
        value = value.split(",")
        exp_status = int(value[0])
        flag_soft_cc = int(value[1])
        # блочим запуск
        if exp_status == 1:
            show_warning_messagebox(self.lang_pack.get("done"), rlj=self.parent.read_language_json)
        elif exp_status == 2:
            show_warning_messagebox(self.lang_pack.get("stopped"), rlj=self.parent.read_language_json)
        elif exp_status == 3:
            show_warning_messagebox(self.lang_pack.get("voltage_high"), rlj=self.parent.read_language_json)
        if flag_soft_cc:
            show_warning_messagebox(self.lang_pack.get("prog_stop"), rlj=self.parent.read_language_json)
        self.application_status = "stop"
        self.stop_exp()

    def on_ticket_finished(self, value: str) -> None:
        """
        Завершили тикет
        """
        # стираем терминаторы
        self._term_left_for_plot_y = []
        self._term_left_for_plot_x = []
        self._term_right_for_plot_y = []
        self._term_right_for_plot_x = []
        self.termline_left.setData(self._term_left_for_plot_x, self._term_left_for_plot_y)
        self.termline_right.setData(self._term_right_for_plot_x, self._term_right_for_plot_y)

    def on_count_changed(self, value: int) -> None:
        """
        Завершили таск
        Изменение счетчика вызывает обновление прогрессбара
        """
        self.total_impacts -= 1
        self.update_label_total_count()
        self.ui.exp_progress.setValue(value)

    def on_progress_finished(self, value: str) -> None:
        """
        Завершение выполнения
        """
        value = value.split(",")
        exp_status = int(value[1])
        flag_soft_cc = int(value[2])
        # рисунок для базы в matplotlib
        plt.clf()
        plt.plot(self.data_for_plot_x, self.data_for_plot_y, marker='o', linewidth=0.5)
        plt.xlabel(self.xlabel_text)
        plt.ylabel(self.ylabel_text)
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        plt.savefig(self.ticket_image_name, dpi=100)
        plt.close()
        self.start_thread.setup_image_saved(True)
        # рисунок для базы в plotly (решили отказаться из-за большого размера библиотеки)
        # fig = px.scatter(x=self.data_for_plot_x, y=self.data_for_plot_y)
        # fig.update_layout(xaxis_title=self.xlabel_text,
        #                     yaxis_title=self.ylabel_text)
        # fig.write_image(self.ticket_image_name, width=640, height=480)

    def on_value_got(self, value: str) -> None:
        """
        Возможно это повторяет on_count_changed
        Получили значение сопротивления
        """
        # полученное значение отобразить
        value = value.split(",")
        count = int(value[0])
        vol = int(value[2])
        sign = int(value[3])
        term_left = int(value[4])
        term_right = int(value[5])
        value = int(value[1])
        # отображение
        #if self.application_status == "start" and self._plot_flag:
        if self._plot_flag:
            # выбор отображения по осям
            y_item = self.y_value_process(value, vol, sign)
            x_item = self.x_value_process(vol=vol, sign=sign, count=count)
            size = 3000 # todo: глубина отрисовки, вынести в константы
            data_len = len(self.data_for_plot_y)
            if data_len > size:
                self.data_for_plot_y = self.data_for_plot_y[1:] + [y_item]
                self.data_for_plot_x = self.data_for_plot_x[1:] + [x_item]
            else:
                self.data_for_plot_y.append(y_item)
                self.data_for_plot_x.append(x_item)
            self.data_line.setData(self.data_for_plot_x, self.data_for_plot_y)
            # отображение терминаторов
            if term_left:
                # левый
                term_left = self.y_value_process(term_left, vol, sign)
                if data_len > size:
                    self._term_left_for_plot_y = self._term_left_for_plot_y[1:] + [term_left]
                    self._term_left_for_plot_x = self._term_left_for_plot_x[1:] + [x_item]
                else:
                    self._term_left_for_plot_y.append(term_left)
                    self._term_left_for_plot_x.append(x_item)
                self.termline_left.setData(self._term_left_for_plot_x, self._term_left_for_plot_y)
            if term_right:
                # правый
                term_right = self.y_value_process(term_right, vol, sign)
                if data_len > size:
                    self._term_right_for_plot_y = self._term_right_for_plot_y[1:] + [term_right]
                    self._term_right_for_plot_x = self._term_right_for_plot_x[1:] + [x_item]
                else:
                    self._term_right_for_plot_y.append(term_right)
                    self._term_right_for_plot_x.append(x_item)
                self.termline_right.setData(self._term_right_for_plot_x, self._term_right_for_plot_y)

class ApplyExp(QThread):
    """
    Поток эксперимента
    """

    count_changed = pyqtSignal(int) # для каждой task
    progress_finished = pyqtSignal(str) # для каждого мемристора из self.coordinates
    ticket_finished = pyqtSignal(str) # для каждого ticket
    value_got = pyqtSignal(str) # для каждого результата value_got
    finished_exp = pyqtSignal(str) # для всего эксперимента
    _mutex = QMutex()
    flag_soft_cc = 0
    PAUSE_TIME = 0.2
    lang_pack: dict

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        # todo: возможно need_pause и need_stop нужно тоже перезаписать на потокобезопасный
        self.need_pause = False # нужна пауза
        self.need_stop = False # нужна остановка
        self.need_stop_rised = False # необходимость остановки возникала
        self.image_saved = False # рисунок создан и сохранен на диск
        _, self.lang_pack = self.parent.parent.read_language_json("apply")

    def setup_image_saved(self, status):
        """
        Установить значение
        """
        self._mutex.lock()
        self.image_saved = status
        self._mutex.unlock()

    def run(self):
        """
        Запуск потока посылки тикета
        """
        if self.parent.parent.man.conn.board_type in ['VISA',]:
            on_VISA = True
        else:
            on_VISA = False  # Flag for VISA instruments
        for item in self.parent.coordinates:
            # todo: подобный функционал должен быть в manager
            if self.parent.parent.man.ap_config['board']['cc_type'] == 'soft':
                # читаем перед экспериментом
                resistance_previous = self.parent.parent.read_cell(item[0], # wl
                                                                item[1]) # bl
            # создаем эксперимент в БД
            name = self.parent.parent.exp_name
            status, memristor_id = self.parent.parent.man.db.get_memristor_id(item[0], # wl
                                                                              item[1], # bl
                                                                              self.parent.parent.man.crossbar_id)
            if not status:
                self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_mem_id"))
            status, experiment_id = self.parent.parent.man.db.add_experiment(name, memristor_id)
            if not status:
                self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_add_exp"))
            meta_info = self.parent.parent.man.get_meta_info()
            status, info = self.parent.parent.man.conn.get_tech_info()
            if not status:
                self.parent.parent.man.ap_logger.warning(self.lang_pack.get("err_conn"))
            if isinstance(meta_info, dict):
                meta_info['board'] = str(info)
            status = self.parent.parent.man.db.update_experiment(experiment_id, 'meta_info', pickle.dumps(meta_info))
            if not status:
                self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_meta"))
            # TODO remove: Initializing .csv save file -----------------
            if self.parent.parent.man.apply_save_csv:
                _, crossbar_serial = self.parent.parent.man.db.get_crossbar_serial_from_id(self.parent.parent.man.crossbar_id)
                csv_header = ['sign', 'vol', 'res', 'timestamp', 'temperature(C)', 'V_temp', 'smu_volt', 'smu_current', 'crossbar_id', "wl", "bl", "t_ms", "t_us", "exp_name", "ticket_name", "ticket_mode", "terminate_type", "terminate_1", "terminate_2"]
                csv_path = init_csv_apply(self.parent.parent.man.apply_csv_path, name, crossbar_serial, item[0], item[1], csv_header)
            # ----------------------------------------------------------
            # инициируем цикл по тикетам
            counter = 0  # Счетчик полученных значений (наносятся на график)
            task_counter = 0  # Счетчик тасков
            for ticket_info in self.parent.parent.exp_list: # ticket["name"], ticket, task_list, count
                ticket = ticket_info[1]
                # терминатор
                term_left, term_right = self.parent.parent.man.get_term_values(ticket['terminate'])
                # TODO remove teminator in Ohms ----------
                term_left_ohm = a2r(self.parent.parent.man.gain,
                                    self.parent.parent.man.res_load,
                                    self.parent.parent.man.vol_read,
                                    self.parent.parent.man.adc_bit,
                                    self.parent.parent.man.vol_ref_adc,
                                    self.parent.parent.man.res_switches,
                                    term_left)
                term_right_ohm = a2r(self.parent.parent.man.gain,
                                     self.parent.parent.man.res_load,
                                     self.parent.parent.man.vol_read,
                                     self.parent.parent.man.adc_bit,
                                     self.parent.parent.man.vol_ref_adc,
                                     self.parent.parent.man.res_switches,
                                     term_right)
                # ----------------------------------------
                # вбиваем координаты
                ticket['params']['wl'] = item[0]
                ticket['params']['bl'] = item[1]
                # сохраняем в БД
                status, ticket_id = self.parent.parent.man.db.add_ticket(ticket, experiment_id)
                if not status:
                    self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_tic"))
                # временный файл для результата
                result_file_path = time.strftime("%Y%m%d-%H%M%S")
                result_file = open(result_file_path, 'wb')
                #for task in task_list:
                #start_time_loop = time.time()
                # инициируем цикл по таскам
                result = 0
                task_generator = self.parent.parent.man.menu[ticket['mode']](ticket['params'], ticket['terminate'], self.parent.parent.man.blank_type)
                for task in task_generator:
                    if self.need_stop:
                        task_generator.throw(Exception("need stop 1"))
                        self.need_stop_rised = True
                        self.need_stop = False
                        continue
                    if self.need_pause:
                        while self.need_pause:
                            if self.need_stop:
                                task_generator.throw(Exception("need stop 2"))
                                self.need_stop_rised = True
                                self.need_stop = False
                                continue
                        if self.need_stop:
                            task_generator.throw(Exception("need stop 3"))
                            self.need_stop_rised = True
                            self.need_stop = False
                            continue
                    # посылаем задачу в плату
                    # если задача связана с подачей импульса (mode_7, mode_9) или ее результат нужно сохранить в БД
                    if task[0]['mode_flag'] in [7, 9, 'sense']: # todo: переделать, добавить в таску поле с флагом записи в БД
                        allowed = True # проверяем разрешение посылки
                        # включен программный ограничитель
                        if self.parent.parent.man.ap_config['board']['cc_type'] == 'soft':
                            # прогнозируем ток
                            if resistance_previous == 0:
                                resistance_previous = 0.00000001 # чтобы исключить деление на 0
                            current_predict = d2v(self.parent.parent.man.dac_bit, self.parent.parent.man.vol_ref_dac, task[0]['vol']) / resistance_previous
                            if not ((task[0]['sign'] == 0 and current_predict <= ticket['params']['dir_cc']) or (task[0]['sign'] == 1 and current_predict <= ticket['params']['rev_cc'])):
                                allowed = False # посылка запроса запрещена
                        if allowed:
                            result = self.parent.parent.man.conn.impact(task[0]) # result = (adc, id, timestamp)
                            # учет выполнения
                            if result:
                                self.value_got.emit(f"{counter},{result[0]},{task[0]['vol']},{task[0]['sign']},{term_left},{term_right},{task[0]['t_ms']},{task[0]['t_us']},{ticket['name']},{ticket['terminate']},{ticket['mode']},{result[2]},{result[3]},{result[4]}")
                                save_list_to_bytearray(result_file, task[0]['sign'], task[0]['vol'], result[0])
                                # TODO remove: saving to csv -------------------
                                if self.parent.parent.man.apply_save_csv:
                                    with open(csv_path, 'a', newline='', encoding='utf-8') as file:
                                        file_wr = csv.writer(file, delimiter=';')
                                        file_wr.writerow([
                                            task[0]['sign'],
                                            task[0]['vol'],
                                            result[0],  # res
                                            result[2],  # timestamp
                                            result[5],  # temperature(C)
                                            result[6],  # V_temp
                                            result[3],  # smu_volt
                                            result[4],  # smu_current
                                            crossbar_serial,  # crossbar_id
                                            item[0],  # wl
                                            item[1],  # bl
                                            task[0]['t_ms'],  # t_ms
                                            task[0]['t_us'],  # t_us
                                            name,  # exp_name
                                            ticket['name'],  # ticket_name
                                            ticket['mode'],  # ticket_mode
                                            ticket['terminate'].get('type'),  # terminate_type
                                            term_left_ohm,  # terminate_1
                                            term_right_ohm  # terminate_2
                                        ])
                                # ----------------------------------------------
                                resistance_previous = a2r(self.parent.parent.man.gain,
                                                        self.parent.parent.man.res_load,
                                                        self.parent.parent.man.vol_read,
                                                        self.parent.parent.man.adc_bit,
                                                        self.parent.parent.man.vol_ref_adc,
                                                        self.parent.parent.man.res_switches,
                                                        result[0])
                                # проверка прерывания тикета
                                interrupt = task[1](result)
                                if interrupt:
                                    task_generator.throw(Exception("interrupt"))
                                    continue
                        else:
                            self.flag_soft_cc = 1
                            self.parent.parent.man.ap_logger.critical("Программное ограничение тока!")
                        counter += 1
                    # иначе задача не связана с подачей сигнала
                    else:
                        request_status = self.parent.parent.man.conn.impact(task[0]) # result = (adc, id)
                        if request_status == 0: # запрос не выполнен, прерываем эксперимент
                            task_generator.throw(Exception("bad request"))
                            continue
                    task_counter += 1
                    self.count_changed.emit(task_counter)
                #print("Весь цикл:", time.time()-start_time_loop)
                # закрываем файл результата
                result_file.close()
                # Пытаемся остановить эксперимент на VISA-устройстве 
                if on_VISA and self.need_stop:
                    self.parent.parent.man.conn.impact({'mode_flag': 'panic', 'wl': item[0], 'bl': item[1], 'id': 0})     
                # сохраняем в БД статус завершения
                if result:
                    last_resistance = int(resistance_previous)  # Если результат есть, то сопротивление уже посчитали на последнем шаге цикла
                    status = self.parent.parent.man.db.update_last_resistance(memristor_id, last_resistance)
                    if not status:
                        self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_info"))
                    status = self.parent.parent.man.db.update_experiment(experiment_id, 'last_resistance', last_resistance)
                    if not status:
                        self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_res"))
                if self.need_stop:
                    status = self.parent.parent.man.db.update_ticket(ticket_id, 'status', 2)
                else:
                    status = self.parent.parent.man.db.update_ticket(ticket_id, 'status', 1)
                if not status:
                    self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_upd_tic"))
                # обновляем значения результата и изображения в БД (можно и здесь конечно)
                #time.sleep(self.PAUSE_TIME)
                # сохраняем результат выполнения тикета
                with open(result_file_path, 'rb') as result_file:
                    result_data = result_file.read()
                    # записываем в базу
                    self.parent.parent.man.db.update_ticket(ticket_id, 'result', result_data)
                os.remove(result_file_path)
                # вызываем событие завершения тикета
                self.ticket_finished.emit(f"{ticket_id},{result_file_path}")
                #time.sleep(self.PAUSE_TIME)
            #time.sleep(self.PAUSE_TIME) # чтобы избежать одновременного доступа к БД из потоков
            # сохраняем в БД статус завершения
            if self.need_stop_rised:
                stop_reason = 2 # прерван
            else:
                stop_reason = 1 # успешно завершен
            status = self.parent.parent.man.db.update_experiment_status(experiment_id, stop_reason)
            self.progress_finished.emit(f"{experiment_id},{stop_reason},{self.flag_soft_cc},{item[0]},{item[1]}")
            if not status:
                self.parent.parent.man.ap_logger.critical(self.lang_pack.get("err_stat"))
            # сохранить картинку эксперимента
            while not self.image_saved:
                time.sleep(0.5)
            with open(self.parent.ticket_image_name, 'rb') as ticket_image_file:
                img_data = ticket_image_file.read()
                # записываем в базу
                self.parent.parent.man.db.update_experiment(experiment_id, 'image', img_data)
            os.remove(self.parent.ticket_image_name)
            self.setup_image_saved(False)
            # прерываем выполнение для всех
            if self.need_stop:
                break
            #time.sleep(self.PAUSE_TIME*3) # ожидание между мемристорами чтобы успело сохранить в БД
        if on_VISA:  # Отключаем все ячейки в кроссбаре от источника
            self.parent.parent.man.conn.impact({'mode_flag': 'standby', 'wl': item[0], 'bl': item[1], 'id': 0})          
        self.finished_exp.emit(f'{stop_reason},{self.flag_soft_cc}') # успешно завершен
        #time.sleep(self.PAUSE_TIME)