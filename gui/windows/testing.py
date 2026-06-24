"""
Тестирование всех ячеек
"""

# pylint: disable=E0611,C0103,I1101,C0301,W0107

import os
import csv
import time
import datetime
import copy
# import pandas as pd
# import plotly.express as px
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
import numpy as np
import numpy.typing as npt
import ast

from manager.service import a2r, d2v
from gui.src import open_file_dialog, show_warning_messagebox, show_choose_window, choose_cells
from gui.windows.apply import ApplyExp

def read_csv(file_path, delimiter):
    """
    Чтение csv
    """
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)
        header = next(reader)  # Пропускаем заголовок
        # Проверяем, что в заголовке есть нужные колонки.
        data = {}
        for item in header:
            data[item] = []
        keys = list(data.keys())
        for row in reader:
            for i,item in enumerate(row):
                if item.isdigit():
                   data[keys[i]].append(int(item))
                else:
                    try:
                        data[keys[i]].append(float(item))
                    except Exception:
                        data[keys[i]].append(item)
        return copy.deepcopy(data)

def custom_shaphop(data, title, save_flag=True, save_path=os.getcwd()):
    """
    Отображение живых мемристоров
    """
    plt.clf()
    # data = np.flipud(data) # отражение для правильной отрисовки
    cmap = plt.cm.colors.ListedColormap(['gray', 'red', 'green'])
    plt.imshow(data, cmap=cmap, aspect='equal', interpolation='nearest')
    # Отображаем график
    plt.title(title, linespacing=1.5)
    plt.tight_layout()
    if save_flag:
        plt.savefig(os.path.join(save_path,"result_map.png"))
        plt.close()
    else:
        plt.show()

