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
                    data[keys[i]].append(float(item))
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
    data_for_plot_x: list
    data_for_plot_y: list
    start_thread: ApplyExp
    cell_list_from_file: bool
    exp_time_estimated: float
    csv_names: list
    xlabel_text: str = 'Напряжение, В'
    ylabel_text: str = 'Сопротивление, Ом'
    ticket_image_name: str = "temp.png"

    def __init__(self, parent=None) -> None: # +
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
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
        self.data_for_plot_x = []
        self.data_for_plot_y = []
        self.start_time = 0.
        self.parent.exp_list = []
        self.parent.exp_name = ''
        self.parent.exp_list_params = {}
        self.parent.exp_list_params['total_tickets'] = 0
        self.parent.exp_list_params['total_tasks'] = 0
        self.button_open_combination()
        self.ui.label_all_cells_count.setText(f"Выбрано ячеек: {len(self.coordinates)}")
        self.ui.label_time_status.setText("Время выполнения теста: н/д")
        self.ui.label_start_time.setText("Начало выполнения теста: н/д")
        self.ui.label_result.setText("Процент годных: н/д")
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
                message = f"Ошибка: Файл не найден: {filepath}"
            except ValueError as e:
                message = f"Ошибка: {e}"
            except Exception as e:
                message = f"Произошла ошибка: {e}"
            if message:
                show_warning_messagebox(message)
            if cells:
                self.coordinates = cells
                self.cell_list_from_file = True
                show_warning_messagebox(f'Тест выполнится для {len(cells)} ячеек!')
            else:
                show_warning_messagebox('Тест выполнится для всех ячеек!')
                self.cell_list_from_file = False
        else:
            show_warning_messagebox('Тест выполнится для всех ячеек!')
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
        message = f'Тест для {len(self.coordinates)} ячеек, примерно займет {self.exp_time_estimated} мин.\nПродолжить?'
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
            show_warning_messagebox(f"Все мемристоры протестированы за {round(time.time() - self.start_time,2)} сек.!")
        elif stop_reason == 2:
            show_warning_messagebox("Эксперимент прерван!")
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
        data_for_plot_x = copy.deepcopy(self.data_for_plot_x)
        data_for_plot_y = copy.deepcopy(self.data_for_plot_y)
        # очищаем для потока ApplyExp
        self.raw_data = []
        self.data_for_plot_x = []
        self.data_for_plot_y = []
        # сохраняем результат в файл
        value = value.split(",")
        # сохранение файла
        wl = int(value[3])
        bl = int(value[4])
        fname = f'{self.crossbar_serial}_{self.parent.exp_name}_{wl}_{bl}.csv'
        fpath = os.path.join(self.result_path, fname)
        with open(fpath, 'w', newline='', encoding='utf-8') as file:
            file_wr = csv.writer(file, delimiter=";")
            file_wr.writerow(['sign','dac','adc','vol','res'])
            for item_index, item in enumerate(raw_data):
                file_wr.writerow([item[0],
                                  item[1],
                                  item[2],
                                  data_for_plot_x[item_index],
                                  data_for_plot_y[item_index]])
        self.csv_names.append(fname+'\n')
        # рисунок для базы в matplotlib
        plt.clf()
        plt.plot(data_for_plot_x, data_for_plot_y, marker='o', linewidth=0.5)
        plt.xlabel(self.xlabel_text)
        plt.ylabel(self.ylabel_text)
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
        self.raw_data.append((sign, dac_value, adc_value))
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
        self.exp_time_estimated = round((((self.parent.exp_list_params['total_tasks'] * num_cells) * 60) / 1000) / 60, 0) # todo: скорректировать время
        self.ui.label_time_status.setText(f"Время выполнения теста: {self.exp_time_estimated} мин.")

    def update_label_start_time(self) -> None: # +
        """
        Обновить лейбл начала эксперимента
        """
        self.ui.label_start_time.setText(f"Начало выполнения теста: {time.strftime('%H:%M', time.localtime(self.start_time))}")

    def update_label_all_cells_count(self) -> None: # +
        """
        Обновить лейбл с количеством ячеек
        """
        self.ui.label_all_cells_count.setText(f"Выбрано ячеек: {len(self.coordinates)}")

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
            show_warning_messagebox('Дождитесь или прервите!')
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
                        if mode == 'больше':
                            case_rmin = min_res > rmin
                        elif mode == 'меньше':
                            case_rmin = min_res < rmin
                    if self.ui.checkbox_rmax.isChecked():
                        mode = self.ui.combo_rmax_mode.currentText()
                        if mode == 'больше':
                            case_rmax = max_res > rmax
                        elif mode == 'меньше':
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
            analyses_path = f'analyses_{formatted_date}'
            os.mkdir(os.path.join(self.result_path, analyses_path))
            # делаем картинку
            all_tested_count = good_mem_count + bad_mem_count
            serial_label = f'Серийный номер: {self.crossbar_serial}\n'
            data_label = f'Дата: {formatted_date}\n'
            status_label = f'Процент годных: {np.round(good_mem_count/all_tested_count*100, 2)}%\n'
            all_data_label = f'Всего: {all_cells_count}, Тест: {all_tested_count} из них годных: {good_mem_count}, остальных: {bad_mem_count}'
            title = serial_label + data_label + status_label + all_data_label
            custom_shaphop(copy.deepcopy(heat_map), title, save_flag=True, save_path=os.path.join(self.result_path, analyses_path))
            self.ui.label_result.setText(f"Процент годных: {np.round(good_mem_count/all_tested_count*100, 2)}%")
            # запись csv годные
            fname = os.path.join(self.result_path, analyses_path, 'good_cells.csv')
            with open(fname,'w', newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=",")
                file_wr.writerow(['wl','bl'])
                for i in range(bl_max):
                    for j in range(wl_max):
                        if heat_map[i][j] == 2: # есть РП
                            file_wr.writerow([j, i])
            fname = os.path.join(self.result_path, analyses_path, 'bad_cells.csv')
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
        show_warning_messagebox('Картинки сгенерированы!')

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
                                    self.image_thread.analyses_path,
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
    analyses_path: str
    wl: int
    bl: int

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.image_saved = False # рисунок создан и сохранен на диск

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
        self.analyses_path = f'images_{formatted_date}'
        os.mkdir(os.path.join(self.parent.result_path, self.analyses_path))
        # настраиваем оси
        self.xlabel_type = self.parent.ui.combo_xlabel.currentText()
        if self.xlabel_type == 'напряжение, В':
            x_axes_type = 'vol'
        elif self.xlabel_type == 'отсчеты':
            x_axes_type = 'count'
        else:
            x_axes_type = 'count'
        self.ylabel_type = self.parent.ui.combo_ylabel.currentText()
        if self.ylabel_type == 'сопротивление, Ом':
            y_axes_type = 'res'
        elif self.ylabel_type == 'ток, мА':
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
                    #                              analyses_path,
                    #                              f'{self.parent.crossbar_serial}_{wl}_{bl}.png'),
                    #                              width=640, height=480)
                    self.need_image.emit('')
                    while not self.image_saved:
                        time.sleep(0.5)
                    self.setup_image_saved(False)
                    count += 1
                    self.count_changed.emit(count)
        self.progress_finished.emit(0)
