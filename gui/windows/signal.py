"""
Диалоговое окно сигнала
"""

# pylint: disable=E0611,W0401,W0611,R0903,R0915,R0912,C0301,C0103

import os
import json
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QPixmap

from manager.service.plots import plot_with_save
from manager.service import v2d, r2a, d2v, a2r
from manager.service.global_settings import TICKET_PATH
from gui.src import show_warning_messagebox, show_choose_window

class SignalMod(QDialog):
    """
    Диалоговое окно сигнала (записывает на диск тикеты)
    parent:
    man
    protected_modes
    exp_settings_dialog.ticket_files
    exp_settings_dialog.refresh_list()
    exp_settings_dialog.apply_edit_to_exp_list()
    read_ticket_from_disk()
    """

    GUI_PATH: str = os.path.join(os.getcwd(),"gui","uies","signal.ui")
    IMG_PATH: str = "ticket.png" # временный рисунок для тикета
    total_task_count: int # счетчик тасков в тикете
    one_value_terminators: list # терминаторы с одним значением
    base_json: dict # базовый тикет
    base_ticket_name: str # имя тикета (по имени файла)
    file_saved: bool # флаг сохраненности файла
    mode: str # режим запуска (create, edit)

    def __init__(self, base_ticket_name, mode, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.setModal(True)
        # обработчики кнопок
        self.ui.button_graph.clicked.connect(self._plot_ticket)
        self.ui.button_save.clicked.connect(self._save_json)
        self.ui.button_cancel.clicked.connect(self.close)
        # другие события
        self.ui.terminator_combobox.activated.connect(self._choose_terminator)
        # начальные значения
        self.set_up_init_values()
        # режим
        self.mode = mode
        # скрываем не нужные
        self._choose_terminator()
        # базовый тикет
        if self.mode == "create":
            self.base_ticket_name = base_ticket_name
            self.base_json = self.parent.read_ticket_from_disk(self.base_ticket_name+".json")
        elif self.mode == "edit":
            self.base_ticket_name = base_ticket_name["name"]
            self.base_json = base_ticket_name
        elif self.mode == "view":
            self.base_ticket_name = base_ticket_name["name"]
            self.base_json = base_ticket_name
            self.ui.button_save.setEnabled(False)
            self.ui.json_name.setEnabled(False)
        self._load_json() # загружаем blank или для редактирования

    def set_up_init_values(self) -> None:
        """
        Задать начальные значения
        """
        self.total_task_count = 0
        self.one_value_terminators = ['==', '>', '<']
        self.base_json = {}
        self.file_saved = False

    def _plot_ticket(self) -> None:
        """
        Просмотр json
        """
        if self._make_json(): # если json сделан
            json_for_plot = self.base_json.copy()
            self.total_task_count = plot_with_save(self.parent.man,
                                                   json_for_plot,
                                                   self.ui.json_plot_type.currentText(),
                                                   save_path=self.IMG_PATH)
            self._show_signal_png()
            # указываем сколько будет задач
            self.ui.label_count_tasks.setText(str(self.total_task_count))

    def _show_signal_png(self) -> None:
        """
        Отобразить png
        """
        pixmap = QPixmap(self.IMG_PATH)
        self.ui.label_png.setPixmap(pixmap)

    def _make_json(self) -> bool:
        """
        Создание json без сохранения

        Returns:
        status -- успех
        """
        status = False
        try:
            # dir inc
            self.base_json['params']['v_dir_strt_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.forward_start.text()))
            self.base_json['params']['v_dir_stop_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.forward_stop.text()))
            self.base_json['params']['v_dir_step_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.forward_step.text()))
            self.base_json['params']['t_dir_msec_inc'] = int(self.ui.forward_ms.text())
            self.base_json['params']['t_dir_usec_inc'] = int(self.ui.forward_mcs.text())
            self.base_json['params']['dir_inc_countr'] = int(self.ui.forward_count.value())
            # чекбокс dir dec
            if self.ui.forward_dec.isChecked():
                self.base_json['params']['v_dir_strt_dec'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.forward_stop.text()))
                self.base_json['params']['v_dir_stop_dec'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.forward_start.text()))
                self.base_json['params']['v_dir_step_dec'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.forward_step.text()))
                self.base_json['params']['t_dir_msec_dec'] = int(self.ui.forward_ms.text())
                self.base_json['params']['t_dir_usec_dec'] = int(self.ui.forward_mcs.text())
                self.base_json['params']['dir_dec_countr'] = int(self.ui.forward_count.value())
            else:
                self.base_json['params']['v_dir_strt_dec'] = 0
                self.base_json['params']['v_dir_stop_dec'] = 0
                self.base_json['params']['v_dir_step_dec'] = 0
                self.base_json['params']['t_dir_msec_dec'] = 0
                self.base_json['params']['t_dir_usec_dec'] = 0
                self.base_json['params']['dir_dec_countr'] = 0
            # rev inc
            self.base_json['params']['v_rev_strt_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.backward_start.text()))
            self.base_json['params']['v_rev_stop_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.backward_stop.text()))
            self.base_json['params']['v_rev_step_inc'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.backward_step.text()))
            self.base_json['params']['t_rev_msec_inc'] = int(self.ui.backward_ms.text())
            self.base_json['params']['t_rev_usec_inc'] = int(self.ui.backward_mcs.text())
            self.base_json['params']['rev_inc_countr'] = int(self.ui.backward_count.value())
            # чекбокс rev dec
            if self.ui.backward_dec.isChecked():
                self.base_json['params']['v_rev_strt_dec'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.backward_stop.text()))
                self.base_json['params']['v_rev_stop_dec'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.backward_start.text()))
                self.base_json['params']['v_rev_step_dec'] = v2d(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,float(self.ui.backward_step.text()))
                self.base_json['params']['t_rev_msec_dec'] = int(self.ui.backward_ms.text())
                self.base_json['params']['t_rev_usec_dec'] = int(self.ui.backward_mcs.text())
                self.base_json['params']['rev_dec_countr'] = int(self.ui.backward_count.value())
            else:
                self.base_json['params']['v_rev_strt_dec'] = 0
                self.base_json['params']['v_rev_stop_dec'] = 0
                self.base_json['params']['v_rev_step_dec'] = 0
                self.base_json['params']['t_rev_msec_dec'] = 0
                self.base_json['params']['t_rev_usec_dec'] = 0
                self.base_json['params']['rev_dec_countr'] = 0

            self.base_json['params']['reverse'] = int(self.ui.direction_combobox.currentIndex())
            self.base_json['params']['count'] = int(self.ui.repeat_count.text())
            self.base_json['params']['id'] = 0

            # терминаторы
            term = self.ui.terminator_combobox.currentText()
            self.base_json['terminate']['type'] = term
            if term == 'pass':
                self.base_json['terminate']['value'] = 0
            elif term in self.one_value_terminators:
                self.base_json['terminate']['value'] = r2a(self.parent.man.gain,
                                                           self.parent.man.res_load,
                                                           self.parent.man.vol_read,
                                                           self.parent.man.adc_bit,
                                                           self.parent.man.vol_ref_adc,
                                                           self.parent.man.res_switches,
                                                           int(self.ui.shutdown_value.text()))
            else:
                # сортируем
                term_values = [r2a(self.parent.man.gain,
                                   self.parent.man.res_load,
                                   self.parent.man.vol_read,
                                   self.parent.man.adc_bit,
                                   self.parent.man.vol_ref_adc,
                                   self.parent.man.res_switches,
                                   int(self.ui.shutdown_min.text())),
                               r2a(self.parent.man.gain,
                                   self.parent.man.res_load,
                                   self.parent.man.vol_read,
                                   self.parent.man.adc_bit,
                                   self.parent.man.vol_ref_adc,
                                   self.parent.man.res_switches,
                                   int(self.ui.shutdown_max.text()))]
                term_values.sort()
                self.base_json['terminate']['value'] = term_values

            status = True
        except ValueError:
            show_warning_messagebox('Не корректный символ!')
        return status

    def _save_json(self) -> None:
        """
        Сохранение json
        """
        # создать json
        answer = None
        if self._make_json():
            if self.mode == "create":
                answer = show_choose_window(self, 'Сохранить файл?')
            elif self.mode == "edit":
                answer = show_choose_window(self, 'Сохранить изменения?')
            if answer:
                try:
                    if self.mode == "create":
                        fname = self.ui.json_name.text()
                        # имя из одних пробелов
                        # todo: сменить логику на более подробную
                        if fname.replace(" ", "") == '':
                            raise ValueError
                        if fname in self.parent.protected_modes:
                            raise ValueError
                        if fname in self.parent.exp_settings_dialog.ticket_files:
                            raise ValueError
                        # открываем файл и пишем
                        self.base_json["name"] = fname
                    elif self.mode == "edit":
                        fname = 'temp'
                    with open(os.path.join(TICKET_PATH,
                                        fname+'.json'),
                                        'w', encoding='utf-8') as outfile:
                        json.dump(self.base_json, outfile)
                    self.file_saved = True
                except ValueError:
                    show_warning_messagebox('Имя файла задано не правильно!')
            if self.file_saved:
                self.close()

    def _load_json(self) -> None:
        """
        Загрузка json файла
        """

        file_name = self.base_ticket_name
        self.ui.json_name.setText(file_name)
        if self.mode == "edit":
            self.json_name.setEnabled(False)

        self.ui.forward_start.setText(str(d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.base_json['params']['v_dir_strt_inc'])))
        self.ui.forward_stop.setText(str(d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.base_json['params']['v_dir_stop_inc'])))
        self.ui.forward_step.setText(str(d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.base_json['params']['v_dir_step_inc'])))
        self.ui.forward_ms.setText(str(self.base_json['params']['t_dir_msec_inc']))
        self.ui.forward_mcs.setText(str(self.base_json['params']['t_dir_usec_inc']))
        self.ui.forward_count.setValue(self.base_json['params']['dir_inc_countr'])

        if self.base_json['params']['dir_dec_countr'] != 0:
            self.ui.forward_dec.setCheckState(2)
        else:
            self.ui.forward_dec.setCheckState(0)

        self.ui.backward_start.setText(str(d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.base_json['params']['v_rev_strt_inc'])))
        self.ui.backward_stop.setText(str(d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.base_json['params']['v_rev_stop_inc'])))
        self.ui.backward_step.setText(str(d2v(self.parent.man.dac_bit,self.parent.man.vol_ref_dac,self.base_json['params']['v_rev_step_inc'])))
        self.ui.backward_ms.setText(str(self.base_json['params']['t_rev_msec_inc']))
        self.ui.backward_mcs.setText(str(self.base_json['params']['t_rev_usec_inc']))
        self.ui.backward_count.setValue(self.base_json['params']['rev_inc_countr'])

        if self.base_json['params']['rev_dec_countr'] != 0:
            self.ui.backward_dec.setCheckState(2)
        else:
            self.ui.backward_dec.setCheckState(0)

        self.ui.direction_combobox.setCurrentIndex(self.base_json['params']['reverse'])

        # терминаторы
        self.ui.terminator_combobox.setCurrentText(self.base_json['terminate']['type'])
        self._choose_terminator()
        if self.base_json['terminate']['type'] in self.one_value_terminators:
            self.ui.shutdown_value.setText(str(int(a2r(self.parent.man.gain,
                                                       self.parent.man.res_load,
                                                       self.parent.man.vol_read,
                                                       self.parent.man.adc_bit,
                                                       self.parent.man.vol_ref_adc,
                                                       self.parent.man.res_switches,
                                                       self.base_json['terminate']['value']))))
        elif self.base_json['terminate']['type'] != 'pass':
            term_values = [int(a2r(self.parent.man.gain,
                                   self.parent.man.res_load,
                                   self.parent.man.vol_read,
                                   self.parent.man.adc_bit,
                                   self.parent.man.vol_ref_adc,
                                   self.parent.man.res_switches,
                                   self.base_json['terminate']['value'][0])), int(a2r(self.parent.man.gain,
                                                                                      self.parent.man.res_load,
                                                                                      self.parent.man.vol_read,
                                                                                      self.parent.man.adc_bit,
                                                                                      self.parent.man.vol_ref_adc,
                                                                                      self.parent.man.res_switches,
                                                                                      self.base_json['terminate']['value'][1]))]
            term_values.sort()
            self.ui.shutdown_min.setText(str(term_values[0]))
            self.ui.shutdown_max.setText(str(term_values[1]))

        self.ui.repeat_count.setValue(self.base_json['params']['count'])

    def _choose_terminator(self) -> None:
        """
        Изменение отображения терминаора
        """
        term = self.ui.terminator_combobox.currentText()
        if term == 'pass':
            self._hide_list_terminate()
            self._hide_int_terminate()
        elif term in self.one_value_terminators:
            self._show_int_terminate()
            self._hide_list_terminate()
        else:
            self._hide_int_terminate()
            self._show_list_terminate()

    def _hide_list_terminate(self) -> None:
        """
        Скрыть виджеты
        """
        self.ui.shutdown_max.hide()
        self.ui.shutdown_max_label.hide()
        self.ui.shutdown_enc.hide()
        self.ui.shutdown_enc_label.hide()
        self.ui.shutdown_min.hide()
        self.ui.shutdown_min_label.hide()

    def _show_list_terminate(self) -> None:
        """
        Показать виджеты
        """
        self.ui.shutdown_max.show()
        self.ui.shutdown_max_label.show()
        self.ui.shutdown_min.show()
        self.ui.shutdown_min_label.show()

    def _hide_int_terminate(self) -> None:
        """
        Скрыть виджеты
        """
        self.ui.shutdown_value.hide()
        self.ui.shutdown_value_label.hide()

    def _show_int_terminate(self) -> None:
        """
        Показать виджеты
        """
        self.ui.shutdown_value.show()
        self.ui.shutdown_value_label.show()

    def closeEvent(self, event):
        """
        Закрытие окна
        """
        if self.file_saved: # событие вызвала кнопка сохранить
            if self.mode == "create":
                # обновляем список
                self.parent.exp_settings_dialog.refresh_list()
            elif self.mode == "edit":
                self.parent.exp_settings_dialog.apply_edit_to_exp_list()
            self.set_up_init_values()
            event.accept()
        else: # событие вызвала кнопка отмена
            self.set_up_init_values()
            event.accept()
        # удаление ticket.png при закрытии окна
        if os.path.isfile(self.IMG_PATH):
            os.remove(self.IMG_PATH)
