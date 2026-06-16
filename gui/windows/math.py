"""
Окно математики
"""

# pylint: disable=E0611, I1101, C0301

import os
import csv
from copy import deepcopy
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt
from manager.service import w2r, r2w, v2d, a2v
from manager.service.converters import quantization
from gui.src import show_warning_messagebox, open_file_dialog
from gui.windows.snapshot import Snapshot

AMOUNT_RANDOM_SAMPLES = 100

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
    if array is not None:
        file_path = QFileDialog.getSaveFileName(parent,
                                                    parent.lang_pack.get('saving_dir'))[0]
        if file_path:
            try:
                path_check = file_path.split('.')
                if path_check[-1] != 'csv':
                    file_path += '.csv'
                save_array_to_csv(array, file_path)
                show_warning_messagebox(parent=parent, message=parent.lang_pack.get('saved_to') + file_path)
            except Exception: # pylint: disable=W0718
                show_warning_messagebox(parent=parent, message=parent.lang_pack.get('saving_error'))

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
    mode: str

    temp_current_weights = None
    temp_current_weights_scaled = None
    temp_goal_weights = None
    temp_input_array_source = None
    temp_matmul_crossbar_results = None
    temp_matmul_crossbar_results_scaled = None

    mask_weights = None
    current_weights = None
    current_weights_scaled = None
    goal_weights = None
    error_weights = None
    matmul_predicted_results = None
    matmul_etalon_results = None
    matmul_crossbar_results = None
    matmul_crossbar_results_scaled = None
    matmul_error_results = None
    input_array_scaled = None
    input_array_source = None
    vol_comp: int # ограничитель напряжения
    is_quintisation_on = False
    lang_pack: dict

    def __init__(self, parent=None, mode=str) -> None:
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.ui.change_language()
        # доп настройки
        self.ui.setWindowFlags(Qt.Window)
        if self.mode == "no_crossbar":
            self.ui.tabwidget_mode.setTabEnabled(1, False)
        # self.setModal(True)
        self.ui.text_voltage.setEnabled(False)
        self.ui.button_apply.setEnabled(False)
        self.ui.button_undo_quantisation.setEnabled(False)
        self.result = [] # результат умножения
        self.voltages = [] # напряжения
        # обработка кнопок
        self.ui.button_apply.clicked.connect(self.apply_math)
        self.ui.button_load_input_data.clicked.connect(self.load_file)
        self.ui.button_save_input_data.clicked.connect(self.save_voltage_file)
        self.ui.button_save_result.clicked.connect(self.save_result_file)
        self.ui.button_change_weight_cell.clicked.connect(self.set_weights)
        # обработка виджетов
        self.ui.combo_preprocess.activated.connect(self.activate_process)
        self.ui.combo_postprocess.activated.connect(self.activate_process)
        self.ui.spinbox_max_input.valueChanged.connect(self.update_all_data)
        self.ui.text_input_data.textChanged.connect(self.update_text_input_data)
        self.ui.spinbox_max_weight.valueChanged.connect(self.update_all_data)
        self.ui.spinbox_max_input.setEnabled(False)
        self.ui.spinbox_max_weight.setEnabled(False)
        self.ui.spinbox_new_weight.valueChanged.connect(self.update_label_target_resistance)
        self.ui.spinbox_correction_a.valueChanged.connect(self.update_output_with_correction)
        self.ui.spinbox_correction_b.valueChanged.connect(self.update_output_with_correction)
        self.ui.checkbox_correction.stateChanged.connect(self.update_output_with_correction)
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
        self.ui.button_heatmap_goal_weights_matrix.clicked.connect(lambda: self.show_snapshot(self.goal_weights))
        self.ui.button_histogram_goal_weights_matrix.clicked.connect(lambda: self.array_to_vector(self.goal_weights))
        self.ui.button_read_current_weights_matrix.clicked.connect(self.read_current_weights_matrix)
        self.ui.button_save_current_weights_matrix.clicked.connect(lambda: save_as_array_to_csv(self, self.current_weights))
        self.ui.button_heatmap_current_weights_matrix.clicked.connect(lambda: self.show_snapshot(self.current_weights))
        self.ui.button_histogram_current_weights_matrix.clicked.connect(lambda: self.array_to_vector(self.current_weights))
        self.ui.button_calculate_error_weights.clicked.connect(self.calculate_weights_error)
        self.ui.button_save_error_weights.clicked.connect(lambda: save_as_array_to_csv(self, self.error_weights))
        self.ui.button_heatmap_error_weights.clicked.connect(lambda: self.show_snapshot(self.error_weights))
        self.ui.button_histogram_error_weights_matrix.clicked.connect(lambda: self.array_to_vector(self.error_weights))
        self.ui.button_heatmap_mask_weights_matrix.clicked.connect(lambda: self.show_snapshot(self.mask_weights, mode='binary'))
        # кнопки работы с данными
        self.ui.input_data_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.input_data_voltage_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.etalon_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.predicted_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.result_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.error_output_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_summary_weights.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_summary_data.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.button_load_input_array_from_disk.clicked.connect(self.load_input_array_from_disk)
        self.ui.button_generate_random_input_data.clicked.connect(self.generate_random_input_data)
        self.ui.button_save_input_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.input_array_source))
        self.ui.button_save_input_voltage_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.input_array_scaled))
        self.ui.button_calculate_etalon_results.clicked.connect(self.calculate_etalon_results)
        self.ui.button_save_etalon_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.matmul_etalon_results))
        self.ui.button_predict_output_data.clicked.connect(self.predict_output_data)
        self.ui.button_save_output_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.matmul_crossbar_results))
        self.ui.button_etalon_vs_output_graph.clicked.connect(self.plot_etalon_vs_output)
        self.ui.button_calculate_matmul_errors.clicked.connect(self.calculate_matmul_error)
        self.ui.button_save_error_array_to_disk.clicked.connect(lambda: save_as_array_to_csv(self, self.matmul_error_results))
        self.ui.button_goal_weights_from_current.clicked.connect(self.copy_goal_weights_from_current)
        self.ui.button_histogram_numbers.clicked.connect(lambda: self.array_to_vector(self.input_array_source))
        self.ui.button_histogram_voltage.clicked.connect(lambda: self.array_to_vector(self.input_array_scaled))
        self.ui.button_masking.clicked.connect(self.apply_mask)
        self.ui.button_reset_mask.clicked.connect(self.reset_mask)
        self.ui.button_do_quantisation.clicked.connect(self.do_quantize)
        self.ui.button_undo_quantisation.clicked.connect(self.undo_quantize)
        self.read_current_weights_matrix()
        self.fill_table_mask_with_ones()

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("math")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.tabwidget_mode.setTabText(0, self.lang_pack.get("cell"))
            self.ui.tabwidget_mode.setTabText(1, self.lang_pack.get("crossbar"))
            self.ui.label_10.setText(self.lang_pack.get("goal"))
            self.ui.button_change_weight_cell.setText(self.lang_pack.get("set"))
            self.ui.groupBox.setTitle(self.lang_pack.get("ent_val"))
            self.ui.groupBox_2.setTitle(self.lang_pack.get("result"))
            self.ui.button_load_input_data.setText(self.lang_pack.get("upload"))
            self.ui.button_save_input_data.setText(self.lang_pack.get("save"))
            self.ui.button_save_result.setText(self.lang_pack.get("save"))
            self.ui.label.setText(self.lang_pack.get("nums"))
            self.ui.label_2.setText(self.lang_pack.get("voltages"))
            self.ui.label_input_data_status.setText(self.lang_pack.get("input_nums"))
            self.ui.groupBox_3.setTitle(self.lang_pack.get("exec"))
            self.ui.label_4.setText(self.lang_pack.get("ent_scale"))
            self.ui.label_3.setText(self.lang_pack.get("weights_scale"))
            self.ui.label_5.setText(self.lang_pack.get("prep"))
            self.ui.label_6.setText(self.lang_pack.get("post"))
            self.ui.combo_preprocess.setItemText(0, self.lang_pack.get("no"))
            self.ui.combo_postprocess.setItemText(0, self.lang_pack.get("no"))
            self.ui.button_apply.setText(self.lang_pack.get("run"))
            self.ui.horizontalGroupBox.setTitle(self.lang_pack.get("depth"))
            self.ui.label_11.setText(self.lang_pack.get("weights"))
            self.ui.label_13.setText(self.lang_pack.get("data"))
            self.ui.label_12.setText(self.lang_pack.get("results"))
            self.ui.button_do_quantisation.setText(self.lang_pack.get("quan"))
            self.ui.button_undo_quantisation.setText(self.lang_pack.get("cancel"))
            self.ui.tabWidget_4.setTabText(0, self.lang_pack.get("weights"))
            self.ui.tabWidget_4.setTabText(1, self.lang_pack.get("data"))
            self.ui.tabWidget_4.setTabText(2, self.lang_pack.get("results"))
            self.ui.tabWidget_2.setTabText(0, self.lang_pack.get("written"))
            self.ui.tabWidget_2.setTabText(1, self.lang_pack.get("mask"))
            self.ui.tabWidget_2.setTabText(2, self.lang_pack.get("goal"))
            self.ui.tabWidget_2.setTabText(3, self.lang_pack.get("mistake"))
            self.ui.tabWidget_2.setTabText(4, self.lang_pack.get("summary"))
            self.ui.tabWidget.setTabText(0, self.lang_pack.get("prediction"))
            self.ui.tabWidget.setTabText(1, self.lang_pack.get("model"))
            self.ui.tabWidget.setTabText(2, self.lang_pack.get("result"))
            self.ui.tabWidget.setTabText(3, self.lang_pack.get("mistake"))
            self.ui.tabWidget.setTabText(4, self.lang_pack.get("summary"))
            self.ui.button_read_current_weights_matrix.setText(self.lang_pack.get("read"))
            self.ui.button_save_current_weights_matrix.setText(self.lang_pack.get("save_csv"))
            self.ui.button_heatmap_current_weights_matrix.setText(self.lang_pack.get("heatmap"))
            self.ui.button_histogram_current_weights_matrix.setText(self.lang_pack.get("hist"))
            self.ui.button_masking.setText(self.lang_pack.get("masking"))
            self.ui.button_reset_mask.setText(self.lang_pack.get("reset"))
            self.ui.button_heatmap_mask_weights_matrix.setText(self.lang_pack.get("heatmap"))
            self.ui.button_goal_weights_from_current.setText(self.lang_pack.get("from_written"))
            self.ui.button_write_goal_weights_matrix.setText(self.lang_pack.get("upload"))
            self.ui.button_save_goal_weights_matrix.setText(self.lang_pack.get("save_csv"))
            self.ui.button_heatmap_goal_weights_matrix.setText(self.lang_pack.get("heatmap"))
            self.ui.button_histogram_goal_weights_matrix.setText(self.lang_pack.get("hist"))
            self.ui.button_calculate_error_weights.setText(self.lang_pack.get("calc"))
            self.ui.button_save_error_weights.setText(self.lang_pack.get("save_csv"))
            self.ui.button_heatmap_error_weights.setText(self.lang_pack.get("heatmap"))
            self.ui.button_histogram_error_weights_matrix.setText(self.lang_pack.get("hist"))
            self.ui.tabWidget_3.setTabText(0, self.lang_pack.get("nums"))
            self.ui.tabWidget_3.setTabText(1, self.lang_pack.get("voltages"))
            self.ui.tabWidget_3.setTabText(2, self.lang_pack.get("summary"))
            self.ui.button_load_input_array_from_disk.setText(self.lang_pack.get("upload"))
            self.ui.button_generate_random_input_data.setText(self.lang_pack.get("generate"))
            self.ui.label_8.setText(self.lang_pack.get("amount"))
            self.ui.label_9.setText(self.lang_pack.get("max"))
            self.ui.button_save_input_array_to_disk.setText(self.lang_pack.get("save_csv"))
            self.ui.button_histogram_numbers.setText(self.lang_pack.get("hist"))
            self.ui.button_save_input_voltage_to_disk.setText(self.lang_pack.get("save_csv"))
            self.ui.button_histogram_voltage.setText(self.lang_pack.get("hist"))
            self.ui.button_predict_output_data.setText(self.lang_pack.get("calc"))
            self.ui.button_calculate_etalon_results.setText(self.lang_pack.get("calc"))
            self.ui.button_save_etalon_array_to_disk.setText(self.lang_pack.get("save_csv"))
            self.ui.button_save_output_array_to_disk.setText(self.lang_pack.get("save_csv"))
            self.ui.button_etalon_vs_output_graph.setText(self.lang_pack.get("graph"))
            self.ui.label_7.setText(self.lang_pack.get("correction"))
            self.ui.button_calculate_matmul_errors.setText(self.lang_pack.get("calc"))
            self.ui.button_save_error_array_to_disk.setText(self.lang_pack.get("save_csv"))

    def update_label_weight_info(self):
        """
        Данные о весах
        """
        self.ui.label_weight_info.setText("") # todo: доделать 

    def update_output_with_correction(self):
        """
        Correction
        """
        self.predict_output_data()
        self.update_output_mvm_result()
        self.calculate_matmul_error()

    def fill_table_mask_with_ones(self):
        """
        Заполнение маски единицами
        """
        self.mask_weights = np.ones_like(self.current_weights, dtype=int)
        self.fill_table(self.ui.table_mask,
                        self.mask_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)

    def copy_goal_weights_from_current(self):
        """
        Копировать в целевые текущие веса
        """
        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.goal_weights = deepcopy(self.current_weights_scaled)
        elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
            self.goal_weights = deepcopy(self.current_weights)
        self.fill_table(self.table_goal_weights,
                            self.goal_weights,
                            self.parent.man.row_num,
                            self.parent.man.col_num)
        # обновление сводки
        self.update_summary_weights()

    def activate_spinboxes(self):
        """
        Активация спинбоксов
        """
        if self.ui.combo_preprocess.currentText() == 'scaling' or self.ui.combo_postprocess.currentText() == 'scaling':
            self.ui.spinbox_max_input.setEnabled(True)
            self.ui.spinbox_max_weight.setEnabled(True)
        else:
            self.ui.spinbox_max_input.setEnabled(False)
            self.ui.spinbox_max_weight.setEnabled(False)

    def activate_process(self):
        """
        Нужен препроцесс
        """
        self.activate_spinboxes()
        # Обновить входы и расчетные веса
        self.update_all_data()
        if type(self.mask_weights) is list:
            self.masking()

