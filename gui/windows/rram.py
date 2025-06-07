"""
Окно работы с rram
"""

import os
import pickle
import shutil
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog, QAbstractItemView
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
import matplotlib.pyplot as plt
from copy import deepcopy
from gui.src import show_warning_messagebox, show_choose_window
from gui.windows.history import History
from gui.windows.apply import ApplyExp
from manager.service import a2r, d2v

class Rram(QDialog):
    """
    Работа с rram
    """

    GUI_PATH = os.path.join("gui","uies","rram.ui")
    heatmap = os.path.join("gui","uies","rram.png")
    experiment_0 = None
    experiment_1 = None
    binary = None
    coordinates = []
    counter = 0
    ticket_image_name: str = "temp.png"
    data_for_plot_x: list
    data_for_plot_y: list
    start_thread: ApplyExp
    xlabel_text: str = 'Напряжение, В'
    ylabel_text: str = 'Сопротивление, Ом'
    ones_writable: bool = False
    all_done: bool = False
    ones_done:bool = False

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # значения по умолчанию
        self.set_up_init_values()
        self.ui.button_set_0.setEnabled(False)
        self.ui.button_set_1.setEnabled(False)
        self.ui.button_interrupt.setEnabled(False)
        self.ui.button_apply_tresh.setEnabled(False)
        self.ui.button_write.setEnabled(False)
        self.ui.button_clear.setEnabled(False)
        self.ui.text_write.clear()
        self.ui.text_read.clear()
        self.parent._snapshot(mode="rram", data=self.parent.snapshot)
        self.ui.label_rram_img.setPixmap(QPixmap(self.heatmap))
        self.ui.list_write_bytes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.list_read_bytes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # обработчики кнопок
        self.ui.button_apply_tresh.clicked.connect(self.apply_tresh)
        self.ui.button_read.clicked.connect(lambda: self.parent.read_cell_all('rram'))
        self.ui.button_save_img.clicked.connect(self.save_heatmap)
        self.ui.button_save.clicked.connect(self.save_text)
        self.ui.button_load.clicked.connect(self.load_text)
        self.ui.button_set_0.clicked.connect(lambda: self.set_experiment(False))
        self.ui.button_set_1.clicked.connect(lambda: self.set_experiment(True))
        self.ui.text_write.textChanged.connect(self.text_to_binary)
        self.ui.combo_write_type.currentIndexChanged.connect(self.text_to_binary)
        self.ui.combo_read_encoding.currentIndexChanged.connect(lambda : self.ui.combo_read_encoding.setCurrentIndex(0))
        self.ui.combo_write_type.currentIndexChanged.connect(lambda : self.ui.combo_write_type.setCurrentIndex(0))
        self.ui.button_write.clicked.connect(self.write_ones_and_zeros)
        self.ui.button_clear.clicked.connect(self.erase_all_cells)
        self.ui.button_interrupt.clicked.connect(self.interrupt)

    def set_up_init_values(self) -> None:
        """
        Установка значений по умолчанию
        """
        self.coordinates = []
        self.parent.exp_list = []
        self.parent.exp_name = ''
        self.parent.exp_list_params = {}
        self.parent.exp_list_params['total_tickets'] = 0
        self.parent.exp_list_params['total_tasks'] = 0
        self.data_for_plot_x = []
        self.data_for_plot_y = []
        self.counter = 0
        self.all_done = False
        self.ones_done = False

    def apply_tresh(self) -> None:
        """
        Применение порога
        """
        tresh = self.ui.spin_tresh_read.value()
        rram_data = deepcopy(self.parent.all_resistances)
        for i in range(len(rram_data)):
            for j in range(len(rram_data[i])):
                if rram_data[i][j] >= tresh:
                    rram_data[i][j] = 1
                else:
                    rram_data[i][j] = 0
        self.parent._snapshot(mode="rram", data=rram_data)
        self.binary_to_text()

    def save_heatmap(self) -> None:
        """
        Сохранение снимка
        """
        save_path = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
        if save_path:
            save_path = os.path.join(save_path, "heatmap.png")
            shutil.copy(self.heatmap, save_path)
            show_warning_messagebox('Снимок сохранен в ' + save_path)

    def save_text(self) -> None:
        """
        Сохранение текста из поля ввода в файл
        """
        text = self.ui.text_read.toPlainText()
        if text:
            save_file = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
            if save_file:
                save_file = os.path.join(save_file, "rram.txt")
                with open(save_file, "w") as f:
                    f.write(text)
                    f.close()
                show_warning_messagebox("Сохранено в " + save_file)
        else:
            show_warning_messagebox("Нечего сохранять!")

    def load_text(self) -> None:
        """
        Загрузка текста из файла в поле ввода
        """
        load_file, _ = QFileDialog.getOpenFileName(self, 'Открыть файл', ".", "Текстовые файлы (*.txt)")
        if load_file:
            with open(load_file, "r+") as f:
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
            translation = ' '.join(format(ord(x), 'b') for x in text)
        elif self.ui.combo_write_type.currentText() == "utf-8":
            translation = ' '.join(format(x, 'b') for x in bytearray(text, 'utf-8'))
        translation = translation.replace(" ", "")
        self.binary = deepcopy(translation)
        cols = self.parent.man.col_num
        rows = self.parent.man.row_num
        self.binary = self.binary[:rows*cols]
        model = QStandardItemModel()
        self.ui.list_write_bytes.setModel(model)
        for i in range(rows):
            model.appendRow(QStandardItem(translation[:cols]))
            translation = translation[cols:]
        self.buttons_activation()

    def binary_to_text(self) -> None:
        """
        Перевод бинарного формата в текст
        """
        cols = self.parent.man.col_num
        rows = self.parent.man.row_num
        tresh = self.ui.spin_tresh_read.value()
        rram_data = deepcopy(self.parent.all_resistances)
        binary_string1 = ''.join('1' if x >= tresh else '0' for row in rram_data for x in row)
        binary_string2 = "".join(binary_string1)
        # перевод в текст
        if self.ui.combo_read_encoding.currentText() == "ascii":
            if len(binary_string1) % 8 != 0:
                extra = 8 - (len(binary_string1) % 8)
                binary_string1 = binary_string1.zfill(len(binary_string1) + extra)
            ascii_text = ""
            for i in range(0, len(binary_string1), 8):
                byte = binary_string1[i:i+8]
                decimal_value = int(byte, 2)
                ascii_text += chr(decimal_value)
            self.ui.text_read.setPlainText(ascii_text)
        elif self.ui.combo_read_encoding.currentText() == "utf-8":
            if len(binary_string1) % 8 != 0:
                extra = 8 - (len(binary_string1) % 8)
                binary_string1 = binary_string1.zfill(len(binary_string1) + extra)
            hex_string = ""
            for i in range(0, len(binary_string1), 8):
                byte = binary_string1[i:i+8]
                hex_string += hex(int(byte, 2))[2:].zfill(2) # Преобразование в шестнадцатеричную строку
            try:
                bytes_object = bytes.fromhex(hex_string)
                utf8_text = bytes_object.decode('utf-8')
                self.ui.text_read.setPlainText(utf8_text)
            except UnicodeError:
                show_warning_messagebox("Ошибка декодирования!")
        # вывод байтов
        model = QStandardItemModel()
        self.ui.list_read_bytes.setModel(model)
        for row in range(rows):
            model.appendRow(QStandardItem(binary_string2[:cols]))
            binary_string2 = binary_string2[cols:]
        # обновление heatmap, активация кнопки порога
        self.ui.label_rram_img.setPixmap(QPixmap(self.heatmap))
        self.ui.button_apply_tresh.setEnabled(True)

    def set_experiment(self, settable: bool) -> None:
        """
        Запись id эксперимента как 0 или 1
        """
        history = History(self.parent)
        history.show()
        history.ui.table_history_experiments.itemClicked.connect(lambda: history.ui.button_load.setEnabled(False))
        history.ui.table_history_experiments.itemDoubleClicked.connect(lambda: double_click(history.ui.table_history_experiments.currentRow()))
        def double_click(current_row):
            if settable:
                self.experiment_1 = history.experiments[current_row]
                show_warning_messagebox("Эксперимент для 1 записан!")
            else:
                self.experiment_0 = history.experiments[current_row]
                show_warning_messagebox("Эксперимент для 0 записан!")
                self.ui.button_clear.setEnabled(True)
            if self.experiment_1 is not None and self.experiment_0 is not None:
                self.ui.button_write.setEnabled(True)
            history.close()

    def buttons_activation(self) -> None:
        """
        Активация/деактивация кнопок
        """
        model = self.ui.list_write_bytes.model()
        if model.data(model.index(0,0)):
            self.ui.button_set_0.setEnabled(True)
            self.ui.button_set_1.setEnabled(True)
        else:
            self.ui.button_set_0.setEnabled(False)
            self.ui.button_set_1.setEnabled(False)
        if self.experiment_1 is not None and self.experiment_0 is not None:
            self.ui.button_write.setEnabled(True)
        else:
            self.ui.button_write.setEnabled(False)

    def write_ones_and_zeros(self) -> None:
        self.set_up_init_values()
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
                    task_list, count = self.calculate_counts_for_ticket(self.parent.man, ticket.copy())
                    self.parent.exp_list_params['total_tickets'] += 1
                    self.parent.exp_list_params['total_tasks'] += count
                    self.parent.exp_list.append((ticket["name"], ticket.copy(), task_list.copy(), count))
                # параметры прогресс бара
                self.counter = 0
                self.ui.bar_progress.setValue(0)
                self.ui.bar_progress.setMaximum(len(self.binary))
                # параметры потока
                self.ones_writable = True
                self.lock_buttons(False)
                self.start_thread = ApplyExp(parent=self)
                self.start_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
                self.start_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
                self.start_thread.value_got.connect(self.on_value_got) # при получении каждого измеренного
                self.start_thread.ticket_finished.connect(self.on_ticket_finished) # при получении каждого измеренного
                self.start_thread.finished_exp.connect(self.on_finished_exp) # закончился прогон
                self.start_thread.start()
            else:
                show_warning_messagebox("Тикеты невозможно получить!")
                self.lock_buttons(True)
    
    def write_ones(self) -> None:
        """
        Запись единиц
        """
        self.set_up_init_values()
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
                task_list, count = self.calculate_counts_for_ticket(self.parent.man, ticket.copy())
                self.parent.exp_list_params['total_tickets'] += 1
                self.parent.exp_list_params['total_tasks'] += count
                self.parent.exp_list.append((ticket["name"], ticket.copy(), task_list.copy(), count))
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

    def erase_all_cells(self) -> None:
        """
        Очистка ячеек (запись нулей)
        """
        self.set_up_init_values()
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
                    task_list, count = self.calculate_counts_for_ticket(self.parent.man, ticket.copy())
                    self.parent.exp_list_params['total_tickets'] += 1
                    self.parent.exp_list_params['total_tasks'] += count
                    self.parent.exp_list.append((ticket["name"], ticket.copy(), task_list.copy(), count))
            # параметры прогресс бара
            self.counter = 0
            self.ui.bar_progress.setValue(0)
            self.ui.bar_progress.setMaximum(len(self.coordinates))
            # параметры потока
            self.all_done = True
            self.lock_buttons(False)
            self.start_thread = ApplyExp(parent=self)
            self.start_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
            self.start_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
            self.start_thread.value_got.connect(self.on_value_got) # при получении каждого измеренного
            self.start_thread.ticket_finished.connect(self.on_ticket_finished) # при получении каждого измеренного
            self.start_thread.finished_exp.connect(self.on_finished_exp) # закончился прогон
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
        dac_value = int(value[2])
        sign = int(value[3])
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

    def on_progress_finished(self, value: str):
        """
        Закончился поток
        """
        # чтобы успеть пока поток ApplyExp не начнет работать
        data_for_plot_x = deepcopy(self.data_for_plot_x)
        data_for_plot_y = deepcopy(self.data_for_plot_y)
        # очищаем для потока ApplyExp
        self.raw_data = []
        self.data_for_plot_x = []
        self.data_for_plot_y = []
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
            self.parent._snapshot(mode="rram", data=deepcopy(self.parent.all_resistances))
            self.ui.label_rram_img.setPixmap(QPixmap(self.heatmap))
            # восстановление
            self.ui.bar_progress.setValue(0)
            self.lock_buttons(True)
            self.buttons_activation()

    def interrupt(self) -> None:
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
        self.ui.button_save_img.setEnabled(state)
        self.ui.button_apply_tresh.setEnabled(state)
        self.ui.button_save_img.setEnabled(state)
        self.ui.button_save.setEnabled(state)
        self.ui.button_read.setEnabled(state)
        self.ui.button_interrupt.setEnabled(not state)

    def closeEvent(self, event):
        """
        Закрытие окна
        """
        # удаление rram.png при закрытии окна
        if os.path.isfile(self.heatmap):
            os.remove(self.heatmap)
        event.accept()