class Testing(QWidget):
    """
    Тестирование всех ячеек
    """

    GUI_PATH = os.path.join("gui","uies","testing.ui")
    result_path: str
    application_status: str = 'stop'
    coordinates: list
    counter: int # прогрессбар
    start_time: float
    # raw_adc_all: list
    crossbar_serial: str
    raw_data: list
    raw_data_extended: list
    data_for_plot_x: list
    data_for_plot_y: list
    start_thread: ApplyExp
    cell_list_from_file: bool
    exp_time_estimated: float
    csv_names: list
    ticket_image_name: str = "temp.png"
    terminator: dict
    lang_pack: dict

    def __init__(self, parent=None) -> None: # +
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        self.ui.setWindowFlags(Qt.Window)
        # доп настройки
        #self.setModal(True)
        # обработчик нажатия
        # вкладка Управление тестом
        self.ui.button_choose_exp.clicked.connect(self.button_choose_exp_clicked)
        self.ui.button_start_exp.clicked.connect(self.button_start_exp_clicked)
        self.ui.button_choose_folder.clicked.connect(self.button_choose_folder_clicked)
        self.ui.button_reset_exp.clicked.connect(self.button_reset_exp_clicked)
        self.ui.button_choose_cells.clicked.connect(self.button_choose_cells_clicked)
        # вкладка Анализ результатов
        self.ui.button_result.clicked.connect(self.button_result_clicked)
        # вкладка Визуализация
        self.ui.button_generate_images.clicked.connect(self.button_generate_images_clicked)
        # значения по умолчанию
        self.result_path = os.getcwd()
        self.set_up_init_values()

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("testing")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.groupBox.setTitle(self.lang_pack.get("results"))
            self.ui.label.setText(self.lang_pack.get("path"))
            self.ui.button_choose_folder.setText(self.lang_pack.get("view"))
            self.ui.tabWidget.setTabText(0, self.lang_pack.get("test_maintenance"))
            self.ui.tabWidget.setTabText(1, self.lang_pack.get("results_analysis"))
            self.ui.tabWidget.setTabText(2, self.lang_pack.get("visual"))
            self.ui.button_choose_exp.setText(self.lang_pack.get("exp"))
            self.ui.button_choose_cells.setText(self.lang_pack.get("cells"))
            self.ui.button_start_exp.setText(self.lang_pack.get("run"))
            self.ui.button_reset_exp.setText(self.lang_pack.get("interrupt"))
            self.ui.combo_rmin_mode.setItemText(0, self.lang_pack.get("more"))
            self.ui.combo_rmin_mode.setItemText(1, self.lang_pack.get("less"))
            self.ui.combo_rmax_mode.setItemText(0, self.lang_pack.get("more"))
            self.ui.combo_rmax_mode.setItemText(1, self.lang_pack.get("less"))
            self.ui.label_4.setText(self.lang_pack.get("ohm"))
            self.ui.label_6.setText(self.lang_pack.get("ohm"))
            self.ui.label_3.setText(self.lang_pack.get("r_r_more"))
            self.ui.button_result.setText(self.lang_pack.get("count"))
            self.ui.label_7.setText(self.lang_pack.get("axisx"))
            self.ui.label_8.setText(self.lang_pack.get("axisy"))
            self.ui.combo_xlabel.setItemText(0, self.lang_pack.get("voltage"))
            self.ui.combo_xlabel.setItemText(1, self.lang_pack.get("counting"))
            self.ui.combo_ylabel.setItemText(0, self.lang_pack.get("resistance"))
            self.ui.combo_ylabel.setItemText(1, self.lang_pack.get("amperage"))
            self.ui.button_generate_images.setText(self.lang_pack.get("make_graphics"))

    def set_up_init_values(self) -> None: # +
        """
        Установить по умолчанию
        """
        self.ui.path_folder_csv.setText(self.result_path)
        _, self.crossbar_serial = self.parent.man.db.get_crossbar_serial_from_id(self.parent.man.crossbar_id)
        # список координат для теста
        self.coordinates = []
        for i in range(self.parent.man.row_num):
            for j in range(self.parent.man.col_num):
                self.coordinates.append((j,i))
        self.raw_data = []
        self.raw_data_extended = []
        self.data_for_plot_x = []
        self.data_for_plot_y = []
        self.start_time = 0.
        self.parent.exp_list = []
        self.parent.exp_name = ''
        self.parent.exp_list_params = {}
        self.parent.exp_list_params['total_tickets'] = 0
        self.parent.exp_list_params['total_tasks'] = 0
        self.button_open_combination()
        self.ui.label_all_cells_count.setText(self.lang_pack.get("cells_chosen") + str(len(self.coordinates)))
        self.ui.label_time_status.setText(self.lang_pack.get("exec_time"))
        self.ui.label_start_time.setText(self.lang_pack.get("exec_start"))
        self.ui.label_result.setText(self.lang_pack.get("suitable"))
        self.cell_list_from_file = False
        self.exp_time_estimated = 0.
        self.csv_names = []

    def button_choose_cells_clicked(self) -> None: # +
        """
        Выбрать ячейки для эксперимента
        """
        filepath = open_file_dialog(self, file_types="CSV Files (*.csv)")
        if filepath:
            # нужно сформировать список кортежей
            cells = []
            message = ''
            wl_max = self.parent.man.col_num
            bl_max = self.parent.man.row_num
            try:
                cells, message = choose_cells(filepath, wl_max, bl_max)
            except FileNotFoundError:
                message = self.lang_pack.get("error_file") + filepath
            except ValueError as e:
                message = self.lang_pack.get("error") + e
            except Exception as e:
                message = self.lang_pack.get("error") + e
            if message:
                show_warning_messagebox(parent=self, message=message)
            if cells:
                self.coordinates = cells
                self.cell_list_from_file = True
                show_warning_messagebox(parent=self, message=self.lang_pack.get("tested_cells") + str(len(cells)))
            else:
                show_warning_messagebox(parent=self, message=self.lang_pack.get("all_cells"))
                self.cell_list_from_file = False
        else:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("all_cells"))
            self.cell_list_from_file = False
        self.update_label_all_cells_count()

    def button_choose_exp_clicked(self) -> None: # +
        """
        Выбрать эксперимент
        """
        self.set_up_init_values()
        self.parent.show_history_dialog(mode="all")

    def button_start_exp_clicked(self) -> None: # +
        """
        Старт обработки
        """
        message = str(len(self.coordinates)) + self.lang_pack.get("tested_for") + str(self.exp_time_estimated) + self.lang_pack.get("continue")
        answer = show_choose_window(self, message)
        if answer:
            wl = self.parent.man.col_num
            bl = self.parent.man.row_num
            # self.raw_adc_all = [[[] for j in range(wl)] for i in range(bl)]
            self.application_status = 'work'
            self.start_time = time.time()
            self.update_label_start_time()
            # блочим кнопки
            self.button_work_combination()
            # записываем файлы с координатами
            fname = 'tested_cells.csv'
            fpath = os.path.join(self.result_path, fname)
            with open(fpath, 'w', newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=",")
                file_wr.writerow(['wl','bl'])
                for item in self.coordinates:
                    file_wr.writerow(item)
            fname = 'not_tested_cells.csv'
            fpath = os.path.join(self.result_path, fname)
            with open(fpath, 'w', newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=",")
                file_wr.writerow(['wl','bl'])
                for i in range(bl):
                    for j in range(wl):
                        if (j, i) not in self.coordinates:
                            file_wr.writerow((j, i))
            # параметры прогресс бара
            self.counter = 0
            self.ui.progress_all.setValue(0)
            self.ui.progress_all.setMaximum(len(self.coordinates))
            # параметры потока
            self.start_thread = ApplyExp(parent=self)
            self.start_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
            self.start_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
            self.start_thread.value_got.connect(self.on_value_got) # при получении каждого измеренного
            self.start_thread.ticket_finished.connect(self.on_ticket_finished) # при получении каждого измеренного
            self.start_thread.finished_exp.connect(self.on_finished_exp) # закончился прогон
            self.start_thread.start()

    def on_finished_exp(self, value: int) -> None: # +
        """
        Закончился тест
        """
        value = value.split(',')
        stop_reason = int(value[0])
        self.ui.progress_all.setValue(0)
        if stop_reason == 1:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("tested") + str(round(time.time() - self.start_time,2)) + self.lang_pack.get("sec"))
        elif stop_reason == 2:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("exp_interrupted"))
        time.sleep(1) # чтобы всё успело сохраниться на диск
        self.application_status = 'stop'
        # сохраняем список результатов
        # todo: если эксперимент не удачный, то файлы потом не открыть
        with open(os.path.join(self.result_path, 'csv_list.txt'), 'w', encoding='utf-8') as file:
            file.writelines(self.csv_names)
        self.csv_names = []
        # self.set_up_init_values()
        self.button_finish_combination()

    def on_count_changed(self, value: int) -> None: # +
        """
        На изменение счетчика
        """
        pass

    def on_progress_finished(self, value: str) -> None: # +
        """
        Завершился поток для одного мемристора
        """
        # чтобы успеть пока поток ApplyExp не начнет работать
        raw_data = copy.deepcopy(self.raw_data)
        raw_data_extended = copy.deepcopy(self.raw_data_extended)
        data_for_plot_x = copy.deepcopy(self.data_for_plot_x)
        data_for_plot_y = copy.deepcopy(self.data_for_plot_y)
        # очищаем для потока ApplyExp
        self.raw_data = []
        self.raw_data_extended = []
        self.data_for_plot_x = []
        self.data_for_plot_y = []
        # сохраняем результат в файл
        value = value.split(",")
        # сохранение файла
        wl = int(value[3])
        bl = int(value[4])
        fname = f'{self.crossbar_serial}_{self.parent.exp_name}_{wl}_{bl}.csv'
        fpath = os.path.join(self.result_path, fname)
        with open(fpath, 'w+', newline='', encoding='utf-8') as file:
            file_wr = csv.writer(file, delimiter=";")
            file_wr.writerow(['sign','dac','adc','vol','res', 'timestamp', "crossbar_id", "dac_bit", "vol_ref_dac", "res_load", "vol_read", "adc_bit", "vol_ref_adc", "res_switches", "gain", "wl", "bl", "t_ms", "t_us", "exp_name", "ticket_name", "terminate_type", "terminate_1", "terminate_2"])
            for item_index, item in enumerate(raw_data):
                file_wr.writerow([item[0],  # 'sign'
                                  item[1],  # 'dac'
                                  item[2],  # 'adc'
                                  data_for_plot_x[item_index],  # 'vol'
                                  data_for_plot_y[item_index],  # 'res'
                                  item[3],   # 'timestamp'
                                  self.crossbar_serial, # "crossbar_id"
                                  self.parent.man.get_meta_info()["dac_bit"],
                                  self.parent.man.get_meta_info()["vol_ref_dac"],
                                  self.parent.man.get_meta_info()["res_load"],
                                  self.parent.man.get_meta_info()["vol_read"],
                                  self.parent.man.get_meta_info()["adc_bit"],
                                  self.parent.man.get_meta_info()["vol_ref_adc"],
                                  self.parent.man.get_meta_info()["res_switches"],
                                  self.parent.man.get_meta_info()["gain"],
                                  wl,
                                  bl,
                                  raw_data_extended[item_index][0],
                                  raw_data_extended[item_index][1],
                                  self.parent.exp_name,
                                  raw_data_extended[item_index][2],
                                  raw_data_extended[item_index][3],
                                  raw_data_extended[item_index][4],
                                  raw_data_extended[item_index][5],
                                  ])
        self.csv_names.append(fname+'\n')
        # рисунок для базы в matplotlib
        plt.rcParams['agg.path.chunksize'] = 20000  # FIXME: This is a hacky fix
        # При исполнении теста на множество ячеек с большим количеством точек (endurance 1e5 циклов)
        # рисунок не сохраняется (OverflowError). Возможно, лучше рисовать не все точки
        plt.clf()
        if len(data_for_plot_x) > 1000:
            plt.plot(data_for_plot_x[0:1000], data_for_plot_y[0:1000], marker='o', linewidth=0.5)
        else:
            plt.plot(data_for_plot_x, data_for_plot_y, marker='o', linewidth=0.5)
        plt.xlabel(self.lang_pack.get("voltage"))
        plt.ylabel(self.lang_pack.get("resistance"))
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        plt.savefig(self.ticket_image_name, dpi=100)
        plt.close()
        self.start_thread.setup_image_saved(True)
        # прогрессбар
        self.counter += 1
        self.ui.progress_all.setValue(self.counter)

    def on_value_got(self, value: str) -> None: # +
        """
        Получили значение
        """
        value = value.split(",")
        adc_value = int(value[1])
        dac_value = int(value[2])
        sign = int(value[3])
        if len(value) > 11:
            self.terminator = ast.literal_eval(value[9]+", " +value[10] + ", " +value[11])
        else:
            self.terminator = ast.literal_eval(value[9]+", " +value[10])
        if isinstance(self.terminator.get("value"), int):
            term_1 = self.terminator.get("value")
            term_2 = ""
        else:
            term_1 = self.terminator.get("value")[0]
            term_2 = self.terminator.get("value")[1]
        self.raw_data.append((sign, dac_value, adc_value, datetime.datetime.now().timestamp()))
        self.raw_data_extended.append((int(value[6]), int(value[7]), value[8], self.terminator.get("type"), term_1, term_2)) # t_ms, t_us, ticket_name, terminate
        self.data_for_plot_x.append(d2v(self.parent.man.dac_bit,
                                        self.parent.man.vol_ref_dac,
                                        dac_value,
                                        sign=sign))
        self.data_for_plot_y.append(a2r(self.parent.man.gain,
                                        self.parent.man.res_load,
                                        self.parent.man.vol_read,
                                        self.parent.man.adc_bit,
                                        self.parent.man.vol_ref_adc,
                                        self.parent.man.res_switches,
                                        adc_value))

    def on_ticket_finished(self, value: str) -> None: # +
        """
        Закончился тикет
        """
        pass

    def button_reset_exp_clicked(self) -> None: # +
        """
        Прервать выполнение эксперимента
        """
        self.start_thread.need_stop = 1

    def button_choose_folder_clicked(self) -> None: # +
        """
        Выбрать папку
        """
        directory = ""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", "/")
        if directory:
            self.result_path = directory
            self.ui.path_folder_csv.setText(self.result_path)

    def button_work_combination(self) -> None: # +
        """
        Отображение кнопок при старте эксперимента
        """
        self.ui.button_choose_exp.setEnabled(False)
        self.ui.button_choose_cells.setEnabled(False)
        self.ui.button_start_exp.setEnabled(False)
        self.ui.button_choose_folder.setEnabled(False)
        self.ui.button_reset_exp.setEnabled(True)
        self.ui.button_result.setEnabled(True)
        self.ui.button_generate_images.setEnabled(True)

    def button_open_combination(self) -> None: # +
        """
        Отображение кнопок при открытии окна
        """
        self.ui.button_choose_exp.setEnabled(True)
        self.ui.button_choose_cells.setEnabled(False)
        self.ui.button_start_exp.setEnabled(False)
        self.ui.button_choose_folder.setEnabled(True)
        self.ui.button_reset_exp.setEnabled(False)
        self.ui.button_result.setEnabled(True)
        self.ui.button_generate_images.setEnabled(True)

    def button_ready_combination(self) -> None: # +
        """
        Отображение кнопок при готовности выполнять
        (после загрузки плана эксперимента)
        """
        self.ui.button_choose_exp.setEnabled(True)
        self.ui.button_choose_cells.setEnabled(True)
        self.ui.button_start_exp.setEnabled(True)
        self.ui.button_choose_folder.setEnabled(True)
        self.ui.button_reset_exp.setEnabled(False)
        self.ui.button_result.setEnabled(True)
        self.ui.button_generate_images.setEnabled(True)

    def button_finish_combination(self) -> None: # +
        """
        Отображение кнопок при завершении эксперимента
        """
        self.ui.button_choose_exp.setEnabled(True)
        self.ui.button_choose_cells.setEnabled(True)
        self.ui.button_start_exp.setEnabled(True)
        self.ui.button_choose_folder.setEnabled(True)
        self.ui.button_reset_exp.setEnabled(False)
        self.ui.button_result.setEnabled(True)
        self.ui.button_generate_images.setEnabled(True)

    def update_label_time_status(self) -> None: # +
        """
        Обновить время выполнения
        """
        num_cells = len(self.coordinates)
        # self.exp_time_estimated = round((((self.parent.exp_list_params['total_tasks'] * num_cells) * 60) / 1000) / 60, 0) # todo: скорректировать время
        self.exp_time_estimated = round((((self.parent.exp_list_params['total_tasks'] * num_cells) * self.parent.man.conn.meta_info['task_time']) / 1000) / 60, 0)
        self.ui.label_time_status.setText(self.lang_pack.get("exec_time") + str(self.exp_time_estimated))

    def update_label_start_time(self) -> None: # +
        """
        Обновить лейбл начала эксперимента
        """
        self.ui.label_start_time.setText(self.lang_pack.get("exec_start") + str(time.strftime('%H:%M', time.localtime(self.start_time))))

    def update_label_all_cells_count(self) -> None: # +
        """
        Обновить лейбл с количеством ячеек
        """
        self.ui.label_all_cells_count.setText(self.lang_pack.get("cells_chosen") + str(len(self.coordinates)))

    def closeEvent(self, event) -> None: # +
        """
        Закрытие окна
        """
        if self.application_status == 'stop':
            # todo: сделать в parent функцию set_up_init_values()
            self.parent.opener = None
            self.parent.fill_table()
            self.parent.color_table()
            self.set_up_init_values()
            self.parent.showNormal()        
            event.accept()
        elif self.application_status == 'work':
            show_warning_messagebox(parent=self, message=self.lang_pack.get("wait_or_interrupt"))
            event.ignore()

    def button_result_clicked(self) -> None: # +
        """
        Показать результат:
        0 - ячейка не тестировалась
        1 - ячейка не отвечает на стимулы
        2 - ячейка имеет резистивное переключение
        """
        # работаем с файлами
        dirlist = os.listdir(self.result_path)
        if 'csv_list.txt' in dirlist and 'tested_cells.csv' in dirlist and 'not_tested_cells.csv' in dirlist:
            # подготовка
            good_mem_count = 0
            bad_mem_count = 0
            # параметры оценки
            treshhold = float(self.ui.spinbox_tresh.value())
            rmin = float(self.ui.spinbox_rmin.value())
            rmax = float(self.ui.spinbox_rmax.value())
            # определяем общее количество ячеек
            all_wl = []
            all_bl = []
            df = read_csv(os.path.join(self.result_path, 'tested_cells.csv'), delimiter=',')
            all_wl += df['wl']
            all_bl += df['bl']
            df = read_csv(os.path.join(self.result_path, 'not_tested_cells.csv'), delimiter=',')
            all_wl += df['wl']
            all_bl += df['bl']
            wl_max = max(all_wl) + 1
            bl_max = max(all_bl) + 1
            all_cells_count = wl_max * bl_max
            # подготавливаем heat_map
            heat_map = np.zeros((bl_max, wl_max)) # все нули - не провереные ячейки
            # идем по файлам csv и определяем res_min и res_max
            with open(os.path.join(self.result_path, 'csv_list.txt'), 'r', encoding='utf-8') as file:
                csv_paths = file.readlines()
            for path in csv_paths:
                if os.path.exists(os.path.join(self.result_path, path.rstrip())):
                    wl = int(path.split('.')[-2].split('_')[-2])
                    bl = int(path.split('.')[-2].split('_')[-1])
                    df = read_csv(os.path.join(self.result_path, path.rstrip()), delimiter=';')
                    resistances = df['res']
                    min_res = min(resistances)
                    max_res = max(resistances)
                    # условия годности
                    case_rmin = True # условие для rmin
                    case_rmax = True # условие для rmax
                    case_tres = True # условие диапазона
                    # проверяем условия
                    if self.ui.checkbox_rmin.isChecked():
                        mode = self.ui.combo_rmin_mode.currentText()
                        if mode == self.lang_pack.get("more"):
                            case_rmin = min_res > rmin
                        elif mode == self.lang_pack.get("less"):
                            case_rmin = min_res < rmin
                    if self.ui.checkbox_rmax.isChecked():
                        mode = self.ui.combo_rmax_mode.currentText()
                        if mode == self.lang_pack.get("more"):
                            case_rmax = max_res > rmax
                        elif mode == self.lang_pack.get("less"):
                            case_rmax = max_res < rmax
                    if self.ui.checkbox_rtresh.isChecked():
                        if max_res/min_res < treshhold: # меньше трешхолда
                            case_tres = False
                    # собираем условие в одно
                    work_status = case_rmin and case_rmax and case_tres
                    if work_status:
                        heat_map[bl][wl] = 2 # ячейка рабочая
                        good_mem_count += 1
                    else:
                        heat_map[bl][wl] = 1 # ячейка не рабочая
                        bad_mem_count += 1
            # сохраняем результаты
            # создаем папку для результатов
            now = datetime.datetime.now()
            formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
            analysis_path = f'analysis_{formatted_date}'
            os.mkdir(os.path.join(self.result_path, analysis_path))
            # делаем картинку
            all_tested_count = good_mem_count + bad_mem_count
            serial_label = self.lang_pack.get("serial") + str(self.crossbar_serial) + '\n'
            data_label = self.lang_pack.get("date") + str(formatted_date) + '\n'
            status_label = self.lang_pack.get("suitable_cells") + str(np.round(good_mem_count/all_tested_count*100, 2)) + '%\n'
            all_data_label = self.lang_pack.get("all") + str(all_cells_count) + self.lang_pack.get("tested_cells_1") + str(all_tested_count) + self.lang_pack.get("suitable_cells") + str(good_mem_count) + self.lang_pack.get("other") + str(bad_mem_count)
            title = serial_label + data_label + status_label + all_data_label
            custom_shaphop(copy.deepcopy(heat_map), title, save_flag=True, save_path=os.path.join(self.result_path, analysis_path))
            self.ui.label_result.setText(self.lang_pack.get("suitable_cells") + str(np.round(good_mem_count/all_tested_count*100, 2)) + '%')
            # запись csv годные
            fname = os.path.join(self.result_path, analysis_path, 'good_cells.csv')
            with open(fname,'w', newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=",")
                file_wr.writerow(['wl','bl'])
                for i in range(bl_max):
                    for j in range(wl_max):
                        if heat_map[i][j] == 2: # есть РП
                            file_wr.writerow([j, i])
            fname = os.path.join(self.result_path, analysis_path, 'bad_cells.csv')
            # запись csv не годные
            # todo: сделать отдельной функцией чтобы не дублировать код
            with open(fname,'w', newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=",")
                file_wr.writerow(['wl','bl'])
                for i in range(bl_max):
                    for j in range(wl_max):
                        if heat_map[i][j] == 1: # 1 - нет РП
                            file_wr.writerow([j, i])

    def button_generate_images_clicked(self) -> None: # +
        """
        Отрисовка графиков
        """
        # работаем с файлами
        dirlist = os.listdir(self.result_path)
        if 'csv_list.txt' in dirlist:
            df = read_csv(os.path.join(self.result_path, 'tested_cells.csv'), delimiter=',')
            self.ui.button_generate_images.setEnabled(False)
            # параметры прогресс бара
            self.counter = 0
            self.ui.progress_images.setValue(0)
            self.ui.progress_images.setMaximum(len(df['wl']))
            # параметры потока
            self.image_thread = ImageGenerator(parent=self)
            self.image_thread.count_changed.connect(self.on_count_changed_image) # заполнение прогрессбара
            self.image_thread.progress_finished.connect(self.on_progress_finished_image) # после выполнения
            self.image_thread.need_image.connect(self.on_need_image) # нужно сохранить картинку
            self.image_thread.start()

    def on_count_changed_image(self, value: int) -> None: # +
        """
        Двигаем прогрессбар
        """
        self.ui.progress_images.setValue(value)

    def on_progress_finished_image(self, value: int) -> None: # +
        """
        Картинки отрисованы
        """
        self.ui.progress_images.setValue(0)
        self.ui.button_generate_images.setEnabled(True)
        show_warning_messagebox(parent=self, message=self.lang_pack.get("pics_done"))

    def on_need_image(self, value):
        """
        Строим картинку
        """
        plt.clf()
        plt.plot(self.image_thread.x_data, self.image_thread.y_data, marker='o', linewidth=0.5)
        plt.xlabel(self.image_thread.xlabel_type)
        plt.ylabel(self.image_thread.ylabel_type)
        plt.title(f'{self.crossbar_serial}_{self.image_thread.wl}_{self.image_thread.bl}')
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        plt.savefig(os.path.join(self.result_path,
                                    self.image_thread.analysis_path,
                                    f'{self.crossbar_serial}_{self.image_thread.wl}_{self.image_thread.bl}.png'),
                                    dpi=100)
        plt.close()
        self.image_thread.setup_image_saved(True)

