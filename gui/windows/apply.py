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
import pyqtgraph as pg
import matplotlib.pyplot as plt
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal

from manager.service import d2v, a2r
from manager.service.saves import save_list_to_bytearray
from gui.src import show_choose_window, show_warning_messagebox

# todo: перенести в manager
def convert_adc_to_current(config_data, adc, vol, sign):
    """
    Конвертировать значение АЦП в ток
    """
    current = 0
    vol = d2v(config_data, vol)
    if sign:
        vol = - vol
    res = a2r(config_data, adc)
    if res != 0:
        current = vol/res
    return current

# todo: перенести в manager (проверить на совпадение с d2v)
def convert_dac_to_voltage(config_data,vol,sign):
    """
    Конвертировать значение ЦАП в напряжение
    """
    x_item = d2v(config_data, vol)
    if sign:
        x_item = - x_item
    return x_item

class Apply(QDialog):
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
    _data_for_plot_y: list
    _data_for_plot_x: list
    coordinates: list

    def __init__(self, parent=None) -> None:
        """
        Инициализация
        """
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
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
        self._data_for_plot_y = []
        self._data_for_plot_x = []
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
        if plt_type == 'линия':
            self.data_line = self.graph_result.plot(self._data_for_plot_x,
                                                    self._data_for_plot_y,
                                                    pen=pg.mkPen(width=3, color = (0, 128, 255)))
        elif plt_type == 'точки':
            self.data_line = self.graph_result.plot(self._data_for_plot_x,
                                                    self._data_for_plot_y,
                                                    symbol='o')
        elif plt_type == 'звездочки':
            self.data_line = self.graph_result.plot(self._data_for_plot_x,
                                                    self._data_for_plot_y,
                                                    symbol='star')

        self.termline_left = self.graph_result.plot(self._term_left_for_plot_x,
                                                    self._term_left_for_plot_y,
                                                    pen=pg.mkPen(width=3, color = (255, 0, 0)))
        self.termline_right = self.graph_result.plot(self._term_right_for_plot_x,
                                                     self._term_right_for_plot_y,
                                                     pen=pg.mkPen(width=3, color = (255, 0, 0)))
        # задание функции для отрисовки осей
        if self.ylabel_text == 'сопротивление, кОм':
            self.y_value_process = lambda y,vol,sign: a2r(self.parent.man, y)/1000
        elif self.ylabel_text == 'сопротивление, Ом':
            self.y_value_process = lambda y,vol,sign: a2r(self.parent.man, y)
        elif self.ylabel_text == 'отсчеты АЦП':
            self.y_value_process = lambda y,vol,sign: y
        elif self.ylabel_text == 'ток, мкА':
            self.y_value_process = lambda y,vol,sign: convert_adc_to_current(self.parent.man,y,vol,sign)/1e6
        elif self.ylabel_text == 'ток, мА':
            self.y_value_process = lambda y,vol,sign: convert_adc_to_current(self.parent.man,y,vol,sign)/1e3
        if self.xlabel_text == 'напряжение, В':
            self.x_value_process = lambda vol,sign,count: convert_dac_to_voltage(self.parent.man,vol,sign)
        elif self.xlabel_text == 'отсчеты':
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
            self.start_thread.need_pause = 0
        self.block_buttons([True, True, False, False]) # пауза остановить
        self.block_comdo(True)

    def pause_exp(self) -> None:
        """
        Поставить эксперимент на паузу
        """
        if self.application_status == "start": # работает
            self.application_status = "pause"
            self.start_thread.need_pause = 1
            self.block_buttons([False, True, True, False]) # запустить остановить

    def stop_exp(self) -> None:
        """
        Остановить эксперимент
        """
        if self.application_status == "start" or "pause": # работает
            self.start_thread.need_stop = 1
            self.application_status = "stop"
        self.block_buttons([False, False, True, True])
        self.block_comdo(False)
        self.total_impacts = self.parent.exp_list_params['total_tasks']
        self.update_label_total_count()

    def plot_settings(self) -> None:
        """
        Окно настройки графика
        """
        show_warning_messagebox("Пока не реализовано")

    def update_label_total_count(self) -> None:
        """
        Обновление лейбла
        """
        self.ui.label_total_count.setText(f"Осталось задач: {self.total_impacts}")

    def update_label_mem_id(self) -> None:
        """
        Обновление лейбла
        """
        mem_id = self.parent.man.db.get_memristor_id(self.parent.current_wl, self.parent.current_bl, self.parent.man.crossbar_id)
        self.ui.label_mem_id.setText(f"ID мемристора: wl={self.parent.current_wl}, bl={self.parent.current_bl}, id={mem_id[1]}")

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
        self.ui.button_pause.setDisabled(flags[2])
        self.ui.button_stop.setDisabled(flags[3])

    def closeEvent(self, event):
        """
        Закрытие
        """
        if self.application_status in ["start", "pause"]: # работает
            answer = show_choose_window(self, 'Останавливаем эксперимент?')
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
        self.start_thread = ApplyExp(parent=self)
        self.start_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
        self.start_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
        self.start_thread.value_got.connect(self.on_value_got) # при получении каждого измеренного
        self.start_thread.ticket_finished.connect(self.on_ticket_finished) # при получении каждого измеренного
        self.start_thread.finished_exp.connect(self.on_finished_exp) # закончился прогон
        self.start_thread.start()

    def on_finished_exp(self, value: int) -> None: ...

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
        # сохраняем результат
        value = value.split(",")
        ticket_id = int(value[0])
        result_file_path = value[1]
        with open(result_file_path, 'rb') as file:
            result_data = file.read()
            # записываем в базу
            self.parent.man.db.update_ticket(ticket_id, 'result', result_data)
        os.remove(result_file_path)

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
        experiment_id = int(value[0])
        exp_status = int(value[1])
        flag_soft_cc = int(value[2])
        # блочим запуск
        if exp_status == 1:
            show_warning_messagebox("Эксперимент выполнен!")
        elif exp_status == 2:
            show_warning_messagebox("Эксперимент прерван!")
        if flag_soft_cc:
            show_warning_messagebox("Срабатывало программное ограничение!")
        self.application_status = "stop"
        self.stop_exp()
        # сохранить картинку
        fname = "temp.png"
        plt.clf()
        plt.plot(self._data_for_plot_x, self._data_for_plot_y, 'o-')
        plt.xlabel(self.ui.xaxes_combobox.currentText())
        plt.ylabel(self.ui.yaxes_combobox.currentText())
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        plt.savefig(fname, dpi=100)
        with open(fname, 'rb') as file:
            img_data = file.read()
            # записываем в базу
            self.parent.man.db.update_experiment(experiment_id, 'image', img_data)
        os.remove(fname)

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
            x_item = self.x_value_process(vol, sign, count)
            size = 3000 # todo: глубина отрисовки, вынести в константы
            data_len = len(self._data_for_plot_y)
            if data_len > size:
                self._data_for_plot_y = self._data_for_plot_y[1:] + [y_item]
                self._data_for_plot_x = self._data_for_plot_x[1:] + [x_item]
            else:
                self._data_for_plot_y.append(y_item)
                self._data_for_plot_x.append(x_item)
            self.data_line.setData(self._data_for_plot_x, self._data_for_plot_y)
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
    finished_exp = pyqtSignal(int) # для всего эксперимента
    flag_soft_cc = 0
    PAUSE_TIME = 0.2

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.need_pause = 0 # нужна пауза
        self.need_stop = 0 # нужна остановка

    def run(self):
        """
        Запуск потока посылки тикета
        """
        for item in self.parent.coordinates:
            # todo: подобный функционал должен быть в manager
            # читаем перед экспериментом
            resistance_previous = self.parent.parent.read_cell(item[0], # wl
                                                               item[1]) # bl
            # создаем эксперимент в БД
            name = self.parent.parent.exp_name
            status, memristor_id = self.parent.parent.man.db.get_memristor_id(item[0], # wl
                                                                              item[1], # bl
                                                                              self.parent.parent.man.crossbar_id)
            if not status:
                self.parent.parent.man.ap_logger.critical("Ошибка БД не возможно получить id мемристора")
            status, experiment_id = self.parent.parent.man.db.add_experiment(name, memristor_id)
            if not status:
                self.parent.parent.man.ap_logger.critical("Ошибка БД не возможно добавить эксперимент")
            # инициируем цикл по тикетам
            counter = 0
            for ticket_info in self.parent.parent.exp_list: # ticket["name"], ticket, task_list, count
                ticket = ticket_info[1]
                # терминатор
                term_left, term_right = self.parent.parent.man.get_term_values(ticket['terminate'])
                # вбиваем координаты
                ticket['params']['wl'] = item[0]
                ticket['params']['bl'] = item[1]
                # сохраняем в БД
                status, ticket_id = self.parent.parent.man.db.add_ticket(ticket, experiment_id)
                if not status:
                    self.parent.parent.man.ap_logger.critical("Ошибка БД не возможно добавить тикет")
                # временный файл для результата
                fname = time.strftime("%Y%m%d-%H%M%S")
                file = open(fname, 'wb')
                #for task in task_list:
                #start_time_loop = time.time()
                # инициируем цикл по таскам
                result = 0
                for task in self.parent.parent.man.menu[ticket['mode']](ticket['params'], ticket['terminate'], self.parent.parent.man.blank_type):
                    if self.need_stop:
                        break
                    if self.need_pause:
                        while self.need_pause:
                            if self.need_stop:
                                break
                        if self.need_stop:
                            break
                    # посылаем задачу в плату
                    # start_time_iter = time.time()
                    # прогнозируем ток
                    current_predict = d2v(self.parent.parent.man, task[0]['vol']) / resistance_previous
                    if (task[0]['sign'] == 0 and current_predict <= 0.04) or (task[0]['sign'] == 1 and current_predict <= self.parent.parent.man.soft_cc):
                        #print(task[1])
                        result = self.parent.parent.man.conn.impact(task[0]) # result = (resistance, id)
                        # учет выполнения
                        if result:
                            self.value_got.emit(f"{counter},{result[0]},{task[0]['vol']},{task[0]['sign']},{term_left},{term_right}")
                            save_list_to_bytearray(file, task[0]['vol'], result[0])
                            resistance_previous = a2r(self.parent.parent.man, result[0])
                            # проверка прерывания тикета
                            interrupt = task[1](result)
                            if interrupt:
                                break
                    else:
                        self.flag_soft_cc = 1
                        self.parent.parent.man.ap_logger.critical("Программное ограничение тока!")
                    counter += 1
                    self.count_changed.emit(counter)
                #print("Весь цикл:", time.time()-start_time_loop)
                # закрываем файл рещультата
                file.close()
                # сохраняем в БД статус завершения
                if result:
                    last_resistance = int(a2r(self.parent.parent.man, result[0]))
                    status = self.parent.parent.man.db.update_last_resistance(memristor_id, last_resistance)
                    if not status:
                        self.parent.parent.man.ap_logger.critical("Ошибка БД не возможно обновить сопротивление")
                if self.need_stop:
                    status = self.parent.parent.man.db.update_ticket(ticket_id, 'status', 2)
                else:
                    status = self.parent.parent.man.db.update_ticket(ticket_id, 'status', 1)
                # обновляем значения результата и изображения в БД (можно и здесь конечно)
                time.sleep(self.PAUSE_TIME)
                self.ticket_finished.emit(f"{ticket_id},{fname}")
                time.sleep(self.PAUSE_TIME)
            time.sleep(self.PAUSE_TIME) # чтобы избежать одновременного доступа к БД из потоков
            # сохраняем в БД статус завершения
            if self.need_stop:
                status = self.parent.parent.man.db.update_experiment_status(experiment_id, 2) # прерван
                self.progress_finished.emit(f"{experiment_id},{2},{self.flag_soft_cc},{item[0]},{item[1]}")
            else:
                status = self.parent.parent.man.db.update_experiment_status(experiment_id, 1) # успешно завершен
                self.progress_finished.emit(f"{experiment_id},{1},{self.flag_soft_cc},{item[0]},{item[1]}")
            if not status:
                self.parent.parent.man.ap_logger.critical("Не возможно обновить статус эксперимента")
            # прерываем выполнение для всех
            if self.need_stop:
                break
            time.sleep(self.PAUSE_TIME*3) # ожидание между мемристорами чтобы успело сохранить в БД
        if self.need_stop:
            self.finished_exp.emit(2) # прерван
        else:
            self.finished_exp.emit(1) # успешно завершен
        time.sleep(self.PAUSE_TIME)