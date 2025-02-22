"""
Тестирование всех ячеек
"""

# pylint: disable=E0611,C0103,I1101,C0301,W0107

import re
import os
import csv
import time
import datetime
import matplotlib.pyplot as plt
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog
import numpy as np

from manager.service import a2r, d2v
from gui.src import show_warning_messagebox, open_file_dialog, show_warning_messagebox
from gui.windows.apply import ApplyExp

def load_csv_with_csv(filepath, gain, res_load, vol_read, adc_bit, vol_ref_adc, res_switches, dac_bit, vol_ref_dac):
    """
    Загрузка csv
    """
    data = []
    with open(filepath, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=';')
        header = next(csv_reader) # Получаем заголовок
        for row in csv_reader:
            data.append([d2v(dac_bit,
                             vol_ref_dac,
                             int(row[1]),
                             sign=int(row[0])),
                         a2r(gain,
                             res_load,
                             vol_read,
                             adc_bit,
                             vol_ref_adc,
                             res_switches,
                             int(row[2]))])
    return header, data

def custom_shaphop(data, title, save_flag=True, save_path=os.getcwd()):
    """
    Отображение живых мемристоров
    """
    plt.clf()
    x = np.arange(0, data.shape[1] + 1)
    y = np.arange(0, data.shape[0] + 1)
    # создаем поле
    plt.pcolormesh(x, y, data, edgecolors='k', linewidth=2)
    # Меняем цифры на оси X
    plt.xticks(x[:-1]+0.5, labels=x[:-1])
    # Меняем цифры на оси Y
    plt.yticks(y[:-1]+0.5, labels=y[:-1])
    levels = ["Нет теста", "СНС", "Рабочий", "СВС"]  # Соответствующие текстовые категории
    # настройка цветовой карты и границ
    bounds = [0, 1, 2, 3]
    # создание colorbar и замена числовых делений на текстовые
    cbar = plt.colorbar(ticks=bounds) # добавляем colorbar, сдвигая деления для корректного отображения
    def format_func(value):
        '''
        Расстановка меток
        '''
        if value == bounds[0]:
            return levels[0]
        elif value == bounds[1]:
            return levels[1]
        elif value == bounds[2]:
            return levels[2]
        elif value == bounds[3]:
            return levels[3]
        else:
            return ""
    cbar.ax.set_yticklabels([format_func(tick) for tick in cbar.get_ticks()])
    # Отображаем график
    plt.title(title, linespacing=1.5)
    plt.tight_layout()
    if save_flag:
        plt.savefig(os.path.join(save_path,"result_map.png"))
    else:
        plt.show()

