"""
Окно истории
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
import csv
import json
import pickle
import struct
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QHeaderView

from manager.service.global_settings import TICKET_PATH
from manager.service.saves import results_from_float_bytes, results_from_bytes
from manager.service import v2d, a2r, d2v
from gui.src import show_warning_messagebox, bool_to_label

class History(QDialog):
    """
    Окно информации о ячейке
    """

    GUI_PATH = os.path.join("gui","uies","history.ui")
    experiments: list # эксперименты из базы
    tickets: list # тикеты из базы
    mode: str # режим открытия
    export_to_json_mode: bool # режим экспорта
    tickets_ids: list    # id тикетов выбранного эксперимента
    lang_pack: dict

    def __init__(self, parent=None, mode=None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        # параметры таблицы table_history_experiments
        self.ui.table_history_experiments.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_history_experiments.setColumnCount(4)
        self.ui.table_history_experiments.setHorizontalHeaderLabels([self.lang_pack.get("e_data"), self.lang_pack.get("e_name"), self.lang_pack.get("e_status"), self.lang_pack.get("e_res")])
        self.ui.table_history_experiments.itemClicked.connect(self.show_experiment_tickets)
        self.ui.table_history_tickets.itemDoubleClicked.connect(self.show_ticket)
        # параметры таблицы table_history_tickets
        self.ui.table_history_tickets.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_history_tickets.setColumnCount(3)
        self.ui.table_history_tickets.setHorizontalHeaderLabels([self.lang_pack.get("e_data"), self.lang_pack.get("e_tic"), self.lang_pack.get("e_status")])
        # доп настройки
        self.setModal(True)
        # история
        self.experiments = []
        self.tickets = []
        self.fill_table_history_experiments()
        # обработчики кнопок
        self.ui.button_load.clicked.connect(self.load_experiment)
        self.ui.button_load_from_db.clicked.connect(self.export_ticket_from_db)
        self.ui.button_export_to_json.clicked.connect(self.export_ticket_to_json)
        self.ui.button_cancel.clicked.connect(self.close)
        self.ui.button_load.setDisabled(True)
        self.ui.button_load_from_db.setDisabled(True)
        self.ui.button_export_to_json.setDisabled(True)
        self.ui.button_choose_exp.setDisabled(True)
        self.ui.button_export.clicked.connect(self.export_experiment)
        # варианты отображения
        if self.parent.opener == 'rram':
            self.ui.button_load.hide()
        else:
            self.ui.button_choose_exp.hide()
        # прочее
        self.export_to_json_mode = False
        self.tickets_ids = []

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("history")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.groupBox_2.setTitle(self.lang_pack.get("name"))
            self.ui.label_3.setText(self.lang_pack.get("exps"))
            self.ui.button_load.setText(self.lang_pack.get("load"))
            self.ui.button_export.setText(self.lang_pack.get("export"))
            self.ui.button_choose_exp.setText(self.lang_pack.get("choose"))
            self.ui.button_cancel.setText(self.lang_pack.get("cancel"))
            self.ui.tab_history_info.setTabText(0, self.lang_pack.get("short"))
            self.ui.tab_history_info.setTabText(1, self.lang_pack.get("full"))
            self.ui.label_2.setText(self.lang_pack.get("quick"))
            self.ui.label.setText(self.lang_pack.get("exp_history"))
            self.ui.button_load_from_db.setText(self.lang_pack.get("csv"))
            self.ui.button_export_to_json.setText(self.lang_pack.get("json"))

    def export_ticket_from_db(self) -> None:
        """
        Выгрузить данные по тикету из бд в csv
        """
        fname = ''
        selected_items = self.ui.table_history_tickets.selectedItems() # все выделенные ячейки
        rows = [] # номера выделенных рядов
        for item in selected_items:
            cur_item = self.ui.table_history_tickets.row(item)
            found = False
            for row in rows: # проверка на повторное вхождение
                if row == cur_item:
                    found = True
                    break
            if found is False:
                rows.append(cur_item)
                fname = fname + "+" + self.ui.table_history_tickets.item(cur_item, 1).text()
        if rows:
            fname = os.path.join(str(QFileDialog.getExistingDirectory(self)),
                                 f'{self.tickets[self.ui.table_history_tickets.currentRow()][1]}_'+fname+'.csv')
            with open(fname,'w',newline='', encoding='utf-8') as file:
                file_wr = csv.writer(file, delimiter=";")
                file_wr.writerow(['sign', 'dac', 'adc', 'vol', 'res'])
                for row in rows:
                    ticket_id = self.tickets[row][0]
                    _, ticket_result = self.parent.man.db.get_ticket_from_id(ticket_id)
                    _, experiment_id = self.parent.man.db.get_experiment_id_from_ticket_id(ticket_id)
                    try:  # New format in floats
                        all_raw_data = results_from_float_bytes(ticket_result, additional_items_size=1)  # TODO pass dac from connector
                        raw_sign, raw_vol, raw_res, raw_adc = [], [], [], []
                        for data in all_raw_data:
                            raw_sign.append(data[0])
                            raw_vol.append(data[1])
                            raw_res.append(data[2])
                            raw_adc.append(data[3])
                        _, meta_info = self.parent.man.db.get_meta_info_from_experiment_id(experiment_id)
                        if isinstance(meta_info, dict):
                            dac_bit = meta_info['dac_bit']
                            vol_ref_dac = meta_info['vol_ref_dac']
                        else:
                            dac_bit = self.parent.man.dac_bit
                            vol_ref_dac = self.parent.man.vol_ref_dac
                        for i, item in enumerate(raw_sign):
                            file_wr.writerow([item,  # sign
                                              str(v2d(dac_bit,  # dac
                                                    vol_ref_dac,
                                                    raw_vol[i])),
                                              raw_adc[i],  # adc
                                              raw_vol[i],  # vol
                                              raw_res[i]])  # res
                    except struct.error:  # Fallback to old format for backwards compatibility
                        all_raw_data = results_from_bytes(ticket_result)
                        raw_sign = all_raw_data[0::3]
                        raw_dac = all_raw_data[1::3]
                        raw_adc = all_raw_data[2::3]
                        _, meta_info = self.parent.man.db.get_meta_info_from_experiment_id(experiment_id)
                        if isinstance(meta_info, dict):
                            dac_bit = meta_info['dac_bit']
                            vol_ref_dac = meta_info['vol_ref_dac']
                            gain = meta_info['gain']
                            res_load = meta_info['res_load']
                            vol_read = meta_info['vol_read']
                            adc_bit = meta_info['adc_bit']
                            vol_ref_adc = meta_info['vol_ref_adc']
                            res_switches = meta_info['res_switches']
                        else:
                            dac_bit = self.parent.man.dac_bit
                            vol_ref_dac = self.parent.man.vol_ref_dac
                            gain = self.parent.man.gain
                            res_load = self.parent.man.res_load
                            vol_read = self.parent.man.vol_read
                            adc_bit = self.parent.man.adc_bit
                            vol_ref_adc = self.parent.man.vol_ref_adc
                            res_switches = self.parent.man.res_switches
                        for i, item in enumerate(raw_sign):
                            file_wr.writerow([item,
                                            raw_dac[i],
                                            raw_adc[i],
                                            str(d2v(dac_bit,
                                                    vol_ref_dac,
                                                    raw_dac[i],
                                                    sign=item)).replace('.',','),
                                            str(a2r(gain,
                                                    res_load,
                                                    vol_read,
                                                    adc_bit,
                                                    vol_ref_adc,
                                                    res_switches,
                                                    raw_adc[i])).replace('.',',')])
            show_warning_messagebox(parent=self, message=self.lang_pack.get("exported") + fname)
        else:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("pick_ticket"))

    def load_experiment(self) -> None:
        """
        Загрузить эксперимент
        """
        current_row = self.ui.table_history_experiments.currentRow()
        experiment_id = self.experiments[current_row][0]
        self.parent.load_experiment(experiment_id)
        self.close()

    def fill_table_history_experiments(self) -> None:
        """
        Заполнить таблицу экспериментов
        """
        # стираем данные
        while self.ui.table_history_experiments.rowCount() > 0:
            self.ui.table_history_experiments.removeRow(0)
        if self.mode == "single":
            _, memristor_id = self.parent.man.db.get_memristor_id(self.parent.current_wl,
                                                                       self.parent.current_bl,
                                                                       self.parent.man.crossbar_id)
            _, self.experiments = self.parent.man.db.get_memristor_experiments(memristor_id)
        else:
            _, self.experiments = self.parent.man.db.get_experiments(self.parent.man.crossbar_id)
        # добавление инфы
        for item in self.experiments:
            #if not item[2] == 'measure':
            row_position = self.ui.table_history_experiments.rowCount()
            self.ui.table_history_experiments.insertRow(row_position)
            self.ui.table_history_experiments.setItem(row_position, 0, QTableWidgetItem(item[1]))
            self.ui.table_history_experiments.setItem(row_position, 1, QTableWidgetItem(item[2]))
            self.ui.table_history_experiments.setItem(row_position, 2, QTableWidgetItem(bool_to_label(item[3])))
            self.ui.table_history_experiments.setItem(row_position, 3, QTableWidgetItem(str(item[4])))
        self.ui.table_history_experiments.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def show_experiment_tickets(self) -> None:
        """
        Показать тикеты эксперимента
        """
        # стираем данные
        while self.ui.table_history_tickets.rowCount() > 0:
            self.ui.table_history_tickets.removeRow(0)
        # определить experiment_id
        current_row = self.ui.table_history_experiments.currentRow()
        experiment_id = self.experiments[current_row][0]
        _, self.tickets = self.parent.man.db.get_experiment_tickets(experiment_id)
        # добавление инфы
        for item in self.tickets:
            row_position = self.ui.table_history_tickets.rowCount()
            self.ui.table_history_tickets.insertRow(row_position)
            self.ui.table_history_tickets.setItem(row_position, 0, QTableWidgetItem(item[1]))
            self.ui.table_history_tickets.setItem(row_position, 1, QTableWidgetItem(item[2]))
            self.ui.table_history_tickets.setItem(row_position, 2, QTableWidgetItem(bool_to_label(item[3])))
        self.ui.table_history_tickets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        if self.parent.man.board_type != 'offline':
            self.ui.button_load.setDisabled(False)
            self.ui.button_choose_exp.setDisabled(False)
        self.ui.button_load_from_db.setDisabled(False)
        self.ui.button_export_to_json.setDisabled(False)
        # поучаем рисунок
        status, image = self.parent.man.db.get_img_experiment(experiment_id)
        if status:
            pixmap = QPixmap()
            pixmap.loadFromData(image)
            self.ui.label_image.setPixmap(pixmap)
            quick_data = self.lang_pack.get("data") + self.experiments[current_row][1]
            quick_data += "\n" + self.lang_pack.get("tic_name") + self.experiments[current_row][2]
            _, mem_id = self.parent.man.db.get_memristor_id_from_experiment_id(experiment_id)
            _, crb_id = self.parent.man.db.get_crossbar_id_from_memristor_id(mem_id)
            _, serial = self.parent.man.db.get_crossbar_serial_from_id(crb_id)
            quick_data += "\n" + self.lang_pack.get("serial") + str(serial)
            _, wl = self.parent.man.db.get_wl_from_memristor_id(mem_id)
            quick_data += "\nWL: " + str(wl)
            _, bl = self.parent.man.db.get_bl_from_memristor_id(mem_id)
            quick_data += "\nBL: " + str(bl)
            _, meta_info = self.parent.man.db.get_meta_info_from_experiment_id(experiment_id)
            if isinstance(meta_info, dict):
                for key in meta_info:
                    quick_data += f"\n{key}: {meta_info[key]}"
            self.ui.quick_view.setText(quick_data)

    def export_ticket_to_json(self) -> None:
        """
        Экспортировать тикет в json
        """
        items = self.ui.table_history_tickets.selectedItems() # все выделенные ячейки
        # проверки на выбор
        ok = True
        if len(items) == 0:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("pick_ticket"))
            ok = False
        elif len(items) > 3:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("pick_one"))
            ok = False
        rows = []
        for item in items:
            cur_row = self.ui.table_history_tickets.row(item)
            more_than_one = False
            for row in rows:
                if row != cur_row:
                    more_than_one = True
                    break
            if more_than_one:
                show_warning_messagebox(parent=self, message=self.lang_pack.get("pick_one"))
                ok = False
            else:
                rows.append(cur_row)
        # экспорт тикета
        if ok:
            ticket_id = self.tickets[cur_row][0]
            blob = self.parent.man.db.get_BLOB_from_ticket_id(ticket_id)[1]
            ticket_info = pickle.loads(blob)
            fname = ticket_info["name"] + "_" + str(ticket_id)
            with open(os.path.join(TICKET_PATH,
                                fname+'.json'),
                                'w', encoding='utf-8') as outfile:
                json.dump(ticket_info, outfile, ensure_ascii=False, indent=4)
                outfile.close()
            show_warning_messagebox(parent=self, message=self.lang_pack.get("exported") + os.path.join(TICKET_PATH, fname + '.json'))

    def show_ticket(self) -> None:
        """
        Отобразить окно сигнала для выбранного тикета
        """
        blob = self.parent.man.db.get_BLOB_from_ticket_id(self.tickets[self.ui.table_history_tickets.currentRow()][0])[1]
        self.parent.show_signal_dialog(pickle.loads(blob), "view")

    def export_experiment(self) -> None:
        """
        Экспорт всех тикетов эксперимента
        """
        # определить experiment_id
        current_row = self.ui.table_history_experiments.currentRow()
        experiment_id = self.experiments[current_row][0]
        _, tickets = self.parent.man.db.get_experiment_tickets(experiment_id)
        if len(tickets) > 0:
            self.export_to_json_mode = True
            for i in range(len(tickets)):
                self.tickets_ids.append(tickets[i][0])
            self.tickets_ids.append(self.experiments[current_row][2])
            # экспорт эксперимента
            fname = self.tickets_ids[len(self.tickets_ids)-1]
            self.tickets_ids.pop()
            experiment_dict = {}
            for k, ticket_id in enumerate(self.tickets_ids):
                blob = self.parent.man.db.get_BLOB_from_ticket_id(ticket_id)[1]
                experiment_dict[k] = pickle.loads(blob)
            with open(os.path.join(TICKET_PATH, fname+'.json'), 'w', encoding='utf-8') as file:
                json.dump(experiment_dict, file, ensure_ascii=False, indent=4)
            show_warning_messagebox(parent=self, message=self.lang_pack.get("exported") + os.path.join(TICKET_PATH, fname + '.json'))
            self.tickets_ids = []
        

    def set_up_init_values(self) -> None:
        """
        Задать начальные значения
        """
        self.experiments = []
        self.tickets = []

    def closeEvent(self, event):
        """
        Выход из окна ифнормации
        """
        self.set_up_init_values()
        event.accept()
