"""
Главное окно программы
https://realpython.com/python-pyqt-database/
https://www.geeksforgeeks.org/pyqt5-qtablewidget/
https://learntutorials.net/ru/pyqt5/topic/9544/%D0%B2%D0%B2%D0%B5%D0%B4%D0%B5%D0%BD%D0%B8%D0%B5-%D0%B2-%D0%B1%D0%B0%D1%80%D1%8B-%D0%BF%D1%80%D0%BE%D0%B3%D1%80%D0%B5%D1%81%D1%81%D0%B0
https://stackoverflow.com/questions/57891219/how-to-make-a-fast-matplotlib-live-plot-in-a-pyqt5-gui
"""

# pylint: disable=E0611,I1101,C0301,R0903,C0103,W0212

import os
import time
import json
import csv
import numpy as np
from numpy import inf
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QHeaderView, QTableWidgetItem, QShortcut
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt

from manager import Manager
from manager.service import a2r
from manager.service.global_settings import TICKET_PATH

from gui.windows.cell_info import CellInfo
from gui.windows.experiment import ExpSettings
from gui.windows.signal import SignalMod
from gui.windows.connect import ConnectDialog
from gui.windows.apply import Apply
from gui.windows.settings import Settings
from gui.windows.history import History
from gui.windows.requests import RequestsList
from gui.windows.terminal import Terminal
from gui.windows.testing import Testing
from gui.windows.map import Map
from gui.windows.cb_info import CbInfo
from gui.windows.rram import Rram
from gui.windows.new_ann import NewAnn
from gui.windows.wait import Wait
from gui.windows.math import Math
from gui.src import show_choose_window, show_warning_messagebox, snapshot

