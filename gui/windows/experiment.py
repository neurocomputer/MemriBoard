"""
Диалоговое окно экспериментов
Доделать:
check_exp
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
import pickle
import json
from typing import Union
from copy import deepcopy
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from gui.windows.algorithm_editor import AlgorithmEditor
from manager.service.global_settings import TICKET_PATH, ALGORITHM_PATH
from manager.service.plots import calculate_counts_for_ticket
from gui.src import show_warning_messagebox, show_choose_window, open_file_dialog

class ExpSettings(QDialog):
    """
    Диалоговое окно экспериментов
    parent:
    man
    protected_modes
    show_signal_dialog()
    read_ticket_from_disk()
    """

    GUI_PATH = os.path.join(os.getcwd(),"gui","uies","experiment.ui")
    ticket_files: list = []
    list_experiments: QStandardItemModel
    list_model: QStandardItemModel
    apply_exp_all_button_clicked: bool = False
    importing_experiment: bool = False
    lang_pack: dict

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        self.setModal(True)
        # список сигналов (тикетов)
        self.list_model = QStandardItemModel()
        self.ui.exp_list.setModel(self.list_model)
        self.refresh_list()
        self.ui.exp_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.exp_list.doubleClicked.connect(self._add_exp_to_list)
        # Список алгоритмов
        self.alg_list_model = QStandardItemModel()
        self.ui.alg_list.setModel(self.alg_list_model)
        self.refresh_alg_list()
        self.ui.alg_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.alg_list.doubleClicked.connect(self._add_alg_to_list)
        # список экспериментов
        self.list_experiments = QStandardItemModel()
        self.ui.plan_list.setModel(self.list_experiments)
        self._refresh_exp_list()
        self.label_total_update()
        self.ui.plan_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.plan_list.doubleClicked.connect(self._edit_ticket)
        try:
            self.ui.exp_name.setText("Experiment_" + str(self.parent.man.db.get_last_experiment()[1]+1))
        except TypeError:
            self.ui.exp_name.setText("Experiment_1")
        # обработка кнопок
        self.ui.button_new_signal.clicked.connect(lambda: self.parent.show_signal_dialog("blank",
                                                                                         "create"))
        self.ui.button_new_algorithm.clicked.connect(lambda: self.show_algorithm_dialog(ticket=None))
        self.ui.button_delete.clicked.connect(lambda: self._delete_json(ticket_group='tickets'))
        self.ui.button_delete_algorithm.clicked.connect(lambda: self._delete_json(ticket_group='algorithms'))
        self.ui.button_add_exp.clicked.connect(self._add_exp_to_list)
        self.ui.button_add_algorithm.clicked.connect(self._add_alg_to_list)
        self.ui.button_up_plan.clicked.connect(lambda: self._exp_list_up_exp(-1))
        self.ui.button_down_plan.clicked.connect(lambda: self._exp_list_up_exp(1))
        self.ui.button_delete_plan.clicked.connect(self._exp_list_delete)
        self.ui.button_edit_ticket.clicked.connect(self._edit_ticket)
        self.ui.button_view_requests.clicked.connect(self._view_requests)
        self.ui.button_cancel_exp.clicked.connect(self.close)
        self.ui.button_load_exp.clicked.connect(lambda: self.parent.show_history_dialog(mode="all"))
        self.ui.button_duplicate.clicked.connect(self.duplicate_ticket)
        self.ui.button_import.clicked.connect(self.import_experiment_json)
        if parent.opener == 'testing':
            self.ui.button_apply_exp.clicked.connect(self.apply_exp_all)
        else:
            self.ui.button_apply_exp.clicked.connect(self.apply_exp)

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("experiment")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.groupBox.setTitle(self.lang_pack.get("signals"))
            self.ui.groupBox_2.setTitle(self.lang_pack.get("exp_plan"))
            self.ui.groupBox_3.setTitle(self.lang_pack.get("algorithms"))
            self.ui.button_new_signal.setText(self.lang_pack.get("new"))
            self.ui.button_add_exp.setText(self.lang_pack.get("add_to_plan"))
            self.ui.button_new_algorithm.setText(self.lang_pack.get("new"))
            self.ui.button_add_algorithm.setText(self.lang_pack.get("add_to_plan"))
            self.ui.label.setText(self.lang_pack.get("exp_name"))
            self.ui.button_load_exp.setText(self.lang_pack.get("upload"))
            self.ui.button_import.setText(self.lang_pack.get("import"))
            self.ui.button_edit_ticket.setText(self.lang_pack.get("edit"))
            self.ui.button_duplicate.setText(self.lang_pack.get("duplicate"))
            self.ui.button_view_requests.setText(self.lang_pack.get("view_req"))
            self.ui.button_apply_exp.setText(self.lang_pack.get("apply_cell"))
            self.ui.button_cancel_exp.setText(self.lang_pack.get("cancel"))

    def set_up_init_values(self):
        """
        Задать начальные значения
        """
        self.ticket_files = []
        self.apply_exp_all_button_clicked = False
        self.parent.exp_list = []
        self.parent.exp_name = ''
        self.parent.exp_list_params = {}
        self.parent.exp_list_params['total_tickets'] = 0
        self.parent.exp_list_params['total_tasks'] = 0

    def refresh_list(self) -> None:
        """
        Обновляем список jsonов
        """
        # очищаем список и обновляем
        self.ticket_files = []
        self.list_model.removeRows(0, self.list_model.rowCount())
        file_list = os.listdir(TICKET_PATH)
        file_list.sort()
        for file in file_list:
            self.list_model.appendRow(QStandardItem(file.replace('.json','')))
            self.ticket_files.append(file.replace('.json',''))
            
    def refresh_alg_list(self) -> None:
        """
        Обновить список алгоритмов
        """
        self.alg_list_model.removeRows(0, self.alg_list_model.rowCount())
        if not os.path.exists(ALGORITHM_PATH):
            os.makedirs(ALGORITHM_PATH)
        for filename in sorted(os.listdir(ALGORITHM_PATH)):
            if filename.lower().endswith('.json'):
                self.alg_list_model.appendRow(QStandardItem(filename.replace('.json','')))
        

    def _delete_json(self, ticket_group: str = 'tickets') -> None:
        """
        Удаляем json файл с диска
        """
        # получаем имя файла
        if ticket_group == 'tickets':
            file_name = self.ui.exp_list.currentIndex().data()
            protected = file_name in self.parent.protected_modes  # Защита .json
            path = TICKET_PATH
        elif ticket_group == 'algorithms':
            file_name = self.ui.alg_list.currentIndex().data()
            protected = False
            path = ALGORITHM_PATH
        if file_name:
            if protected:
                show_warning_messagebox(self, self.lang_pack.get('json_protected'))
                return
            answer = show_choose_window(self, self.lang_pack.get("delete_file"))
            if answer:
                os.remove(os.path.join(path, file_name+'.json'))
                if ticket_group == 'tickets':
                    self.refresh_list() # обновляем список
                elif ticket_group == 'algorithms':
                    self.refresh_alg_list()

    def label_total_update(self) -> None:
        """
        Обновляем значение лейблов
        """
        time_done = round(((self.parent.exp_list_params['total_tasks'] * 55) / 1000) / 60, 0) # todo: скорректировать время
        self.ui.label_count_tasks.setText(self.lang_pack.get("tickets") + str(self.parent.exp_list_params['total_tickets']) + self.lang_pack.get("board_req") + str(self.parent.exp_list_params['total_tasks']) + self.lang_pack.get("est_time") + str(time_done) + self.lang_pack.get("min"))

    def _add_exp_to_list(self, **kwargs) -> None:
        """
        Заполнить эксперимент
        """
        try:
            if 'ticket' in kwargs:
                ticket = kwargs['ticket'].copy()
            else:
                # 1 получаем название тикета
                file_name = self.ui.exp_list.currentIndex().data()
                # 2 загружаем тикет в память
                ticket = self.parent.read_ticket_from_disk(file_name+".json")
            # 3 указываем ячейку
            ticket["params"]["wl"] = self.parent.current_wl
            ticket["params"]["bl"] = self.parent.current_bl
            # 4 считаем сколько тикетов и тасков в списке
            count = calculate_counts_for_ticket(self.parent.man, ticket.copy())
            self.parent.exp_list_params['total_tickets'] += 1
            self.parent.exp_list_params['total_tasks'] += count
            # 5 отображаем название тикета в списке
            self.parent.exp_list.append((ticket["name"], ticket.copy(), count))
            self._refresh_exp_list()
            # 6 обновляем значение лейблов
            self.label_total_update()
        except KeyError:
            self.import_experiment_json(mode='dblclick')
            if not self.importing_experiment:
                self.importing_experiment = False
                show_warning_messagebox(parent=self, message=self.lang_pack.get("ticket_unreadable"))
                
    def _add_alg_to_list(self, **kwargs) -> None:
        """
        Добавить алгоритм в план
        """
        if 'ticket' in kwargs:
            ticket = kwargs['ticket'].copy()
        else:
            filename = self.ui.alg_list.currentIndex().data()
            with open(os.path.join(ALGORITHM_PATH, filename + '.json'), 'r', encoding='utf-8') as file:
                ticket = json.load(file)
        ticket["params"]["wl"] = self.parent.current_wl
        ticket["params"]["bl"] = self.parent.current_bl
        count = calculate_counts_for_ticket(self.parent.man, ticket.copy())
        self.parent.exp_list_params['total_tickets'] += 1
        self.parent.exp_list_params['total_tasks'] += count
        self.parent.exp_list.append((ticket["name"], ticket.copy(), count))
        self._refresh_exp_list()
        self.label_total_update()
        

    def _refresh_exp_list(self) -> None:
        """
        Обновление списка
        """
        self.list_experiments.removeRows(0, self.list_experiments.rowCount())
        for item in self.parent.exp_list:
            self.list_experiments.appendRow(QStandardItem(item[0]))

    def _exp_list_delete(self) -> None:
        """
        Удалить тикет из плана
        """
        try:
            ticket_for_del = self.parent.exp_list.pop(self.ui.plan_list.currentIndex().row())
            # 4 считаем сколько тикетов и тасков в списке
            self.parent.exp_list_params['total_tickets'] -= 1
            self.parent.exp_list_params['total_tasks'] -= ticket_for_del[2]
            # 5 обновляем значение лейблов
            self.label_total_update()
            # обновляем список
            self._refresh_exp_list()
        except IndexError:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("nothing_to_remove"))

    def _exp_list_up_exp(self, direction: int) -> None:
        """
        Движение по списку тикетов
        """
        try:
            exp_index = self.ui.plan_list.currentIndex().row()
            self.parent.exp_list.insert(exp_index + direction, self.parent.exp_list.pop(exp_index))
            self._refresh_exp_list()
            self.ui.plan_list.setCurrentIndex(self.ui.plan_list.model().index(exp_index + direction,0))
        except IndexError:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("list_empty"))

    def _edit_ticket(self) -> None:
        """
        Правка тикета
        """
        # определяем номер тикета
        ticket_position = self.ui.plan_list.currentIndex().row()
        ticket = self.parent.exp_list[ticket_position][1].copy()
        # открываем для редактирования
        
        if ticket['mode'] == 'algorithm':
            self.show_algorithm_dialog(ticket)
        else:
            self.parent.show_signal_dialog(ticket, "edit")

    def apply_edit_to_exp_list(self, new_ticket: Union[dict, None] = None) -> None:
        """
        Применить правки тикета
        """
        if new_ticket is None:  # Ticket is passed from Signal window via temp.json file
            new_ticket = self.parent.read_ticket_from_disk("temp.json")
            os.remove(os.path.join(TICKET_PATH,"temp.json"))
        #указываем ячейку
        new_ticket["params"]["wl"] = self.parent.current_wl
        new_ticket["params"]["bl"] = self.parent.current_bl
        count = calculate_counts_for_ticket(self.parent.man, new_ticket.copy())
        ticket_position = self.ui.plan_list.currentIndex().row()
        self.parent.exp_list_params['total_tasks'] -= self.parent.exp_list[ticket_position][2]
        self.parent.exp_list_params['total_tasks'] += count
        self.parent.exp_list[ticket_position] = (new_ticket["name"],
                                                 new_ticket.copy(),
                                                 count)
        self._refresh_exp_list()
        self.label_total_update()

    def apply_exp(self) -> None:
        """
        Выполнение эксперимента
        """
        if self.parent.exp_list:
            # получить имя эксперимента
            exp_name = self.ui.exp_name.text()
            if exp_name:
                self.parent.exp_name = exp_name
                self.parent.show_apply_dialog()
            else:
                show_warning_messagebox(parent=self, message=self.lang_pack.get("exp_name_expected"))
        else:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("fill_plan"))

    def apply_exp_all(self) -> None:
        """
        Применить один эксперимент ко всем ячейкам
        """
        if self.parent.exp_list:
            # получить имя эксперимента
            exp_name = self.ui.exp_name.text()
            if exp_name:
                self.parent.exp_name = exp_name
        self.apply_exp_all_button_clicked = True
        self.close()

    def _view_requests(self) -> None:
        """
        Показать запросы
        """
        self.parent.show_requests_dialog()

    def closeEvent(self, event):
        """
        Выход из планировщика
        """
        if self.parent.opener == 'testing':
            if self.parent.exp_list and self.apply_exp_all_button_clicked:
                self.parent.testing_dialog.button_ready_combination()
                self.parent.testing_dialog.update_label_time_status()
        else:
            self.set_up_init_values()
            self.parent.update_current_cell_info()
            if self.parent.opener == 'cell_info':
                self.parent.cell_info_dialog.fill_info()
            elif self.parent.opener == 'math':
                self.parent.math_dialog.update_label_cell_info()
            elif self.parent.opener == 'mapping':
                self.parent.fill_table()
                self.parent.color_table()
                self.parent.mapping_dialog.update_table_weights(self.parent.current_wl,
                                                                self.parent.current_bl,
                                                                self.parent.current_last_resistance)
        event.accept()

    def check_exp(self) -> None:  # TODO можно доделать и вернуть кнопку
        """
        Проверить эксперимент
        """
        show_warning_messagebox(parent=self, message=self.lang_pack.get("not_done"))

    def load_tickets(self, exp_name: str, tickets: list) -> None:
        """
        Загрузка тикетов из истории
        """
        self.ui.exp_name.setText(exp_name)
        for ticket in tickets:
            tick = pickle.loads(ticket[0])
            self._add_exp_to_list(ticket=tick)

    def import_experiment_json(self, mode='') -> None:
        """
        Импорт json с экспериментом
        """
        try:
            filepath = ''
            if mode == 'dblclick':
                self.importing_experiment = True
                filepath = os.path.join(TICKET_PATH, self.ui.exp_list.currentIndex().data()) + ".json"
            if not filepath:
                filepath = open_file_dialog(self, file_types="JSON Files (*.json)")
            if filepath:
                data: str
                with open (filepath, "r+") as f:
                    data = f.read()
                tickets = json.loads(data)
                for i in range(len(tickets)):
                    self._add_exp_to_list(ticket=tickets.get(str(i)))
                self.ui.exp_name.setText(os.path.splitext(os.path.basename(filepath))[0])
        except Exception as e:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("ticket_unreadable") + f'\n{type(e).__name__}: {e}')

    def duplicate_ticket(self) -> None:
        """
        Дублировать сигнал
        """
        # определяем номер тикета
        ticket_position = self.ui.plan_list.currentIndex().row()
        ticket = deepcopy(self.parent.exp_list[ticket_position][1])
        count = calculate_counts_for_ticket(self.parent.man, deepcopy(ticket))
        # копируем выбранный тикет
        self.parent.exp_list.append((ticket["name"], deepcopy(ticket), count))
        # обновляем параметры
        self.parent.exp_list_params['total_tickets'] += 1
        self.parent.exp_list_params['total_tasks'] += count
        self._refresh_exp_list()
        self.label_total_update()
        
    def show_algorithm_dialog(self, ticket: Union[dict, None] = None) -> None:
        """
        Показать окно редактирования алгоритма
        """
        self.algorithm_dialog = AlgorithmEditor(parent=self, ticket=ticket)
        self.algorithm_dialog.show()
