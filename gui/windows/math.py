"""
Окно математики
"""

# pylint: disable=E0611

import os
import numpy as np
import random
from copy import deepcopy
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QHeaderView, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
from manager.service import w2r, r2w, v2d, a2v
from gui.src import show_warning_messagebox, open_file_dialog, snapshot
import csv
import matplotlib.pyplot as plt

def adjust_columns(arr, col_num_max):
    """
    Подстраиваем входные данные под нужный формат
    """
    current_cols = arr.shape[1] if arr.ndim > 1 else 1
    if current_cols < col_num_max:
        # Add zero columns
        zeros_to_add = col_num_max - current_cols
        return np.pad(arr, ((0, 0), (0, zeros_to_add))), 'added'
    elif current_cols > col_num_max:
        # Remove extra columns
        return arr[:, :col_num_max], 'removed'
    else:
        # No change needed
        return arr, 'no change'

def save_array_to_csv(array, file_path):
    """
    Сохранить numpy массив в csv
    """
    np.savetxt(file_path, array, delimiter=',')

def save_as_array_to_csv(parent, array):
    """
    Сохранить массив через диалог
    """
    file_path = QFileDialog.getSaveFileName(parent,
                                                "Выберите директорию для сохранения")[0]
    if file_path:
        try:
            path_check = file_path.split('.')
            # print(path_check)
            if path_check[-1] != 'csv':
                file_path += '.csv'
            save_array_to_csv(array, file_path)
            show_warning_messagebox(f'Сохранено в {file_path}')
        except Exception as ex: # pylint: disable=W0718
            # print(ex)
            show_warning_messagebox('Ошибка сохранения!')

def read_csv_to_array(file_path):
    """
    Загрузка numpy массива с диска
    """
    return np.loadtxt(file_path, delimiter=',', dtype=float)

class Math(QWidget):
    """
    Окно математики
    """

    GUI_PATH = os.path.join("gui","uies","math.ui")
    result: list
    voltages: list
    empty_table: list

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.ui.setWindowFlags(Qt.Window)
        # self.setModal(True)
        self.ui.text_voltage.setEnabled(False)
        self.ui.button_apply.setEnabled(False)
        self.result = [] # результат умножения
        self.voltages = [] # напряжения
        # обработка кнопок
        self.ui.button_apply.clicked.connect(self.apply_math)
        self.ui.button_load_input_data.clicked.connect(self.load_file)
        self.ui.button_save_input_data.clicked.connect(self.save_voltage_file)
        self.ui.button_save_result.clicked.connect(self.save_result_file)
        self.ui.button_change_weight_cell.clicked.connect(self.set_weights)
        # обработка комбобоксов
        self.ui.combo_math_mode.activated.connect(self.combo_math_mode_activated)
        self.ui.combo_preprocess.activated.connect(self.on_text_input_data_changed)
        self.ui.combo_postprocess.activated.connect(self.fill_result_text)
        # обработка спинбоксов
        self.ui.spinbox_new_weight.valueChanged.connect(self.update_label_target_resistance)
        self.ui.spinbox_max_input.valueChanged.connect(self.on_text_input_data_changed)
        # обработка поля текста
        self.ui.text_input_data.textChanged.connect(self.on_text_input_data_changed)
        # обновление лейблов
        self.update_label_cell_info()
        self.update_label_target_resistance()
        # таблицы
        self.empty_table = np.zeros(shape=(self.parent.man.row_num, self.parent.man.col_num))
        # кнопки матричного умножения
        # кнопки работы с весами
        self.ui.table_goal_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_real_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_weights_errors.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.button_write_goal_weights_matrix.clicked.connect(self.button_write_weights_matrix_clicked)
        self.ui.button_save_goal_weights_matrix.clicked.connect(lambda: save_as_array_to_csv(self, self.goal_weights))
        self.ui.button_heatmap_goal_weights_matrix.clicked.connect(lambda: snapshot(self.goal_weights))
        self.ui.button_read_current_weights_matrix.clicked.connect(self.read_current_weights_matrix)
        self.ui.button_save_current_weights_matrix.clicked.connect(lambda: save_as_array_to_csv(self, self.current_weights))
        self.ui.button_heatmap_current_weights_matrix.clicked.connect(lambda: snapshot(self.current_weights))
        self.ui.button_calculate_error_weights.clicked.connect(self.calculate_weights_error)
        self.ui.button_save_error_weights.clicked.connect(lambda: save_as_array_to_csv(self, self.error_weights))
        self.ui.button_heatmap_error_weights.clicked.connect(lambda: snapshot(self.error_weights))
        # кнопки работы с данными
        self.ui.input_data_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.etalon_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.predicted_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.result_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.error_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.button_load_input_array_from_disk.clicked.connect(self.load_input_array_from_disk)
        self.ui.button_generate_random_input_data.clicked.connect(self.generate_random_input_data)
        self.ui.button_save_input_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.input_array))
        self.ui.button_calculate_etalon_results.clicked.connect(self.calculate_etalon_results)
        self.ui.button_save_etalon_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.matmul_etalon_results))
        self.ui.button_predict_output_data.clicked.connect(self.predict_output_data)
        self.ui.button_save_output_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.matmul_crossbar_results))
        self.ui.button_etalon_vs_output_graph.clicked.connect(self.plot_etalon_vs_output)
        self.ui.button_calculate_matmul_errors.clicked.connect(self.calculate_matmul_error)
        self.ui.button_save_error_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.matmul_error_results))