class Window(QMainWindow):
    """
    Основное окно
    """

    man: Manager # менеджер работы с платой
    GUI_PATH = os.path.join("gui","uies","crossbar.ui")
    all_resistances: list # все сопротивления для раскраски
    snapshot = None # для кнопки снимок
    close_modal_flag: bool = False # главное окно закрывает модальное окно

    all_results_progressed = 0
    number_results_wait = 0
    time_period = 200 # мс

    current_wl: int = None
    current_bl: int = None
    current_last_resistance: int = None
    exp_list: list = []
    exp_name: str = ''
    exp_list_params: dict = {}
    exp_list_params['total_tickets'] = 0
    exp_list_params['total_tasks'] = 0

    cell_info_dialog: CellInfo
    exp_settings_dialog: ExpSettings
    signal_dialog: SignalMod
    apply_dialog: Apply
    connect_dialog: ConnectDialog
    settings_dialog: Settings
    requests_dialog: RequestsList
    history_dialog: History
    terminal_dialog: Terminal
    testing_dialog: Testing
    map_dialog: Map
    cb_info_dialog: CbInfo
    rram_dialog: Rram
    new_ann_dialog: NewAnn
    wait_dialog: Wait
    opener: str = ''

    protected_modes: list = ['blank', # защищенные от удаления и перезаписи файлы
                             'endurance',
                             'iv-curve-reset',
                             'iv-curve-reversed',
                             'iv-curve-set',
                             'iv-curve',
                             'measure',
                             'plast-dep-pot',
                             'plast-pot-dep',
                             'prog-with-set',
                             'programming-reversed',
                             'programming',
                             'reset',
                             'retention',
                             'set']

    def __init__(self) -> None:
        super().__init__() # инит QMainWindow
        # менеджер работы с платой
        self.man = Manager()
        self.man.blank_type = 'mode_7'
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # параметры кроссбара
        self.ui.crossbar_progress.setVisible(False)
        # параметры таблицы
        self.ui.table_crossbar.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_crossbar.itemDoubleClicked.connect(self.show_cell_info_dialog)
        # обработчики кнопок
        self.ui.button_rram.clicked.connect(self.show_rram_dialog)
        self.ui.button_tests.clicked.connect(self.show_testing_dialog)
        self.ui.button_math.clicked.connect(self.show_math_dialog)
        self.ui.button_snapshot.clicked.connect(lambda: snapshot(self.snapshot))
        self.ui.button_net.clicked.connect(lambda: show_warning_messagebox('В процессе адаптации под открытый доступ!'))
        self.ui.button_settings.clicked.connect(self.show_settings_dialog)
        # хоткей
        shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        shortcut.activated.connect(self.show_terminal_dialog)
        shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        shortcut.activated.connect(self.show_crossbar_weights_dialog)
        shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        shortcut.activated.connect(self.show_cb_info_dialog)
        shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        shortcut.activated.connect(self.show_new_ann_dialog)
        shortcut = QShortcut(QKeySequence("Ctrl+U"), self)
        shortcut.activated.connect(lambda: self.read_cell_all('crossbar'))
        # диалоговое окно подключения
        self.show_connect_dialog()

    # методы открытия диалоговых окон

    def load_experiment(self, experiment_id: int) -> None:
        """
        Загрузка старого эксперимента
        """
        status, exp_name = self.man.db.get_exp_name(experiment_id)
        status, tickets = self.man.db.get_tickets(experiment_id)
        if status:
            self.show_exp_settings_dialog()
            self.exp_settings_dialog.load_tickets(exp_name, tickets)
    
    def show_math_dialog(self) -> None:
        """
        Показать окно математики
        """
        self.read_cell_all('crossbar') # чтение всех ячеек
        self.opener = 'math'
        self.current_bl = self.ui.table_crossbar.currentRow()
        self.current_wl = self.ui.table_crossbar.currentColumn()
        if self.current_bl == -1:
            self.current_bl = 0
            self.current_wl = 0
        self.current_last_resistance = self.ui.table_crossbar.item(self.current_bl, self.current_wl).text()
        self.math_dialog = Math(parent=self)
        self.math_dialog.show()
        self.showMinimized()
   
    def show_new_ann_dialog(self, mode=None) -> None: 
        """
        Показать окно записи
        """
        self.new_ann_dialog = NewAnn(parent=self, mode=mode)
        self.new_ann_dialog.show()

    def show_terminal_dialog(self) -> None:
        """
        Открыть терминал
        """
        self.terminal_dialog = Terminal(parent=self)
        self.terminal_dialog.show()

    def show_requests_dialog(self) -> None:
        """
        Окно всех запросов
        """
        self.requests_dialog = RequestsList(parent=self)
        self.requests_dialog.show()

    def show_connect_dialog(self) -> None:
        """
        Показать диалоговое окно подключения
        """
        self.connect_dialog = ConnectDialog(parent=self)
        self.connect_dialog.show()

    def show_history_dialog(self, mode: str = None) -> None:
        """
        Показать окно истории
        """
        self.history_dialog = History(parent=self, mode=mode)
        self.history_dialog.show()
        if mode == 'all' and self.opener != 'testing' and self.opener != 'rram':
            self.exp_settings_dialog.close()

    def show_cell_info_dialog(self) -> None:
        """
        Диалоговое окно информации о ячейке
        """
        self.opener = 'cell_info'
        self.current_bl = self.ui.table_crossbar.currentRow()
        self.current_wl = self.ui.table_crossbar.currentColumn()
        self.current_last_resistance = self.ui.table_crossbar.item(self.current_bl, self.current_wl).text()
        self.cell_info_dialog = CellInfo(parent=self)
        self.cell_info_dialog.show()

    def show_exp_settings_dialog(self) -> None:
        """
        Диалоговое окно эксперимент
        """
        self.exp_settings_dialog = ExpSettings(parent=self)
        self.exp_settings_dialog.show()

    def show_signal_dialog(self, ticket_name: str, mode: str) -> None:
        """
        Диалоговое окно сигнала
        """
        self.signal_dialog = SignalMod(ticket_name, mode, parent=self)
        self.signal_dialog.show()

    def show_apply_dialog(self) -> None:
        """
        Окно выполнения
        """
        self.apply_dialog = Apply(parent=self)
        self.apply_dialog.show()

    def show_settings_dialog(self) -> None:
        """
        Показать окно настроек
        """
        if not hasattr(self, 'settings_dialog'):
            self.settings_dialog = Settings(parent=self)
        self.settings_dialog.show()

    def show_testing_dialog(self) -> None:
        """
        Отобразить окно тестирования
        """
        self.opener = 'testing'
        self.testing_dialog = Testing(parent=self)
        self.testing_dialog.show()
        self.showMinimized()

    def show_map_dialog(self) -> None:
        """
        Открытие карты
        """
        self.map_dialog = Map(parent=self)
        self.map_dialog.show()

    def show_crossbar_weights_dialog(self) -> None:
        """
        Отображение весов кроссбара
        """
        self.show_map_dialog()
        self.map_dialog.fill_table(mode='weights')
        self.map_dialog.set_prompt("Веса кроссбара")

    def show_cb_info_dialog(self) -> None:
        """
        Открытие окна инормации о кроссбаре
        """
        self.cb_info_dialog = CbInfo(parent=self)
        self.cb_info_dialog.show()

    def show_rram_dialog(self) -> None:
        """
        Открытие окна инормации о кроссбаре
        """
        self.opener = 'rram'
        self.rram_dialog = Rram(parent=self)
        self.rram_dialog.show()
        self.showMinimized()

    def show_wait_dialog(self, opener) -> None:
        """
        Диалоговое окно прогрессбара
        """
        self.wait_dialog = Wait(opener=opener, parent=self)
        self.wait_dialog.show()

    # обработчики кнопок

    def custom_shaphop(self, data, title, save_flag=True, save_path=os.getcwd()):
        """
        Картинка imshow
        """
        plt.clf()
        x = np.arange(0, data.shape[1] + 1)
        y = np.arange(0, data.shape[0] + 1)
        plt.pcolormesh(x, y, data, edgecolors='k', linewidth=2)
        # Меняем цифры на оси X
        plt.xticks(x[:-1]+0.5, labels=x[:-1])
        # Меняем цифры на оси Y
        plt.yticks(y[:-1]+0.5, labels=y[:-1])
        # Отображаем график
        plt.title(title, linespacing=1.5)
        plt.tight_layout()
        if save_flag:
            plt.savefig(os.path.join(save_path,"result_map.png"))
            plt.close()
        else:
            plt.show()

    def update_current_cell_info(self):
        """
        Обновить информацию
        """
        _, mem_id = self.man.db.get_memristor_id(self.current_wl, self.current_bl, self.man.crossbar_id)
        _, self.current_last_resistance = self.man.db.get_last_resistance(mem_id)

    def fill_table(self) -> None:
        """
        Заполнение таблицы сопротивлений
        """
        # row count
        self.ui.table_crossbar.setRowCount(self.man.row_num)
        # column count
        self.ui.table_crossbar.setColumnCount(self.man.col_num)
        # table will fit the screen horizontally
        self.ui.table_crossbar.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # запрос к БД
        status, resistances = self.man.db.get_all_resistances(self.man.crossbar_id)
        if status:
            bl, wl, res = range(3)
            # раскрашиваем
            for item in resistances:
                self.ui.table_crossbar.setItem(item[bl], item[wl], QTableWidgetItem(str(item[res])))
                self.all_resistances[item[bl]][item[wl]] = item[res]
        self.ui.table_crossbar.setHorizontalHeaderLabels([str(i) for i in range(self.man.col_num)])
        self.ui.table_crossbar.setVerticalHeaderLabels([str(i) for i in range(self.man.row_num)])

    def is_writable_cells_file_correct(self) -> None:
        """
        Проверка csv файла ячеек
        """
        is_correct = True
        cells = []
        # формирование списка
        if self.man.get_meta_info()["writable_cells"] != '':
            with open(self.man.get_meta_info()["writable_cells"], 'r', newline='') as f:
                csvreader = csv.reader(f, delimiter=",")
                for row in csvreader:
                    if row[0] != "wl":
                        cells.append(row)
                f.close()
            # проверки
            if len(cells) >= self.man.row_num:
                return False, []
            for i in range(len(cells)):
                for j in range(len(cells[i])):
                    if cells[i][j].isalpha():
                        return False, []
                    if len(cells[i][j]) >= self.man.col_num:
                        return False, []
        return is_correct, cells

    def color_table(self) -> None:
        """
        Раскраска таблицы сопротивлений
        """
        try:
            sum_values = np.sum(self.all_resistances)
            log_resistances = np.log10(self.all_resistances)
            self.snapshot = np.zeros((self.man.row_num, self.man.col_num))
            writable = []

            if self.man.get_meta_info()["writable_cells"] != '':
                is_correct, cells = self.is_writable_cells_file_correct()
                if is_correct:
                    writable = [[0 for j in range(self.man.col_num)] for i in range(self.man.row_num)]
                    for i in range(len(cells)):
                        for j in range(len(cells[i])):
                            writable[i][int(cells[i][j])] = 1
                else:
                    show_warning_messagebox("Файл с рабочими ячейками некорректно сформирован!")
            print(writable)
            if sum_values != 0:
                colors = [[0 for j in range(self.man.col_num)] for i in range(self.man.row_num)]
                # определяем цвета
                max_resistance = np.max(log_resistances)
                min_resistance = np.min(log_resistances)
                if min_resistance == -inf:
                    min_resistance = 0
                for i in range(self.man.row_num):
                    for j in range(self.man.col_num):
                        item = self.ui.table_crossbar.item(i, j)
                        resistance = np.log10(int(self.ui.table_crossbar.item(i, j).text()))
                        if resistance == -inf:
                            color_value = 0
                        else:
                            color_value = (resistance - min_resistance)/(max_resistance - min_resistance)
                            color_value = int(color_value*255)
                        if writable != []:
                            if writable[i][j] == 1:
                                colors[i][j] = QColor(color_value, color_value, color_value)
                            else:
                                colors[i][j] = QColor(0, 0, 0)
                        else:
                            colors[i][j] = QColor(color_value, color_value, color_value)
                        self.snapshot[i][j] = color_value
        except ValueError:
            #show_warning_messagebox("Не возможно корректно задать цвета!")
            pass
        else:
            if sum_values != 0:
                # раскрашиваем
                for i in range(self.man.row_num):
                    for j in range(self.man.col_num):
                        item = self.ui.table_crossbar.item(i, j)
                        item.setBackground(colors[i][j])

    def read_cell(self, wl: int, bl: int) -> None:
        """
        Прочитать одну 
        """
        ticket_name = self.man.ap_config['gui']['measure_ticket']
        ticket = self.read_ticket_from_disk(ticket_name)
        ticket["params"]["wl"] = wl
        ticket["params"]["bl"] = bl
        # временное решение, лучше переписать на потоки
        _, memristor_id = self.man.db.get_memristor_id(wl, bl, self.man.crossbar_id)
        # _, experiment_id = self.man.db.add_experiment('measure', memristor_id)
        # _, ticket_id = self.man.db.add_ticket(ticket, experiment_id)
        for task in self.man.menu[ticket['mode']](ticket['params'],
                                                  ticket['terminate'],
                                                  self.man.blank_type):
            result = self.man.conn.impact(task[0]) # result = (resistance, id)
        try:
            last_resistance = int(a2r(self.man.gain,
                                      self.man.res_load,
                                      self.man.vol_read,
                                      self.man.adc_bit,
                                      self.man.vol_ref_adc,
                                      self.man.res_switches,
                                      result[0]))
        except IndexError:
            last_resistance = 0
        _ = self.man.db.update_last_resistance(memristor_id, last_resistance)
        # _ = self.man.db.update_ticket(ticket_id, 'status', 1)
        # _ = self.man.db.update_experiment_status(experiment_id, 1)
        return last_resistance

    def button_all_set_enabled(self, status):
        """
        Блок кнопок
        """
        self.ui.button_rram.setEnabled(status)
        self.ui.button_tests.setEnabled(status)
        self.ui.button_math.setEnabled(status)
        self.ui.button_snapshot.setEnabled(status)
        self.ui.button_net.setEnabled(status)
        self.ui.button_settings.setEnabled(status)

    def read_cell_all(self, opener) -> None:
        """
        Прочитать все
        """
        answer = show_choose_window(self, 'Прочитать все?')
        if answer:
            self.button_all_set_enabled(False)
            # окно
            self.show_wait_dialog(opener)
            # поток чтения
            self.wait_dialog.ui.progress_wait.setValue(0)
            self.wait_dialog.ui.progress_wait.setMaximum(self.man.col_num*self.man.row_num)
            self.wait_dialog.ui.progress_wait.setVisible(True)
            # тикет
            ticket_name = self.man.ap_config['gui']['measure_ticket']
            ticket = self.read_ticket_from_disk(ticket_name)
            # поток
            send_ticket_all_thread = SendTicketAll(ticket, parent=self)
            send_ticket_all_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
            send_ticket_all_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
            send_ticket_all_thread.start()

    def not_done(self) -> None:
        """
        Заглушка
        """
        show_warning_messagebox("Пока не реализовано")

    def read_ticket_from_disk(self, ticket_name: str) -> dict:
        """
        Чтение тикетов с диска

        Arguments:
            ticket_name -- название тикета + json 

        Returns:
            ticket -- тикет
        """
        fname = os.path.join(TICKET_PATH, ticket_name)
        with open(fname, encoding='utf-8') as file:
            ticket = json.load(file)
        return ticket

    def on_count_changed(self, value: int) -> None:
        """
        Изменение счетчика вызывает обновление прогрессбара
        """
        self.wait_dialog.ui.progress_wait.setValue(value)

    def on_progress_finished(self, value: int) -> None:
        """
        Завершение выполнения скрываем прогресс бар
        """
        self.fill_table()
        self.color_table()
        self.button_all_set_enabled(True)
        self.wait_dialog.ui.progress_wait.setValue(0)
        self.wait_dialog.close()

    def closeEvent(self, event) -> None:
        """
        Закрытие окна
        """
        if self.close_modal_flag:
            self.safe_close()
            event.accept()
        else:
            answer = show_choose_window(self, 'Выходим?')
            if answer:
                self.safe_close()
                event.accept()
            else:
                event.ignore()

    def safe_close(self) -> None:
        """
        Безопасное завершение
        """
        # поиск и удаление бэкапа
        backup = self.man.get_meta_info()["backup"]
        if os.path.exists(backup+"backup.db"):
            os.remove(backup+"backup.db")
        elif os.path.exists(os.path.join(os.getcwd(), "base.db")[:-7] +"backup.db"):
            os.remove(os.path.join(os.getcwd(), "base.db")[:-7] +"backup.db")
        # резервное копирование дб
        if not os.path.isdir(backup):
            backup = os.path.join(os.getcwd(), "base.db")[:-7]
        _ = self.man.db.db_backup(backup)
        # закрытие программы
        self.man.abort()
        self.man.close()
        time.sleep(0.1) # может и не надо

