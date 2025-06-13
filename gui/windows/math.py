"""
Окно математики
"""

# pylint: disable=E0611

import os
import time
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
from manager.service import w2r, r2w, v2d, a2r, d2v, a2v
from gui.src import show_choose_window, show_warning_messagebox
import csv


class Math(QDialog):
    """
    Окно математики
    """

    GUI_PATH = os.path.join("gui","uies","math.ui")
    result: list
    voltages: list

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
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
        event.accept()

    def apply_math(self):
        """
        Выполнение умножения
        """
        self.result = []
        v_dac = []
        # генерация ЦАП
        for vol in self.voltages:
            v_dac.append(v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac, vol))
        # 3 подаем значения в плату
        self.ui.progress_bar.setMaximum(len(v_dac))
        mult_thread = MakeMult(v_dac, parent=self)
        mult_thread.count_changed.connect(self.on_count_changed) # заполнение прогрессбара
        mult_thread.value_got.connect(self.on_value_got) # после выполнения
        mult_thread.progress_finished.connect(self.on_progress_finished) # после выполнения
        mult_thread.start()

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
                result_for_show.append((a2v(self.parent.parent.man.gain,
                                            self.parent.parent.man.adc_bit,
                                            self.parent.parent.man.vol_ref_adc, 
                                            item)/0.3)*float(self.ui.spinbox_max_input.value())) #todo: вынести из GUI
            elif self.ui.combo_postprocess.currentText() == 'нет':
                result_for_show.append(a2v(self.parent.parent.man.gain,
                                            self.parent.parent.man.adc_bit,
                                            self.parent.parent.man.vol_ref_adc, 
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