## кнопки работы с весами

    def on_weights_written(self, goal_weights):
        """
        Запись целевых весов в табличку интерфейса
        """
        # print(goal_weights)
        self.goal_weights = deepcopy(self.empty_table)
        k = 0
        for i in range(self.parent.man.row_num):
            for j in range(self.parent.man.col_num):
                self.goal_weights[i][j] = goal_weights[k]
                k += 1
        self.fill_table(self.table_goal_weights,
                        self.goal_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)

    def button_write_weights_matrix_clicked(self):
        """
        Запись весов
        """
        self.parent.show_new_ann_dialog(mode='matmul')

    def read_current_weights_matrix(self):
        """
        Чтение текущих весов
        """
        # todo: добавить чтение с платы
        self.current_weights = deepcopy(self.empty_table)
        for i in range(self.parent.man.row_num):
            for j in range(self.parent.man.col_num):
                self.current_weights[i][j] = round(self.parent.man.sum_gain/self.parent.all_resistances[i][j], 2)
        self.fill_table(self.table_real_weights,
                        self.current_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)

    def calculate_weights_error(self):
        """
        Посчитать ошибку
        """
        self.error_weights = np.abs(self.goal_weights - self.current_weights)
        self.fill_table(self.table_weights_errors,
                        self.error_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)

