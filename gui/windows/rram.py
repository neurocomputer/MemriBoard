"""
Окно работы с rram
"""

# pylint: disable=E0611

import os
import pickle
from copy import deepcopy
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QAbstractItemView, QWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import matplotlib.pyplot as plt
from gui.src import show_warning_messagebox, show_choose_window
from gui.windows.apply import ApplyExp
from gui.windows.snapshot import Snapshot
from manager.service import a2r

def save_binary_string_to_file(binary_str: str, filename: str) -> None:
    """
    Сохранение бинарного файла с данными из RRAM
    """
    # Преобразуем строку из '0' и '1' в байты
    byte_array = bytearray()
    for i in range(0, len(binary_str), 8):
        byte_chunk = binary_str[i:i+8]
        # Дополняем последний байт нулями справа, если необходимо
        byte_chunk = byte_chunk.ljust(8, '0')
        byte_value = int(byte_chunk, 2)
        byte_array.append(byte_value)
    # Записываем байты в файл
    with open(filename, 'wb') as file:
        file.write(byte_array)

def ascii_to_binary(text: str) -> str:
    """
    ASCII в бинарный
    """
    binary_str = ""
    for char in text:
        # Получаем ASCII-код символа (0-255)
        ascii_code = ord(char)
        # Переводим в 8-битный двоичный формат (дополняем нулями слева)
        binary_char = bin(ascii_code)[2:].zfill(8)
        binary_str += binary_char
    return binary_str