## кнопки работы с весами

    def on_weights_written(self, goal_weights, weights_correction):
        """
        Запись целевых весов в табличку интерфейса
        """
        if goal_weights:
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
            self.ui.spinbox_max_weight.setValue(weights_correction)
        self.read_current_weights_matrix()

    def button_write_weights_matrix_clicked(self):
        """
        Запись весов
        """
        self.parent.show_new_ann_dialog(mode='matmul')

    def read_current_weights_matrix(self):
        """
        Чтение текущих весов
        """
        self.current_weights = deepcopy(self.empty_table)
        self.current_weights_scaled = deepcopy(self.empty_table)
        for i in range(self.parent.man.row_num):
            for j in range(self.parent.man.col_num):
                self.current_weights_scaled[i][j] = round(self.parent.man.sum_gain/self.parent.all_resistances[i][j], 4) * float(self.ui.spinbox_max_weight.value())
                self.current_weights[i][j] = round(self.parent.man.sum_gain/self.parent.all_resistances[i][j], 4)
        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.fill_table(self.table_real_weights,
                        self.current_weights_scaled,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
            self.fill_table(self.table_real_weights,
                        self.current_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        # обновление сводки
        self.update_summary_weights()

    def calculate_weights_error(self):
        """
        Посчитать ошибку
        """
        if self.goal_weights is not None:
            if self.ui.combo_preprocess.currentText() == 'scaling':
                self.error_weights = np.abs(self.goal_weights - self.current_weights_scaled)
            elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
                self.error_weights = np.abs(self.goal_weights - self.current_weights)
            self.fill_table(self.table_weights_errors,
                            self.error_weights,
                            self.parent.man.row_num,
                            self.parent.man.col_num)
        # обновить сводку
        self.update_summary_weights()
            
    def array_to_vector(self, array):
        """
        Преобразовывать массив в вектор и строить для него гистограмму
        """
        if array is not None:
            vector = np.array(array).flatten("F")
            plt.hist(vector)
            plt.show()

    def get_max_min(self, list):
        """
        Нахождение максимума, минимума из списка
        """
        min = list[0][0]
        max = list[0][0]
        k = 0
        for i in range(len(list)):
            for j in range(len(list[0])):
                k = list[i][j]
                if k < min:
                    min = k
                if k > max:
                    max = k
        return(max, min)

    def update_summary_weights(self):
        """
        Обновление сводки весов
        """
        data = []
        data.append(['', self.lang_pack.get("minimum"), self.lang_pack.get("maximum")])
        rows = 1
        max = None
        min = None
        if self.current_weights is not None:
            if self.ui.combo_postprocess.currentText() == 'scaling':
                max, min = self.get_max_min(self.current_weights_scaled)
            elif self.ui.combo_postprocess.currentText() == self.lang_pack.get("no"):
                max, min = self.get_max_min(self.current_weights)
            data.append([self.lang_pack.get("written") + ':', str(min), str(max)])
            rows += 1
        if self.goal_weights is not None:
            max, min = self.get_max_min(self.goal_weights)
            data.append([self.lang_pack.get("goal") + ':', str(min), str(max)])
            rows += 1
        if self.error_weights is not None:
            max, min = self.get_max_min(self.error_weights)
            data.append([self.lang_pack.get("mistake") + ':', str(min), str(max)])
            rows += 1
        if min is not None or max is not None:
            self.ui.table_summary_weights.setRowCount(rows)
            self.ui.table_summary_weights.setColumnCount(3)
            # заполнение данными
            for i in range(rows):
                for j in range(3):
                    self.ui.table_summary_weights.setItem(i,j, QTableWidgetItem(data[i][j],4))
            self.ui.table_summary_weights.setHorizontalHeaderLabels([str(i) for i in range(3)])
            self.ui.table_summary_weights.setVerticalHeaderLabels([str(i) for i in range(rows)])

    def update_summary_data(self):
        """
        Обновление сводки данных
        """
        data = []
        data.append(['', self.lang_pack.get("minimum"), self.lang_pack.get("maximum")])
        rows = 1
        max = None
        min = None
        if self.input_array_source is not None:
            max, min = self.get_max_min(self.input_array_source)
            data.append([self.lang_pack.get("nums") + ":", str(round(min, 4)), str(round(max, 4))])
            rows += 1
        if self.input_array_scaled is not None:
            max, min = self.get_max_min(self.input_array_scaled)
            data.append([self.lang_pack.get("voltages") + ":", str(round(min, 4)), str(round(max, 4))])
            rows += 1
        if min is not None or max is not None:
            self.ui.table_summary_data.setRowCount(rows)
            self.ui.table_summary_data.setColumnCount(3)
            # заполнение данными
            for i in range(rows):
                for j in range(3):
                    self.ui.table_summary_data.setItem(i,j, QTableWidgetItem(data[i][j],4))
            self.ui.table_summary_data.setHorizontalHeaderLabels([str(i) for i in range(3)])
            self.ui.table_summary_data.setVerticalHeaderLabels([str(i) for i in range(rows)])

## кнопки работы с данными
    def load_input_array_from_disk(self):
        """
        Загрузить входные данные (массив) с диска
        """
        file_path = open_file_dialog(self, file_types="CSV Files (*.csv)")
        if file_path:
            try:
                # загружаем
                self.input_array_source = read_csv_to_array(file_path)
                self.input_array_source, _ = adjust_columns(self.input_array_source, self.parent.man.row_num)
                # проверка на нули
                zeros = False
                for i in range(len(self.input_array_source)):
                    if zeros:
                        break
                    for j in range(len(self.input_array_source[0])):
                        if self.input_array_source[i][j] < 0:
                            zeros = True
                            break                            
                if zeros:
                    show_warning_messagebox(parent=self, message=self.lang_pack.get("neg_nums"))
                    for i in range(len(self.input_array_source)):
                        for j in range(len(self.input_array_source[0])):
                            self.input_array_source[i][j] = abs(self.input_array_source[i][j])
                self.update_voltages_array()
                self.update_summary_data() # обновление сводки
            except Exception as ex: # pylint: disable=W0718
                show_warning_messagebox(parent=self, message=self.lang_pack.get("incorrect_file") + ex)

    def generate_random_input_data(self):
        """
        Сгенерировать случайные входные данные
        """
        self.input_array_source = np.random.uniform(0, self.ui.spinbox_max.value(), size=(self.ui.spinbox_amount.value(), self.parent.man.row_num))
        #self.input_array_source[:,16:] = 0
        self.update_voltages_array()
        self.update_summary_data() # обновление сводки

    def calculate_etalon_results(self):
        """
        Посчитать результат матричного умножения (эталон)
        """
        if (self.input_array_source is not None) and (self.goal_weights is not None):
            self.matmul_etalon_results = self.input_array_source @ self.goal_weights
            print(self.matmul_etalon_results)
            self.fill_table(self.ui.etalon_output_table,
                            self.matmul_etalon_results,
                            self.matmul_etalon_results.shape[0],
                            self.matmul_etalon_results.shape[1])
            self.ui.button_apply.setEnabled(True)

    def predict_output_data(self):
        """
        Прогноз результата с текущими весами
        """
        if self.input_array_scaled is not None:
            self.matmul_predicted_results = self.input_array_scaled @ self.current_weights
            self.fill_table(self.ui.predicted_output_table,
                            self.matmul_predicted_results,
                            self.matmul_predicted_results.shape[0],
                            self.matmul_predicted_results.shape[1])
            self.ui.button_apply.setEnabled(True)

    def plot_etalon_vs_output(self):
        """
        График эталона и ошибок матричного умножения
        """
        if (self.matmul_etalon_results is not None) and (self.matmul_crossbar_results is not None):
            plt.clf()
            # correction_a = 1
            # correction_b = 0
            # if self.ui.checkbox_correction.isChecked():
            #     correction_a = self.ui.spinbox_correction_a.value()
            #     correction_b = self.ui.spinbox_correction_b.value()
            source_flatten = self.matmul_etalon_results.flatten()
            # if self.ui.combo_postprocess.currentText() == 'scaling':
            #     target_flatten = self.matmul_crossbar_results.flatten() * correction * float(self.ui.spinbox_max_input.value()) * float(self.ui.spinbox_max_weight.value())
            # elif self.ui.combo_postprocess.currentText() == 'нет':
            #     target_flatten = self.matmul_crossbar_results.flatten() * correction
            target_flatten = self.matmul_crossbar_results_scaled.flatten()
            indices = np.argsort(source_flatten)
            
            plt.plot(source_flatten[indices], target_flatten[indices], 'o', label='real')
            plt.plot(source_flatten[indices], source_flatten[indices], label='etalon')
            
            plt.xlabel('MatMul results')
            plt.ylabel('MatMul results')
            plt.legend()
            plt.grid(True, linestyle='--', linewidth=0.5)
            plt.show()

    def calculate_matmul_error(self):
        """
        Посчитать ошибку умножения
        """
        if self.matmul_crossbar_results is not None:
            if self.ui.combo_postprocess.currentText() == 'scaling':
                self.matmul_error_results = self.matmul_etalon_results - self.matmul_crossbar_results_scaled
            elif self.ui.combo_postprocess.currentText() == self.lang_pack.get("no"):
                # correction_a = 1
                # correction_b = 0
                # if self.ui.checkbox_correction.isChecked():
                #     correction_a = self.ui.spinbox_correction_a.value()
                #     correction_b = self.ui.spinbox_correction_b.value()
                self.matmul_error_results = self.matmul_etalon_results - self.matmul_crossbar_results_scaled # (self.matmul_crossbar_results * correction_a + correction_b)
            self.fill_table(self.ui.error_output_table,
                            self.matmul_error_results,
                            self.matmul_error_results.shape[0],
                            self.matmul_error_results.shape[1])

    def fill_table(self, table, data, row_count, column_count):
        """
        Заполнить таблицу
        """
        table.setRowCount(row_count)
        table.setColumnCount(column_count)
        # заполнение данными
        for i in range(row_count):
            for j in range(column_count):
                table.setItem(i,j, QTableWidgetItem(str(round(data[i][j],8))))
        table.setHorizontalHeaderLabels([str(i) for i in range(column_count)])
        table.setVerticalHeaderLabels([str(i) for i in range(row_count)])

    def set_weights(self):
        """
        Задать веса
        """
        self.parent.show_exp_settings_dialog()

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
        except Exception: # pylint: disable=W0718
            show_warning_messagebox(parent=self, message=self.lang_pack.get("incorrect_file"))

    def update_all_data(self):
        """
        Обновить все данные
        """
        if self.tabwidget_mode.currentIndex() == 0:
            # preprocess
            self.update_text_input_data()
            self.update_label_cell_info()
            self.update_label_target_resistance()
            # postprocess
            self.fill_output_data()
        elif self.tabwidget_mode.currentIndex() == 1:
            # preprocess
            self.update_voltages_array()
            self.read_current_weights_matrix()
            self.calculate_weights_error()
            # postprocess
            self.predict_output_data()
            self.update_output_mvm_result()
            self.calculate_matmul_error()
            if type(self.mask_weights) is list:
                self.masking()

    def update_voltages_array(self):
        """
        Обновить массив напряжений
        """
        if self.input_array_source is not None:
            if self.ui.combo_preprocess.currentText() == 'scaling':
                self.input_array_scaled = deepcopy(self.input_array_source) / self.ui.spinbox_max_input.value()
            elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
                self.input_array_scaled = deepcopy(self.input_array_source)
            # отображаем
            self.fill_table(self.ui.input_data_table,
                            self.input_array_source,
                            self.input_array_source.shape[0],
                            self.input_array_source.shape[1])
            self.fill_table(self.ui.input_data_voltage_table,
                            self.input_array_scaled,
                            self.input_array_scaled.shape[0],
                            self.input_array_scaled.shape[1])

    def update_text_input_data(self):
        """
        Изменение поля входных данных
        """
        try:
            inp_text = self.ui.text_input_data.toPlainText()
            inp_data = inp_text.split('\n')
            try:
                inp_data = list(filter(lambda a: a != '', inp_data))
            except Exception: # pylint: disable=W0718
                pass
            inp_data = list(map(float, inp_data))
            self.voltages = []
            self.ui.text_voltage.clear()
            # 1 Предобработка
            if self.ui.combo_preprocess.currentText() == 'scaling':
                for val in inp_data:
                    self.voltages.append(round(val/float(self.ui.spinbox_max_input.value()),4))
            elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
                for val in inp_data:
                    self.voltages.append(val)
            # заполнение текста
            text = ''
            for vol in self.voltages:
                text += str(vol).replace('.',',') + '\n'
            self.ui.text_voltage.appendPlainText(text)
            self.ui.label_input_data_status.setText(str(len(self.voltages)) + self.lang_pack.get("vals_inputed"))
            self.ui.button_apply.setEnabled(True)
            if len(self.voltages) == 0:
                self.ui.label_input_data_status.setText(self.lang_pack.get("input_nums"))
                self.ui.button_apply.setEnabled(False)
        except ValueError:
            self.ui.label_input_data_status.setText(self.lang_pack.get("incorrect"))
            self.ui.button_apply.setEnabled(False)
        except ZeroDivisionError:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("max_unset"))
            self.ui.button_apply.setEnabled(False)

    def update_label_cell_info(self):
        """
        Обновить лейбл информации о ячейке
        """
        try:
            wl = self.parent.current_wl
            bl = self.parent.current_bl
            res = self.parent.current_last_resistance
            weight = 0
            if self.ui.combo_preprocess.currentText() == 'scaling':
                weight = round(r2w(self.parent.man.res_load, int(self.parent.current_last_resistance))*float(self.ui.spinbox_max_weight.value()), 4)
            elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
                weight = round(r2w(self.parent.man.res_load, int(self.parent.current_last_resistance)), 4)
            self.ui.label_cell_info.setText(f"WL={wl}, BL={bl}, R={res}," + self.lang_pack.get("cur_val") + str(weight))
        except ZeroDivisionError:
            pass

    def update_label_target_resistance(self):
        """
        Обновить значение сопротивления
        """
        try:
            res = 0
            if self.ui.combo_preprocess.currentText() == 'scaling':
                res = w2r(self.parent.man.res_load, self.ui.spinbox_new_weight.value()/self.ui.spinbox_max_weight.value())
            elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
                res = w2r(self.parent.man.res_load, self.ui.spinbox_new_weight.value())
            self.ui.label_target_resistance.setText(f"R={res}" + self.lang_pack.get("ohm"))
        except ZeroDivisionError:
            pass

    def apply_mask(self):
        """
        Применение маски с выбором
        """
        self.get_mask_file()
        self.masking()

    def get_mask_file(self):
        """
        Получить маску из файла
        """
        # если есть файл в настройках
        is_correct = False
        if self.parent.man.get_meta_info()["writable_cells"] != '':
            is_correct, cells = self.parent.is_writable_cells_file_correct(None)
        else:   # выбрать файл вручную
            file_path = open_file_dialog(self, file_types="CSV Files (*.csv)")
            is_correct, cells = self.parent.is_writable_cells_file_correct(file_path)
        
        if is_correct:
            self.mask_weights = [[0 for j in range(self.parent.man.col_num)] for i in range(self.parent.man.row_num)]
            for i in range(len(cells)):
                self.mask_weights[int(cells[i][1])][int(cells[i][0])] = 1

    def masking(self):
        """
        Маскировать
        """
        # применение маски
        # заполнение таблицы маски
        self.fill_table(self.ui.table_mask,
                        self.mask_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        # бэкапы весов
        self.temp_current_weights = deepcopy(self.current_weights)
        self.temp_current_weights_scaled = deepcopy(self.current_weights_scaled)
        self.temp_goal_weights = deepcopy(self.goal_weights)

        # маскировка весов
        for i in range(len(self.mask_weights)):
            for j in range(len(self.mask_weights[0])):
                if len(self.current_weights) != 0:
                    self.current_weights[i][j] = self.current_weights[i][j] * self.mask_weights[i][j]
                if len(self.current_weights_scaled) != 0:
                    self.current_weights_scaled[i][j] = self.current_weights_scaled[i][j] * self.mask_weights[i][j]
                if np.any(self.goal_weights):
                    self.goal_weights[i][j] = self.current_weights[i][j] * self.mask_weights[i][j]

        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.fill_table(self.table_real_weights,
                        self.current_weights_scaled,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
            self.fill_table(self.table_real_weights,
                        self.current_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        if np.any(self.goal_weights):
            self.fill_table(self.ui.table_goal_weights,
                                self.goal_weights,
                                self.parent.man.row_num,
                                self.parent.man.col_num)
        # обновление сводки
        self.update_summary_weights()
            
    def reset_mask(self):
        """
        Сбросить маску
        """

        self.fill_table_mask_with_ones()
        if np.any(self.temp_current_weights):
            self.current_weights = deepcopy(self.temp_current_weights)
            self.current_weights_scaled = deepcopy(self.temp_current_weights_scaled)
            self.goal_weights = deepcopy(self.temp_goal_weights)
            self.temp_current_weights = None
            self.temp_current_weights_scaled = None
            self.temp_goal_weights = None

        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.fill_table(self.table_real_weights,
                        self.current_weights_scaled,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        elif self.ui.combo_preprocess.currentText() == self.lang_pack.get("no"):
            self.fill_table(self.table_real_weights,
                        self.current_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        if np.any(self.goal_weights):
            self.fill_table(self.ui.table_goal_weights,
                                self.goal_weights,
                                self.parent.man.row_num,
                                self.parent.man.col_num)
        # обновление сводки
        self.update_summary_weights()

    def do_quantize(self):
        """
        Квантизация
        """
        # получение значений из спинбоксов
        weights_int = int(self.ui.spinbox_weights.value())
        data_int = int(self.ui.spinbox_data.value())

        # сохранение матриц
        self.temp_current_weights = deepcopy(self.current_weights)
        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.temp_current_weights_scaled = deepcopy(self.current_weights_scaled)
        if self.goal_weights is not None:
            self.temp_goal_weights = deepcopy(self.goal_weights)
        if self.input_array_source is not None:
            self.temp_input_appay_source = deepcopy(self.input_array_source)

        # применение квантизации
        self.current_weights = quantization(data = self.current_weights, bit_depth = weights_int, states = 4)
        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.current_weights_scaled = quantization(data = self.current_weights_scaled, bit_depth = weights_int, states = 4)
        if self.goal_weights is not None:
            self.goal_weights = quantization(data = self.goal_weights, bit_depth = weights_int, states = 4)
        if self.input_array_source is not None:
            self.input_array_source = quantization(data = self.input_array_source, bit_depth = data_int, states = 8)

        # запись в таблицы
        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.fill_table(self.table_real_weights,
                            self.current_weights_scaled,
                            self.parent.man.row_num,
                            self.parent.man.col_num)
        else:
            self.fill_table(self.table_real_weights,
                        self.current_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        if self.goal_weights is not None:
            self.fill_table(self.ui.table_goal_weights,
                                self.goal_weights,
                                self.parent.man.row_num,
                                self.parent.man.col_num)
        if self.input_array_source is not None:
            self.fill_table(self.ui.input_data_table,
                                self.input_array_source,
                                self.input_array_source.shape[0],
                                self.input_array_source.shape[1])

        self.is_quintisation_on = True
        self.ui.button_do_quantisation.setEnabled(False)
        self.ui.button_undo_quantisation.setEnabled(True)

    def undo_quantize(self):
        """
        Деквантизация
        """
        # восстановление матриц
        self.current_weights = deepcopy(self.temp_current_weights)
        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.current_weights_scaled = deepcopy(self.temp_current_weights_scaled)
        if self.temp_goal_weights is not None:
            self.goal_weights = deepcopy(self.temp_goal_weights)
        if self.temp_input_array_source is not None:
            self.input_appay_source = deepcopy(self.temp_input_array_source)
        if self.is_quintisation_on:
            if self.ui.combo_postprocess.currentText() == 'scaling' and self.temp_matmul_crossbar_results_scaled is not None:
                    self.matmul_crossbar_results_scaled = deepcopy(self.temp_matmul_crossbar_results_scaled)
            else:
                if self.temp_matmul_crossbar_results is not None:
                    self.matmul_crossbar_results = deepcopy(self.temp_matmul_crossbar_results)

        # запись в таблицы
        if self.ui.combo_preprocess.currentText() == 'scaling':
            self.fill_table(self.table_real_weights,
                            self.current_weights_scaled,
                            self.parent.man.row_num,
                            self.parent.man.col_num)
        else:
            self.fill_table(self.table_real_weights,
                        self.current_weights,
                        self.parent.man.row_num,
                        self.parent.man.col_num)
        if self.goal_weights is not None:
            self.fill_table(self.ui.table_goal_weights,
                                self.goal_weights,
                                self.parent.man.row_num,
                                self.parent.man.col_num)
        if self.input_array_source is not None:
            self.fill_table(self.ui.input_data_table,
                                self.input_array_source,
                                self.input_array_source.shape[0],
                                self.input_array_source.shape[1])
        
        if self.is_quintisation_on:
            if self.ui.combo_postprocess.currentText() == 'scaling'  and self.matmul_crossbar_results_scaled is not None:
                self.fill_table(self.ui.result_output_table,
                                self.matmul_crossbar_results_scaled,
                                self.matmul_crossbar_results_scaled.shape[0],
                                self.matmul_crossbar_results_scaled.shape[1])
            else:
                if self.matmul_crossbar_results is not None:
                    self.fill_table(self.ui.result_output_table,
                                    self.matmul_crossbar_results,
                                    self.matmul_crossbar_results.shape[0],
                                    self.matmul_crossbar_results.shape[1])
        
        self.is_quintisation_on = False
        self.ui.button_do_quantisation.setEnabled(True)
        self.ui.button_undo_quantisation.setEnabled(False)

    def set_up_init_values(self):
        """
        Init values
        """
        self.current_weights = None
        self.current_weights_scaled = None
        self.goal_weights = None
        self.error_weights = None
        self.matmul_predicted_results = None
        self.matmul_etalon_results = None
        self.matmul_crossbar_results = None
        self.matmul_crossbar_results_scaled = None
        self.matmul_error_results = None
        self.input_array_scaled = None
        self.input_array_source = None
        self.vol_comp = 3.3

    def closeEvent(self, event): # pylint: disable=C0103
        """
        Закрытие окна
        """
        self.parent.fill_table()
        self.parent.color_table()
        self.parent.opener = None
        self.parent.current_bl = None
        self.parent.current_wl = None
        self.parent.current_last_resistance = None
        if self.parent.snapshot_dialog is not None:
            self.parent.snapshot_dialog.data = self.parent.all_resistances
            self.parent.snapshot_dialog.plot_matrix()
        self.set_up_init_values()
        self.parent.showNormal()
        self.parent.math_dialog = Math
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
            self.ui.progress_bar.setMaximum(self.matmul_predicted_results.shape[0]*self.matmul_predicted_results.shape[1])
            self.vol_comp = 3.3
            if self.ui.checkbox_correction.isChecked():
                self.vol_comp *= self.ui.spinbox_correction_a.value() #todo: ??????? ЧТО ЗА!
            mult_thread = MatMul(parent=self)
            mult_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
            mult_thread.value_got.connect(self.on_value_got) # после выполнения
            mult_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
            mult_thread.start()

    def update_output_mvm_result(self):
        """
        Обновить отображение результата
        """
        if self.matmul_crossbar_results is not None:
            if self.ui.combo_postprocess.currentText() == 'scaling':
                self.matmul_crossbar_results_scaled = deepcopy(self.matmul_crossbar_results) * float(self.ui.spinbox_max_input.value()) * float(self.ui.spinbox_max_weight.value())
            elif self.ui.combo_postprocess.currentText() == self.lang_pack.get("no"):
                self.matmul_crossbar_results_scaled = deepcopy(self.matmul_crossbar_results)
            if self.ui.checkbox_correction.isChecked():
                self.matmul_crossbar_results_scaled = self.matmul_crossbar_results_scaled * self.ui.spinbox_correction_a.value() + self.ui.spinbox_correction_b.value()
            self.fill_table(self.ui.result_output_table,
                            self.matmul_crossbar_results_scaled,
                            self.matmul_crossbar_results_scaled.shape[0],
                            self.matmul_crossbar_results_scaled.shape[1])

    def on_value_got(self, value: int):
        """
        Получено значение
        """
        if self.tabwidget_mode.currentIndex() == 0:
            self.result.append(value)

    def on_count_changed(self, value: int) -> None:
        """
        Изменение счетчика вызывает обновление прогрессбара
        """
        self.ui.progress_bar.setValue(value)

    def fill_output_data(self):
        """
        Заполняем результат
        """
        result_for_show = []
        for item in self.result:
            # постобработка
            if self.ui.combo_postprocess.currentText() == 'scaling':
                result_for_show.append(a2v(self.parent.man.gain,
                                        self.parent.man.adc_bit,
                                        self.parent.man.vol_ref_adc,
                                        item) * float(self.ui.spinbox_max_input.value()) * float(self.ui.spinbox_max_weight.value()))
            elif self.ui.combo_postprocess.currentText() == self.lang_pack.get("no"):
                result_for_show.append(a2v(self.parent.man.gain,
                                        self.parent.man.adc_bit,
                                        self.parent.man.vol_ref_adc,
                                        item))
        # заполняем text
        self.ui.text_output_data.clear()
        text = ''
        for value in result_for_show:
            text += str(round(value,8)).replace('.',',') + '\n'
        self.ui.text_output_data.appendPlainText(text)

    def on_progress_finished(self, _: int) -> None:
        """
        Завершение выполнения
        """
        if self.tabwidget_mode.currentIndex() == 0:
            self.fill_output_data()
        if self.tabwidget_mode.currentIndex() == 1:
            self.update_output_mvm_result()
        if self.is_quintisation_on:
            result_int = int(self.ui.spinbox_result.value())
            if self.ui.combo_postprocess.currentText() == 'scaling':
                self.temp_matmul_crossbar_results_scaled = deepcopy(self.matmul_crossbar_results_scaled)
                self.matmul_crossbar_results_scaled = quantization(data = self.matmul_crossbar_results_scaled, bit_depth = result_int, states = 8)
                self.fill_table(self.ui.result_output_table,
                                self.matmul_crossbar_results_scaled,
                                self.matmul_crossbar_results_scaled.shape[0],
                                self.matmul_crossbar_results_scaled.shape[1])
            else:
                self.temp_matmul_crossbar_results = deepcopy(self.matmul_crossbar_results)
                self.matmul_crossbar_results = quantization(data = self.matmul_crossbar_results, bit_depth = result_int, states = 8)
                self.fill_table(self.ui.result_output_table,
                                self.matmul_crossbar_results,
                                self.matmul_crossbar_results.shape[0],
                                self.matmul_crossbar_results.shape[1])
        self.ui.progress_bar.setValue(0)
        
    def show_snapshot(self, data: list, mode: str = 'weights') -> None:
        """
        Окно со снапшотом
        """
        if self.parent.snapshot_dialog is None:
            self.parent.snapshot_dialog = Snapshot(parent=self.parent, data=data, mode=mode)
            self.parent.snapshot_dialog.show()
        else:
            session_type = os.environ.get('XDG_SESSION_TYPE')
            if session_type is not None and session_type == 'wayland':  # Workaround for wayland
                self.parent.snapshot_dialog.safe_close()
                self.show_snapshot(data, mode)
            else:
                self.parent.snapshot_dialog.data = data
                self.parent.snapshot_dialog.plot_matrix(mode=mode)
                self.parent.snapshot_dialog.activateWindow()  

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

class MatMul(QThread):
    """
    Матричное умножение
    """
    count_changed = pyqtSignal(int)
    value_got = pyqtSignal(int)
    progress_finished = pyqtSignal(int)
    mask: list

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.mask = np.array(self.parent.mask_weights).T

    def run(self):
        """
        Запуск потока умножения
        """
        #print(self.mask)
        counter = 0
        for i in range(self.parent.input_array_scaled.shape[0]): #100
            # подготавливаем семпл
            # v_dac = [0 for i in range(32)] # todo: перенести в драйвер
            v_dac = [0 for i in range(self.parent.input_array_scaled.shape[1])]
            for h in range(self.parent.input_array_scaled.shape[1]):
                if self.parent.input_array_scaled[i][h] > 0.3:
                    v_dac[h] = v2d(self.parent.parent.man.dac_bit,
                                self.parent.parent.man.vol_ref_dac,
                                0.3)
                else:
                    v_dac[h] = v2d(self.parent.parent.man.dac_bit,
                                self.parent.parent.man.vol_ref_dac,
                                self.parent.input_array_scaled[i][h])
            # проходим по всем строкам кроссбара
            for j in range(self.parent.parent.man.col_num): #8
                if self.parent.matmul_predicted_results[i][j] < self.parent.vol_comp:
                    # маскирование v_adc
                    v_dac_current = deepcopy(v_dac)
                    # наложение на v dac 8-ми разных масок
                    print(v_dac_current)
                    for z in range(self.parent.parent.man.row_num):
                        if self.mask[j][z] == 0:
                            v_dac_current[z] = 0
                    task = {'mode_flag': 10,
                            'vol': v_dac_current,
                            'id': 0,
                            'wl': j}
                    v_adc, _ = self.parent.parent.man.conn.impact(task)
                    #print(v_adc)
                else:
                    v_adc = 0
                self.parent.matmul_crossbar_results[i][j] = a2v(self.parent.parent.man.gain,
                                        self.parent.parent.man.adc_bit,
                                        self.parent.parent.man.vol_ref_adc,
                                        v_adc)
                counter += 1
                self.count_changed.emit(counter)
                self.value_got.emit(v_adc)
        self.progress_finished.emit(counter)