class Testing(QDialog):
    """
    Тестирование всех ячеек
    """

    GUI_PATH = os.path.join("gui","uies","testing.ui")
    result_path: str
    application_status: str = 'stop'
    coordinates: list = []
    counter: int
    start_time: float
    live_memristors: list
    raw_adc_all: list
    crossbar_serial: str
    raw_data: list
    start_thread: ApplyExp
    cell_list_from_file: bool = False

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработчик нажатия
        # self.ui.button_send.clicked.connect(self.send_command)
        self.ui.button_choose_exp.clicked.connect(self.button_choose_exp_clicked)
        self.ui.button_start_exp.clicked.connect(self.button_start_exp_clicked)
        self.ui.button_choose_folder.clicked.connect(self.button_choose_folder_clicked)
        self.ui.button_reset_exp.clicked.connect(self.button_reset_exp_clicked)
        self.ui.button_result.clicked.connect(self.view_result)
        self.ui.button_choose_cells.clicked.connect(self.button_choose_cells_clicked)
        self.ui.button_graphs.clicked.connect(self.save_graph_vol_res)
        # значения по умолчанию
        self.result_path = os.getcwd()
        self.set_up_init_values()
        _, self.crossbar_serial = self.parent.man.db.get_crossbar_serial_from_id(self.parent.man.crossbar_id)

    def set_up_init_values(self):
        """
        Установить по умолчанию
        """
        self.ui.path_folder_csv.setText(self.result_path)
        #self.coordinates = []
        self.raw_data = []
        self.start_time = 0.
        self.parent.exp_list = []
        self.parent.exp_name = ''
        self.parent.exp_list_params = {}
        self.parent.exp_list_params['total_tickets'] = 0
        self.parent.exp_list_params['total_tasks'] = 0
        self.button_open_combination()
        self.ui.label_time_status.setText("Время выполнения теста: н/д")
        self.ui.label_start_time.setText("Начало выполнения теста: н/д")
        self.ui.label_result.setText("Процент годных:")

    def button_choose_cells_clicked(self):
        """
        Выбрать ячейки для эксперимента
        """
        filepath = open_file_dialog(self, file_types="CSV Files (*.csv)")
        if filepath:
            # нужно сформировать список списков
            cells = []
            message = ''
            wl_max = self.parent.man.col_num
            bl_max = self.parent.man.row_num
            try:
                with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader)  # Пропускаем заголовок
                    # Проверяем, что в заголовке есть нужные колонки.
                    if header != ['wl', 'bl']:
                        raise ValueError("Файл CSV должен иметь столбцы 'wl' и 'bl' в указанном порядке")
                    for row in reader:
                        try:
                            if len(row) > 2:
                                raise ArithmeticError("В строке больше 2-х значений")
                            else:
                                wl = int(row[0]) # Преобразуем в число
                                bl = int(row[1])
                                if wl > wl_max or bl > bl_max:
                                    raise ArithmeticError("WL или BL имеют не корректное значение")
                                if [wl, bl] not in cells: # Без дубликатов
                                    cells.append([wl, bl]) # Заполняем список
                        except (ValueError, IndexError):
                            message = f"Ошибка при преобразовании строки в числа: {row}"
                        except ArithmeticError as e:
                            message = f"Ошибка: {e}"
                        continue # переходим к следующей строке
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

    def button_choose_exp_clicked(self):
        """
        Выбрать эксперимент
        """
        self.set_up_init_values()
        self.parent.show_history_dialog(mode="all")

    def button_start_exp_clicked(self):
        """
        Старт обработки
        """
        wl = self.parent.man.col_num
        bl = self.parent.man.row_num
        self.raw_adc_all = [[[] for j in range(wl)] for i in range(bl)]
        self.application_status = 'work'
        self.start_time = time.time()
        self.update_label_start_time()
        # блочим кнопки
        self.button_work_combination()
        # список координат для теста
        if not self.cell_list_from_file:
            self.coordinates = []
            for i in range(self.parent.man.row_num):
                for j in range(self.parent.man.col_num):
                    self.coordinates.append((j,i))
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

    def on_finished_exp(self, value: int) -> None:
        """
        Закончился тест
        """
        self.ui.progress_all.setValue(0)
        self.button_open_combination()
        if value == 1:
            show_warning_messagebox(f"Все мемристоры протестированы за {round(time.time() - self.start_time,2)} сек.!")
        elif value == 2:
            show_warning_messagebox("Эксперимент прерван!")
        time.sleep(1) # чтобы всё успело сохраниться на диск
        self.application_status = 'stop'
        self.set_up_init_values()
        self.button_finish_combination()

    def on_count_changed(self, value: int) -> None:
        """
        На изменение счетчика
        """
        pass

    def on_progress_finished(self, value: str) -> None:
        """
        Завершился поток для одного мемристора
        """
        value = value.split(",")
        experiment_id = int(value[0])
        # сохранить картинку
        fname = "temp.png"
        plt.clf()
        plt.plot([i for i in range(len(self.raw_data))], list(map(lambda x: a2r(self.parent.man.gain,
                                                                                self.parent.man.res_load,
                                                                                self.parent.man.vol_read,
                                                                                self.parent.man.adc_bit,
                                                                                self.parent.man.vol_ref_adc,
                                                                                self.parent.man.res_switches,
                                                                                x[2]), self.raw_data)), 'o-')
        plt.xlabel('Отсчеты')
        plt.ylabel("Сопротивление, Ом")
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        plt.savefig(fname, dpi=100)
        with open(fname, 'rb') as file:
            img_data = file.read()
            # записываем в базу
            self.parent.man.db.update_experiment(experiment_id, 'image', img_data)
        os.remove(fname)
        # сохранение файла
        wl = int(value[3])
        bl = int(value[4])
        fname = os.path.join(self.result_path,
                             f'{self.crossbar_serial}_{self.parent.exp_name}_{wl}_{bl}.csv')
        with open(fname,'w', newline='', encoding='utf-8') as file:
            file_wr = csv.writer(file, delimiter=";")
            file_wr.writerow(['sign','dac','adc','res'])
            for _, item in enumerate(self.raw_data):
                res = a2r(self.parent.man.gain,
                          self.parent.man.res_load,
                          self.parent.man.vol_read,
                          self.parent.man.adc_bit,
                          self.parent.man.vol_ref_adc,
                          self.parent.man.res_switches,
                          int(item[2])) # проверить нужно ли int
                file_wr.writerow([item[0],item[1],item[2],str(res)]) # проверить нужно ли str
        # сохранение в переменную
        self.raw_adc_all[bl][wl] = [item[2] for item in self.raw_data]
        # прогрессбар
        self.counter += 1
        self.ui.progress_all.setValue(self.counter)
        self.raw_data = []

    def on_value_got(self, value: str) -> None:
        """
        Получили значение
        """
        value = value.split(",")
        vol = int(value[2])
        sign = int(value[3])
        value = int(value[1])
        self.raw_data.append((sign,vol,value))

    def on_ticket_finished(self, value: str) -> None:
        """
        Закончился тикет
        """
        # сохраняем результат
        value = value.split(",")
        ticket_id = int(value[0])
        result_file_path = value[1]
        with open(result_file_path, 'rb') as file:
            result_data = file.read()
            # записываем в базу
            self.parent.man.db.update_ticket(ticket_id, 'result', result_data)
        os.remove(result_file_path)

    def button_reset_exp_clicked(self):
        """
        Прервать выполнение эксперимента
        """
        self.start_thread.need_stop = 1

    def button_choose_folder_clicked(self):
        """
        Выбрать папку
        """
        directory = ""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", "/")
        if directory:
            self.result_path = directory
            self.ui.path_folder_csv.setText(self.result_path)

    def button_work_combination(self):
        """
        Отображение кнопок при старте эксперимента
        """
        self.ui.button_choose_exp.setEnabled(False)
        self.ui.button_choose_cells.setEnabled(False)
        self.ui.button_start_exp.setEnabled(False)
        self.ui.button_choose_folder.setEnabled(False)
        self.ui.button_reset_exp.setEnabled(True)
        self.ui.button_result.setEnabled(False)
        #self.ui.button_graphs.setEnabled(False)

    def button_open_combination(self):
        """
        Отображение кнопок при открытии окна
        """
        self.ui.button_choose_exp.setEnabled(True)
        self.ui.button_choose_cells.setEnabled(True)
        self.ui.button_start_exp.setEnabled(False)
        self.ui.button_choose_folder.setEnabled(True)
        self.ui.button_reset_exp.setEnabled(False)
        self.ui.button_result.setEnabled(False)
        #self.ui.button_graphs.setEnabled(False)

    def button_ready_combination(self):
        """
        Отображение кнопок при готовности выполнять
        (после загрузки плана эксперимента)
        """
        self.ui.button_choose_exp.setEnabled(True)
        self.ui.button_choose_cells.setEnabled(True)
        self.ui.button_start_exp.setEnabled(True)
        self.ui.button_choose_folder.setEnabled(True)
        self.ui.button_reset_exp.setEnabled(False)
        self.ui.button_result.setEnabled(False)
        #self.ui.button_graphs.setEnabled(False)
        self.update_label_time_status()

    def button_finish_combination(self):
        """
        Отображение кнопок при открытии окна
        """
        self.ui.button_choose_exp.setEnabled(True)
        self.ui.button_choose_cells.setEnabled(True)
        self.ui.button_start_exp.setEnabled(True)
        self.ui.button_choose_folder.setEnabled(True)
        self.ui.button_reset_exp.setEnabled(False)
        self.ui.button_result.setEnabled(True)
        #self.ui.button_graphs.setEnabled(True)

    def update_label_time_status(self):
        """
        Обновить время выполнения
        """
        if self.cell_list_from_file:
            num_cells = len(self.coordinates)
        else:
            num_cells = self.parent.man.row_num * self.parent.man.col_num
        message_time = round((((self.parent.exp_list_params['total_tasks'] * num_cells) * 55) / 1000) / 60, 0) # todo: скорректировать время
        self.ui.label_time_status.setText(f"Время выполнения теста: {message_time} мин.")

    def update_label_start_time(self):
        """
        Обновить лейбл начала эксперимента
        """
        self.ui.label_start_time.setText(f"Начало выполнения теста: {time.strftime('%H:%M', time.localtime(self.start_time))}")

    def closeEvent(self, event):
        """
        Закрытие окна
        """
        if self.application_status == 'stop':
            # todo: сделать в parent функцию set_up_init_values()
            self.parent.opener = None
            self.parent.fill_table()
            self.parent.color_table()
            self.set_up_init_values()
            self.coordinates = []
            self.cell_list_from_file = False
            event.accept()
        elif self.application_status == 'work':
            show_warning_messagebox('Дождитесь или прервите!')
            event.ignore()

    def view_result(self):
        """
        Показать результат
        """
        treshhold = float(self.ui.spinbox_tresh.value())
        wl = self.parent.man.col_num
        bl = self.parent.man.row_num
        good_mem_count = 0
        LRS_mem_count = 0
        HRS_mem_count = 0
        hot_map = np.zeros((bl, wl))
        # среднее значение adc живого мемристора
        all_mean_adc = []
        for i in range(bl):
            for j in range(wl):
                try:
                    max_adc = max(self.raw_adc_all[i][j])
                    min_adc = min(self.raw_adc_all[i][j])
                    max_res = a2r(self.parent.man.gain,
                                    self.parent.man.res_load,
                                    self.parent.man.vol_read,
                                    self.parent.man.adc_bit,
                                    self.parent.man.vol_ref_adc,
                                    self.parent.man.res_switches,
                                    min_adc)
                    min_res = a2r(self.parent.man.gain,
                                    self.parent.man.res_load,
                                    self.parent.man.vol_read,
                                    self.parent.man.adc_bit,
                                    self.parent.man.vol_ref_adc,
                                    self.parent.man.res_switches,
                                    max_adc)
                    if self.cell_list_from_file:
                        if [j, i] in self.coordinates:
                            if max_res/min_res >= treshhold:
                                hot_map[i][j] = 2
                                all_mean_adc.append(np.mean(self.raw_adc_all[i][j]))
                                good_mem_count+=1
                    else:
                        if max_res/min_res >= treshhold:
                            hot_map[i][j] = 2
                            all_mean_adc.append(np.mean(self.raw_adc_all[i][j]))
                            good_mem_count+=1
                except:
                    pass
        # среднее значение  adc всех живых мемристоров
        avg_adc = np.mean(all_mean_adc)
        for i in range(bl):
            for j in range(wl):
                try:
                    if self.cell_list_from_file:
                        if [j, i] in self.coordinates:
                            if hot_map[i][j] == 0:
                                if np.mean(self.raw_adc_all[i][j]) < avg_adc:
                                    hot_map[i][j] = 3
                                    HRS_mem_count += 1
                                else:
                                    hot_map[i][j] = 1
                                    LRS_mem_count += 1
                    else:
                        if hot_map[i][j] == 0:
                            if np.mean(self.raw_adc_all[i][j]) < avg_adc:
                                hot_map[i][j] = 3
                                HRS_mem_count += 1
                            else:
                                hot_map[i][j] = 1
                                LRS_mem_count += 1
                except:
                    pass
        now = datetime.datetime.now()
        formatted_date = now.strftime("%d.%m.%Y %H:%M:%S")
        if self.cell_list_from_file:
            all_cells_count = len(self.coordinates)
        else:
            all_cells_count = wl*bl
        title = f'Серийный номер: {self.crossbar_serial}\nДата: {formatted_date}\nГодные мемристоры: {np.round(good_mem_count/all_cells_count*100,2)}%\nСНС мемристоры: {np.round(LRS_mem_count/all_cells_count*100,2)}%\nСВС мемристоры: {np.round(HRS_mem_count/all_cells_count*100,2)}%'
        custom_shaphop(hot_map, title, save_flag=True, save_path=self.result_path)
        self.ui.label_result.setText(f"Процент годных: {np.round(good_mem_count/all_cells_count*100,2)}%")

    def save_graph_vol_res(self):
        """
        График для результатов тестов ячеек
        """
        csv_name_list = os.listdir(self.result_path)
        wl = self.parent.man.col_num
        bl = self.parent.man.row_num
        _, axs = plt.subplots(bl, wl, figsize=(20*4, 20*9))
        for csv_name in csv_name_list:
            match = re.search(r'_(\d+)\.csv$', csv_name)
            if match:
                filepath = os.path.join(self.result_path, csv_name)
                _, data = load_csv_with_csv(filepath,
                                            self.parent.man.gain,
                                            self.parent.man.res_load,
                                            self.parent.man.vol_read,
                                            self.parent.man.adc_bit,
                                            self.parent.man.vol_ref_adc,
                                            self.parent.man.res_switches,
                                            self.parent.man.dac_bit,
                                            self.parent.man.vol_ref_dac)
                all_data = np.array(data)
                bl = int(csv_name.split('.')[-2].split('_')[-1])
                wl = int(csv_name.split('.')[-2].split('_')[-2])
                axs[bl,wl].plot(all_data[:,0],all_data[:,1],marker='o', linestyle='-')
                axs[bl,wl].set_title(f"BL = {bl}, WL = {wl}")
                axs[bl,wl].set_xlabel("Напряжение, В")
                axs[bl,wl].set_ylabel("Сопротивление, Ом")

        plt.tight_layout()
        plt.savefig(os.path.join(self.result_path,'rv_curve.png'), dpi=300)