class Rram(QWidget):
    """
    Работа с rram
    """

    GUI_PATH = os.path.join("gui","uies","rram.ui")
    experiment_0: tuple # параметры эксперимена для записи 0
    experiment_1: tuple # параметры эксперимена для записи 0
    binary: str # бинарная последовательность для записи в rram
    coordinates: list # список пар координат для записи
    counter: int # счетчик выполнения операций записи
    ticket_image_name: str # название временного файла с картинкой записи
    data_for_plot_y: list # список значений для отрисовки картинки для БД
    xlabel_text: str # подпись оси Х
    ylabel_text: str # подпись оси Y
    ones_writable: bool # готовы писать единицы
    all_done: bool # все данные записаны
    ones_done: bool # единицы записаны
    snapshot_binary: list # данные для записи
    raw_data: list # переменная для записи результатов
    start_thread: ApplyExp

    def __init__(self, parent=None) -> None: #+
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.ui.setWindowFlags(Qt.Window)
        # значения по умолчанию
        self.set_up_init_values()
        self.ui.button_interrupt.setEnabled(False)
        self.ui.button_apply_tresh.setEnabled(False)
        self.ui.button_snapshot.setEnabled(False)
        self.ui.button_write.setEnabled(False)
        self.ui.button_clear.setEnabled(False)
        self.ui.button_save_bin.setEnabled(False)
        self.ui.text_write.clear()
        self.ui.text_read.clear()
        self.ui.list_write_bytes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.list_read_bytes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # обработчики кнопок
        self.ui.button_apply_tresh.clicked.connect(self.apply_tresh)
        self.ui.button_read.clicked.connect(lambda: self.parent.read_cell_all('rram'))
        self.ui.button_snapshot.clicked.connect(self.show_snapshot)
        self.ui.button_save_bin.clicked.connect(self.save_bin)
        self.ui.button_load.clicked.connect(self.load_text)
        self.ui.button_set_0.clicked.connect(lambda: self.set_experiment(False))
        self.ui.button_set_1.clicked.connect(lambda: self.set_experiment(True))
        self.ui.text_write.textChanged.connect(self.text_to_binary)
        self.ui.combo_write_type.currentIndexChanged.connect(self.text_to_binary)
        self.ui.button_write.clicked.connect(self.write_ones_and_zeros)
        self.ui.button_clear.clicked.connect(self.erase_all_cells)
        self.ui.button_interrupt.clicked.connect(self.interrupt)
        self.ui.combo_read_encoding.currentTextChanged.connect(self.binary_to_text)

    def set_up_init_values(self) -> None: #+
        """
        Установка значений по умолчанию
        """
        self.experiment_0 = None
        self.experiment_1 = None
        self.binary = None
        self.coordinates = []
        self.counter = 0
        self.ticket_image_name = "temp.png"
        self.data_for_plot_y = []
        self.xlabel_text = 'Отсчеты'
        self.ylabel_text = 'Сопротивление, Ом'
        self.ones_writable = False
        self.all_done = False
        self.ones_done = False
        self.snapshot_binary = None
        # параметры приложения
        self.parent.exp_list = []
        self.parent.exp_name = ''
        self.parent.exp_list_params = {}
        self.parent.exp_list_params['total_tickets'] = 0
        self.parent.exp_list_params['total_tasks'] = 0

    def set_up_init_values_exp(self): #+
        """
        Установка значений по умолчанию перед экспериментами
        """
        self.parent.exp_list = []
        self.parent.exp_name = ''
        self.parent.exp_list_params = {}
        self.parent.exp_list_params['total_tickets'] = 0
        self.parent.exp_list_params['total_tasks'] = 0
        self.coordinates = []
        self.data_for_plot_y = []
        self.counter = 0
        self.all_done = False
        self.ones_done = False

    def apply_tresh(self) -> None: #+
        """
        Применение порога после чтения данных
        """
        cols = self.parent.man.col_num
        rows = self.parent.man.row_num
        tresh = self.ui.spin_tresh_read.value()
        rram_data = deepcopy(self.parent.all_resistances)
        # подготовка для бинарного снапшота
        self.snapshot_binary = deepcopy(self.parent.all_resistances)
        for i in range(len(rram_data)):
            for j in range(len(rram_data[i])):
                if rram_data[i][j] >= tresh:
                    self.snapshot_binary[i][j] = 0
                else:
                    self.snapshot_binary[i][j] = 1
        # вывод байтов
        binary_string = "".join(str(x) for row in self.snapshot_binary for x in row)
        model = QStandardItemModel() # todo: вынести в init
        self.ui.list_read_bytes.setModel(model)
        for _ in range(rows):
            model.appendRow(QStandardItem(binary_string[:cols]))
            binary_string = binary_string[cols:]
        # активация кнопок
        self.ui.button_apply_tresh.setEnabled(True)
        self.ui.button_save_bin.setEnabled(True)
        self.ui.button_snapshot.setEnabled(True)
        # перевод в текст (по умолчанию)
        self.binary_to_text()

    def save_bin(self) -> None: #+
        """
        Дамп памяти в бинарном виде
        """
        binary_string = "".join(str(x) for row in self.snapshot_binary for x in row)
        save_file = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
        if save_file:
            save_file = os.path.join(save_file, "rram.bin")
            save_binary_string_to_file(binary_string, save_file)
            show_warning_messagebox(f'{save_file} сохранен!')

    def load_text(self) -> None: #+
        """
        Загрузка текста из файла в поле ввода
        """
        load_file, _ = QFileDialog.getOpenFileName(self,
                                                   'Открыть файл',
                                                   ".",
                                                   "Текстовые файлы (*.txt)")
        if load_file:
            with open(load_file, "r+", encoding='utf-8') as f:
                text = f.read()
                f.close()
            if text:
                self.ui.text_write.insertPlainText(text)
            else:
                show_warning_messagebox("Файл " + load_file + " пуст!")

    def text_to_binary(self) -> None:
        """
        Перевод текста в бинарный формат
        """
        text = self.ui.text_write.toPlainText()
        translation = ""
        if self.ui.combo_write_type.currentText() == "ascii":
            translation = ascii_to_binary(text)
        elif self.ui.combo_write_type.currentText() == "bits":
            translation = text
        self.ui.label_write_info.setText(f'Задано {len(translation)} бит')
        self.binary = deepcopy(translation)
        cols = self.parent.man.col_num
        rows = self.parent.man.row_num
        self.binary = self.binary[:rows*cols]
        model = QStandardItemModel()
        self.ui.list_write_bytes.setModel(model)
        for _ in range(rows):
            model.appendRow(QStandardItem(translation[:cols]))
            translation = translation[cols:]
        self.buttons_activation()

    def binary_to_text(self) -> None: #+
        """
        Перевод бинарного формата в текст
        """
        binary_string = "".join(str(x) for row in self.snapshot_binary for x in row)
        # перевод в текст
        if self.ui.combo_read_encoding.currentText() == "ascii":
            # Разбиваем на байты
            bytes_list = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
            # Переводим в ASCII
            ascii_text = ""
            for byte in bytes_list:
                decimal = int(byte, 2)
                # Заменяем непечатаемые символы
                ascii_char = chr(decimal) if 32 <= decimal <= 126 else "�"
                ascii_text += ascii_char
            self.ui.text_read.setPlainText(ascii_text)
        elif self.ui.combo_read_encoding.currentText() == "bits":
            self.ui.text_read.setPlainText(binary_string)

    def set_experiment(self, settable: bool) -> None: #+
        """
        Запись id эксперимента как 0 или 1
        """
        self.parent.show_history_dialog(mode='all')
        self.parent.history_dialog.button_choose_exp.clicked.connect( \
        lambda: double_click(self.parent.history_dialog.ui.table_history_experiments.currentRow()))
        def double_click(current_row):
            if settable:
                self.experiment_1 = self.parent.history_dialog.experiments[current_row]
                show_warning_messagebox("Эксперимент для записи 1 выбран!")
                self.ui.label_exp1_name.setText(f'{self.experiment_1[2]}')
            else:
                self.experiment_0 = self.parent.history_dialog.experiments[current_row]
                show_warning_messagebox("Эксперимент для записи 0 выбран!")
                self.ui.label_exp0_name.setText(f'{self.experiment_0[2]}')
                self.ui.button_clear.setEnabled(True)
            if self.experiment_1 is not None and self.experiment_0 is not None:
                self.ui.button_write.setEnabled(True)
            self.parent.history_dialog.close()

    def buttons_activation(self) -> None: #+
        """
        Активация/деактивация кнопок
        """
        if self.experiment_1 is not None and self.experiment_0 is not None:
            self.ui.button_write.setEnabled(True)
        else:
            self.ui.button_write.setEnabled(False)

    def write_ones_and_zeros(self) -> None:
        """
        Запись нулей и единиц по кнопке Записать
        """
        self.set_up_init_values_exp()
        message = "Будет перезаписано " + str(len(self.binary)) + " ячеек. Продолжить?"
        answer = show_choose_window(self, message)
        if answer:
            wl = self.parent.man.col_num
            bl = self.parent.man.row_num
            # записываем координаты
            index = 0
            for i in range (bl):
                for j in range (wl):
                    if len(self.binary) <= index:
                        break
                    if self.binary[index] == '0':
                        self.coordinates.append((j, i))
                    index = index + 1
            # установка выбранного эксперимента
            self.parent.exp_name = self.experiment_0[2]
            experiment_id = self.experiment_0[0]
            status, tickets = self.parent.man.db.get_tickets(experiment_id)
            if status and tickets != []:
                for ticket in tickets:
                    ticket = pickle.loads(ticket[0])
                    task_list, count = self.calculate_counts_for_ticket(self.parent.man,
                                                                        ticket.copy())
                    self.parent.exp_list_params['total_tickets'] += 1
                    self.parent.exp_list_params['total_tasks'] += count
                    self.parent.exp_list.append((ticket["name"],
                                                 ticket.copy(),
                                                 task_list.copy(),
                                                 count))
                # параметры прогресс бара
                self.counter = 0
                self.ui.bar_progress.setValue(0)
                self.ui.bar_progress.setMaximum(len(self.binary))
                # параметры потока
                self.ones_writable = True
                self.lock_buttons(False)
                self.start_thread = ApplyExp(parent=self)
                self.start_thread.count_changed.connect(self.on_count_changed)
                self.start_thread.progress_finished.connect(self.on_progress_finished)
                self.start_thread.value_got.connect(self.on_value_got)
                self.start_thread.ticket_finished.connect(self.on_ticket_finished)
                self.start_thread.finished_exp.connect(self.on_finished_exp)
                self.start_thread.start()
            else:
                show_warning_messagebox("Тикеты невозможно получить!")
                self.lock_buttons(True)

    def write_ones(self) -> None: #+
        """
        Запись единиц
        """
        self.set_up_init_values_exp()
        wl = self.parent.man.col_num
        bl = self.parent.man.row_num
        # записываем координаты
        index = 0
        for i in range (bl):
            for j in range (wl):
                if len(self.binary) <= index:
                    break
                if self.binary[index] == '1':
                    self.coordinates.append((j, i))
                index = index + 1
        # установка выбранного эксперимента
        self.parent.exp_name = self.experiment_1[2]
        experiment_id = self.experiment_1[0]
        status, tickets = self.parent.man.db.get_tickets(experiment_id)
        if status and tickets != []:
            for ticket in tickets:
                ticket = pickle.loads(ticket[0])
                task_list, count = self.calculate_counts_for_ticket(self.parent.man,
                                                                    ticket.copy())
                self.parent.exp_list_params['total_tickets'] += 1
                self.parent.exp_list_params['total_tasks'] += count
                self.parent.exp_list.append((ticket["name"],
                                             ticket.copy(),
                                             task_list.copy(),
                                             count))
            # параметры прогресс бара
            self.counter = self.binary.count("0")
            self.ui.bar_progress.setValue(self.counter)
            # параметры потока
            self.ones_done = True
            self.lock_buttons(False)
            self.start_thread.start()
        else:
            show_warning_messagebox("Тикеты невозможно получить!")
            self.lock_buttons(True)

    def erase_all_cells(self) -> None: #+
        """
        Очистка ячеек (запись нулей)
        """
        self.set_up_init_values_exp()
        wl = self.parent.man.col_num
        bl = self.parent.man.row_num
        # записываем координаты
        for i in range (bl):
            for j in range (wl):
                self.coordinates.append((j, i))
        # установка выбранного эксперимента
        self.parent.exp_name = self.experiment_0[2]
        experiment_id = self.experiment_0[0]
        status, tickets = self.parent.man.db.get_tickets(experiment_id)
        if status and tickets != []:
            for ticket in tickets:
                ticket = pickle.loads(ticket[0])
                task_list, count = self.calculate_counts_for_ticket(self.parent.man,
                                                                    ticket.copy())
                self.parent.exp_list_params['total_tickets'] += 1
                self.parent.exp_list_params['total_tasks'] += count
                self.parent.exp_list.append((ticket["name"],
                                                ticket.copy(),
                                                task_list.copy(),
                                                count))
            # параметры прогресс бара
            self.counter = 0
            self.ui.bar_progress.setValue(0)
            self.ui.bar_progress.setMaximum(len(self.coordinates))
            # параметры потока
            self.all_done = True
            self.lock_buttons(False)
            self.start_thread = ApplyExp(parent=self)
            self.start_thread.count_changed.connect(self.on_count_changed)
            self.start_thread.progress_finished.connect(self.on_progress_finished)
            self.start_thread.value_got.connect(self.on_value_got)
            self.start_thread.ticket_finished.connect(self.on_ticket_finished)
            self.start_thread.finished_exp.connect(self.on_finished_exp)
            self.start_thread.start()

    def calculate_counts_for_ticket(self, parent, ticket):
        """
        Посчитать количество задач для тикета
        """
        # получаем генератор задач
        task = parent.menu[ticket['mode']], (ticket['params'],
                                            ticket['terminate'],
                                            parent.blank_type)
        count = 0
        task_list = []
        for tsk in task[0](*task[1]):
            count += 1
            task_list.append(tsk)
        return task_list, count

    def on_ticket_finished(self, value):
        pass

    def on_count_changed(self, value):
        pass

    def on_value_got(self, value: str) -> None: # +
        """
        Получили значение
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

    def on_progress_finished(self, value: str):
        """
        Закончился поток
        """
        # чтобы успеть пока поток ApplyExp не начнет работать
        data_for_plot_y = deepcopy(self.data_for_plot_y)
        # очищаем для потока ApplyExp
        self.raw_data = []
        self.data_for_plot_y = []
        # рисунок для базы в matplotlib
        plt.clf()
        plt.plot(data_for_plot_y, marker='o', linewidth=0.5)
        plt.xlabel(self.xlabel_text)
        plt.ylabel(self.ylabel_text)
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        plt.savefig(self.ticket_image_name, dpi=100)
        plt.close()
        self.start_thread.setup_image_saved(True)
        # прогрессбар
        self.counter += 1
        self.ui.bar_progress.setValue(self.counter)

    def on_finished_exp(self, value: int) -> None: # +
        """
        Закончилась запись
        """
        value = value.split(',')
        stop_reason = int(value[0])
        if stop_reason == 1 and self.all_done:
            show_warning_messagebox("Переписано " + str(len(self.coordinates)) + " ячеек!")
        elif stop_reason == 1 and self.ones_done:
            show_warning_messagebox("Переписано " + str(len(self.binary)) + " ячеек!")
        elif stop_reason == 2:
            show_warning_messagebox("Запись прервана!")
            self.ones_writable = False
        # запись единиц
        if self.ones_writable:
            self.write_ones()
            self.ones_writable = False
        else:
            # обновление heatmap
            self.parent.fill_table()
            self.parent.color_table()
            # восстановление
            self.ui.bar_progress.setValue(0)
            self.lock_buttons(True)
            self.buttons_activation()

    def interrupt(self) -> None: #+
        """
        Прервать поток
        """
        self.start_thread.need_stop = True

    def lock_buttons(self, state: bool) -> None:
        """
        Блокировка кнопок на время записи экспериментов
        """
        self.ui.button_write.setEnabled(state)
        self.ui.button_clear.setEnabled(state)
        self.ui.button_load.setEnabled(state)
        self.ui.button_set_1.setEnabled(state)
        self.ui.button_set_0.setEnabled(state)
        self.ui.button_apply_tresh.setEnabled(state)
        self.ui.button_snapshot.setEnabled(state)
        self.ui.button_save_bin.setEnabled(state)
        self.ui.button_read.setEnabled(state)
        self.ui.button_interrupt.setEnabled(not state)
        
    def show_snapshot(self):
        """
        Окно со снапшотом
        """
        if self.parent.snapshot_dialog is None:
            self.parent.snapshot_dialog = Snapshot(self.parent, self.snapshot_binary, mode='binary')
            self.parent.snapshot_dialog.show()
        else:
            self.parent.snapshot_dialog.data = self.snapshot_binary
            self.parent.snapshot_dialog.plot_matrix(mode='binary')
            self.parent.snapshot_dialog.showNormal()
            self.parent.snapshot_dialog.activateWindow()

    def closeEvent(self, event):
        """
        Закрытие окна
        """
        self.parent.opener = None
        self.parent.showNormal()
        self.set_up_init_values()
        if self.parent.snapshot_dialog is not None:
            self.parent.snapshot_dialog.data = self.parent.all_resistances
            self.parent.snapshot_dialog.plot_matrix()
        event.accept()