class SendTicketAll(QThread):
    """
    Послать одинаковый тикет на все ячейки
    """
    count_changed = pyqtSignal(int)
    progress_finished = pyqtSignal(int)

    def __init__(self, ticket, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.ticket = ticket

    def run(self):
        """
        Запуск потока посылки тикета
        """
        counter = 0
        for i in range(self.parent.man.col_num):
            for j in range(self.parent.man.row_num):
                self.ticket["params"]["wl"] = i
                self.ticket["params"]["bl"] = j
                # временное решение, лучше переписать на потоки
                _, memristor_id = self.parent.man.db.get_memristor_id(i, j, self.parent.man.crossbar_id)
                for task in self.parent.man.menu[self.ticket['mode']](self.ticket['params'],
                                                 self.ticket['terminate'],
                                                 self.parent.man.blank_type):
                    result = self.parent.man.conn.impact(task[0]) # result = (resistance, id)
                try:
                    last_resistance = int(a2r(self.parent.man.gain,
                                            self.parent.man.res_load,
                                            self.parent.man.vol_read,
                                            self.parent.man.adc_bit,
                                            self.parent.man.vol_ref_adc,
                                            self.parent.man.res_switches,
                                            result[0]))
                except IndexError:
                    last_resistance = 0
                _ = self.parent.man.db.update_last_resistance(memristor_id, last_resistance)
                counter += 1
                self.count_changed.emit(counter)
        self.progress_finished.emit(counter)