class ImageGenerator(QThread):
    """
    Поток эксперимента
    """

    count_changed = pyqtSignal(int) # для каждой task
    progress_finished = pyqtSignal(int) # для каждого мемристора из self.coordinates
    need_image = pyqtSignal(str)
    _mutex = QMutex()
    x_data: npt.NDArray
    y_data: npt.NDArray
    xlabel_type: str
    ylabel_type: str
    analysis_path: str
    wl: int
    bl: int
    lang_pack: dict

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.image_saved = False # рисунок создан и сохранен на диск
        _, self.lang_pack = self.parent.parent.read_language_json("testing")

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
        # TODO: Add current in uA as ylabel type
        # создаем папку
        now = datetime.datetime.now()
        formatted_date = now.strftime("%d.%m.%Y_%H.%M.%S")
        self.analysis_path = f'images_{formatted_date}'
        os.mkdir(os.path.join(self.parent.result_path, self.analysis_path))
        # настраиваем оси
        self.xlabel_type = self.parent.ui.combo_xlabel.currentText()
        if self.xlabel_type == self.lang_pack.get("voltage"):
            x_axes_type = 'vol'
        elif self.xlabel_type == self.lang_pack.get("counting"):
            x_axes_type = 'count'
        else:
            x_axes_type = 'count'
        self.ylabel_type = self.parent.ui.combo_ylabel.currentText()
        if self.ylabel_type == self.lang_pack.get("resistance"):
            y_axes_type = 'res'
        elif self.ylabel_type == self.lang_pack.get("amperage"):
            y_axes_type = 'cur'
        else:
            y_axes_type = 'res'
        with open(os.path.join(self.parent.result_path, 'csv_list.txt'), 'r', encoding='utf-8') as file:
            csv_paths = file.readlines()
            count = 0
            for path in csv_paths:
                if os.path.exists(os.path.join(self.parent.result_path, path.rstrip())):
                    self.wl = int(path.split('.')[-2].split('_')[-2])
                    self.bl = int(path.split('.')[-2].split('_')[-1])
                    df = read_csv(os.path.join(self.parent.result_path, path.rstrip()), delimiter=';')
                    self.x_data = np.array(df['vol'])
                    self.y_data = np.array(df['res'])
                    if y_axes_type == 'cur':
                        self.y_data = self.x_data / self.y_data * 1000  # Converting current to mA
                    if x_axes_type == 'count':
                        self.x_data = [i+1 for i in range(len(self.x_data))]
                    # от plotly отказались из-за большого размера библиотеки
                    # fig = px.line(x=x_data, y=y_data, markers=True)
                    # fig.update_layout(xaxis_title=xlabel_type,
                    #                   yaxis_title=ylabel_type)
                    # fig.write_image(os.path.join(self.parent.result_path,
                    #                              analysis_path,
                    #                              f'{self.parent.crossbar_serial}_{wl}_{bl}.png'),
                    #                              width=640, height=480)
                    self.need_image.emit('')
                    while not self.image_saved:
                        time.sleep(0.5)
                    self.setup_image_saved(False)
                    count += 1
                    self.count_changed.emit(count)
        self.progress_finished.emit(0)