## кнопки работы с данными
    def load_input_array_from_disk(self):
        """
        Загрузить входные данные (массив) с диска
        """
        file_path = open_file_dialog(self, file_types="CSV Files (*.csv)")
        if file_path:
            try:
                # загружаем
                self.input_array = read_csv_to_array(file_path)
                self.input_array, _ = adjust_columns(self.input_array, self.parent.man.row_num)
                # отображаем
                self.fill_table(self.ui.input_data_table,
                                self.input_array,
                                self.input_array.shape[0],
                                self.input_array.shape[1])
            except Exception as ex: # pylint: disable=W0718
                show_warning_messagebox(f'Файл не соответствует требованиям! {ex}')

    def generate_random_input_data(self):
        """
        Сгенерировать случайные входные данные
        """
        np.random.seed(7)
        self.input_array = np.random.uniform(0, 0.3, size=(10, self.parent.man.row_num))
        self.fill_table(self.ui.input_data_table,
                        self.input_array,
                        self.input_array.shape[0],
                        self.input_array.shape[1])

    def calculate_etalon_results(self):
        """
        Посчитать результат матричного умножения (эталон)
        """
        self.matmul_etalon_results = self.input_array @ self.goal_weights
        self.fill_table(self.ui.etalon_output_table,
                        self.matmul_etalon_results,
                        self.matmul_etalon_results.shape[0],
                        self.matmul_etalon_results.shape[1])
        self.ui.button_apply.setEnabled(True)

    def predict_output_data(self):
        """
        Прогноз результата с текущими весами
        """
        self.matmul_predicted_results = self.input_array @ self.current_weights
        self.fill_table(self.ui.predicted_output_table,
                        self.matmul_predicted_results,
                        self.matmul_predicted_results.shape[0],
                        self.matmul_predicted_results.shape[1])
        self.ui.button_apply.setEnabled(True)

    def plot_etalon_vs_output(self):
        """
        График эталона и ошибок матричного умножения
        """
        plt.clf()
        plt.plot(np.sort(self.matmul_crossbar_results.flatten()),
                 np.sort(self.matmul_crossbar_results.flatten()))
        plt.show()

    def calculate_matmul_error(self):
        """
        Посчитать ошибку умножения
        """
        self.matmul_error_results = self.matmul_etalon_results - self.matmul_crossbar_results
        self.fill_table(self.ui.error_output_table,
                        self.matmul_error_results,
                        self.matmul_error_results.shape[0],
                        self.matmul_error_results.shape[1])

    def fill_table(self, table, data, row_count, column_count):
        """
        Заполнить таблицу
        """
        # row count
        table.setRowCount(row_count)
        # column count
        table.setColumnCount(column_count)
        # table will fit the screen horizontally
        # table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # table.resizeColumnsToContents()
        # заполнение весами
        for i in range(row_count):
            for j in range(column_count):
                table.setItem(i,j, QTableWidgetItem(str(round(data[i][j],4))))
        # todo: можно добавить остальные варианты для вызова из других окон
        table.setHorizontalHeaderLabels([str(i) for i in range(column_count)])
        table.setVerticalHeaderLabels([str(i) for i in range(row_count)])

    def set_weights(self):
        """
        Задать веса
        """
        mode = self.ui.combo_math_mode.currentText()
        if mode == 'ячейкой':
            self.parent.show_exp_settings_dialog()
        elif mode == 'кроссбаром':
            show_warning_messagebox('Пока не реализовано!')

    def save_result_file(self):
        """
        Сохранить файл результата
        """
        filename, _ = QFileDialog.getSaveFileName(None, "Save File", ".", "Text Files (*.csv);;All Files (*)")
        if filename:
            out_text = self.ui.text_output_data.toPlainText().replace('.',',')
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(out_text)

    def save_voltage_file(self):
        """
        Сохранение входных данных
        """
        filename, _ = QFileDialog.getSaveFileName(None, "Save File", ".", "Text Files (*.csv);;All Files (*)")
        if filename:
            inp_text = self.ui.text_input_data.toPlainText().replace('.',',')
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(inp_text)

    def load_file(self):
        """
        Загрузить файл с данными
        """
        csv_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;csv (*.csv)")#, options=options)
        try:
            if csv_path:
                self.ui.text_input_data.clear()
                with open(csv_path, encoding='utf-8') as r_file:
                    file_reader = csv.reader(r_file, delimiter = ";")
                    text = ''
                    for row in file_reader:
                        text += row[0].replace(',','.') + '\n'
                    self.ui.text_input_data.appendPlainText(text)
        except:
            show_warning_messagebox("Некорректный файл!")

    def on_text_input_data_changed(self):
        """
        Изменение поля входных данных
        """
        try:
            inp_text = self.ui.text_input_data.toPlainText()
            inp_data = inp_text.split('\n')
            try:
                inp_data = list(filter(lambda a: a != '', inp_data))
            except:
                pass
            inp_data = list(map(float, inp_data))
            self.voltages = []
            self.ui.text_voltage.clear()
            # 1 Предобработка
            if self.ui.combo_preprocess.currentText() == 'mapping':
                for val in inp_data:
                    self.voltages.append(round(val*300*0.001/float(self.ui.spinbox_max_input.value()),3)) #todo: вынести из GUI
            elif self.ui.combo_preprocess.currentText() == 'нет':
                for val in inp_data:
                    self.voltages.append(val)
            # заполнение текста
            text = ''
            for vol in self.voltages:
                text += str(vol).replace('.',',') + '\n'   
            self.ui.text_voltage.appendPlainText(text)            
            self.ui.label_input_data_status.setText(f"Введено {len(self.voltages)} значений!")
            self.ui.button_apply.setEnabled(True)
            if len(self.voltages) == 0:
                self.ui.label_input_data_status.setText("Введите по одному числу в строке!")
                self.ui.button_apply.setEnabled(False)
        except ValueError as er:
            self.ui.label_input_data_status.setText("Некорректное значение!")
            self.ui.button_apply.setEnabled(False)
        except ZeroDivisionError:
            show_warning_messagebox("Задайте максимум!")
            self.ui.button_apply.setEnabled(False)

    def combo_math_mode_activated(self):
        """
        Выбор комбобокса режима работы
        """
        mode = self.ui.combo_math_mode.currentText()
        if mode == 'ячейкой':
            self.hide_widgets_for_crossbar(True)
        elif mode == 'кроссбаром':
            self.hide_widgets_for_crossbar(False)

    def hide_widgets_for_crossbar(self, state):
        """
        Скрыть виджеты для работы с кроссбаром
        """
        self.ui.label_cell_info.setVisible(state)
        self.ui.label_10.setVisible(state)
        self.ui.spinbox_new_weight.setVisible(state)
        self.ui.label_target_resistance.setVisible(state)
        #self.adjustSize()

    def update_label_cell_info(self):
        """
        Обновить лейбл информации о ячейке
        """
        self.ui.label_cell_info.setText(f"WL={self.parent.current_wl}, BL={self.parent.current_bl}, R={self.parent.current_last_resistance}, Текущее значение={round(r2w(self.parent.man.res_load, int(self.parent.current_last_resistance)),2)}")

    def update_label_target_resistance(self):
        """
        Обновить значение сопротивления
        """
        self.ui.label_target_resistance.setText(f"R={w2r(self.parent.man.res_load, self.ui.spinbox_new_weight.value())} Ом")

    def closeEvent(self, event):
        """
        Закрытие окна
        """
        self.parent.fill_table()
        self.parent.color_table()
        self.parent.opener = None
        self.parent.current_bl = None
        self.parent.current_wl = None
        self.parent.current_last_resistance = None
        self.parent.showNormal()
        event.accept()

    def apply_math(self):
        """
        Выполнение умножения
        """
        if self.tabwidget_mode.currentIndex() == 0:
            # поэлементное умножение
            self.result = []
            v_dac = []
            # генерация ЦАП
            for vol in self.voltages:
                v_dac.append(v2d(self.parent.man.dac_bit,
                                self.parent.man.vol_ref_dac,
                                vol))
            # 3 подаем значения в плату
            self.ui.progress_bar.setMaximum(len(v_dac))
            mult_thread = MakeMult(v_dac, parent=self)
            mult_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
            mult_thread.value_got.connect(self.on_value_got) # после выполнения
            mult_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
            mult_thread.start()
        elif self.tabwidget_mode.currentIndex() == 1:
            # матричное умножение
            # цикл по семплам
            self.matmul_crossbar_results = deepcopy(self.matmul_predicted_results)
            for i in range(self.input_array.shape[0]):
                # подготавливаем семпл
                v_dac = []
                for h in range(self.input_array.shape[1]):
                    if self.input_array[i][h] > 0.3:
                        v_dac.append(v2d(self.parent.man.dac_bit,
                                    self.parent.man.vol_ref_dac,
                                    0.3))
                    else:
                        v_dac.append(v2d(self.parent.man.dac_bit,
                                    self.parent.man.vol_ref_dac,
                                    self.input_array[i][h]))
                # проходим по всем строкам кроссбара
                for j in range(self.parent.man.col_num):
                    task = {'mode_flag': 10,
                            'vol': v_dac,
                            'id': 0,
                            'wl': j}
                    # print(task)
                    # print(i, j)
                    v_adc, _ = self.parent.man.conn.impact(task)
                    self.matmul_crossbar_results[i][j] = a2v(self.parent.man.gain,
                                            self.parent.man.adc_bit,
                                            self.parent.man.vol_ref_adc,
                                            v_adc)
            # self.matmul_crossbar_results = self.input_array @ self.current_weights
            self.fill_table(self.ui.result_output_table,
                            self.matmul_crossbar_results,
                            self.matmul_crossbar_results.shape[0],
                            self.matmul_crossbar_results.shape[1])

    def on_value_got(self, value: int):
        """
        Получено значение
        """
        self.result.append(value)

    def on_count_changed(self, value: int) -> None:
        """
        Изменение счетчика вызывает обновление прогрессбара
        """
        self.ui.progress_bar.setValue(value)

    def fill_result_text(self):
        """
        Заполняем результат
        """
        result_for_show = []
        for item in self.result:
            # постобработка
            if self.ui.combo_postprocess.currentText() == 'mapping':
                result_for_show.append((a2v(self.parent.man.gain,
                                            self.parent.man.adc_bit,
                                            self.parent.man.vol_ref_adc, 
                                            item)/0.3)*float(self.ui.spinbox_max_input.value())) #todo: вынести из GUI
            elif self.ui.combo_postprocess.currentText() == 'нет':
                result_for_show.append(a2v(self.parent.man.gain,
                                            self.parent.man.adc_bit,
                                            self.parent.man.vol_ref_adc, 
                                            item))
        # заполняем text
        self.ui.text_output_data.clear()
        text = ''
        for value in result_for_show:
            text += str(round(value,3)).replace('.',',') + '\n'
        self.ui.text_output_data.appendPlainText(text)

    def on_progress_finished(self, value: int) -> None:
        """
        Завершение выполнения
        """
        self.fill_result_text()
        self.ui.progress_bar.setValue(0)

class MakeMult(QThread):
    """
    Послать одинаковый тикет на все ячейки
    """
    count_changed = pyqtSignal(int)
    value_got = pyqtSignal(int)
    progress_finished = pyqtSignal(int)

    def __init__(self, v_dac, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.v_dac = v_dac

    def run(self):
        """
        Запуск потока умножения
        """
        counter = 0
        for item in self.v_dac:
            # посылка запроса на плату
            # todo: сделать для кроссбара и единичных 8 и 9
            task = {'mode_flag': 9,
                    'vol': item,
                    'id': 0,
                    'wl': self.parent.parent.current_wl,
                    'bl': self.parent.parent.current_bl}
            v_adc, _ = self.parent.parent.man.conn.impact(task)
            # учет значения
            counter += 1
            self.count_changed.emit(counter)
            self.value_got.emit(v_adc)
        self.progress_finished.emit(counter)
