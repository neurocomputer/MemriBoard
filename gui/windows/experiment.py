"""
Диалоговое окно экспериментов
Доделать:
check_exp
"""

# pylint: disable=E0611,C0103,I1101,C0301

import os
import pickle
from copy import deepcopy
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from manager.service.global_settings import TICKET_PATH
from manager.service.plots import calculate_counts_for_ticket
from gui.src import show_warning_messagebox, show_choose_window

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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.setModal(True)
        # список сигналов (тикетов)
        self.list_model = QStandardItemModel()
        self.ui.exp_list.setModel(self.list_model)
        self.refresh_list()
        self.ui.exp_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.exp_list.doubleClicked.connect(self._add_exp_to_list)
        # список экспериментов
        self.list_experiments = QStandardItemModel()
        self.ui.plan_list.setModel(self.list_experiments)
        self._refresh_exp_list()
        self.ui.plan_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.plan_list.doubleClicked.connect(self._edit_ticket)
        try:
            self.ui.exp_name.setText("Эксперимент_" + str(self.parent.man.db.get_last_experiment()[1]+1))
        except TypeError:
            self.ui.exp_name.setText("Эксперимент_1")
        # обработка кнопок
        self.ui.button_new_signal.clicked.connect(lambda: self.parent.show_signal_dialog("blank",
                                                                                         "create"))
        self.ui.button_delete.clicked.connect(self._delete_json)
        self.ui.button_add_exp.clicked.connect(self._add_exp_to_list)
        self.ui.button_up_plan.clicked.connect(lambda: self._exp_list_up_exp(-1))
        self.ui.button_down_plan.clicked.connect(lambda: self._exp_list_up_exp(1))
        self.ui.button_delete_plan.clicked.connect(self._exp_list_delete)
        self.ui.button_edit_ticket.clicked.connect(self._edit_ticket)
        self.ui.button_view_requets.clicked.connect(self._view_requests)
        self.ui.button_cancel_exp.clicked.connect(self.close)
        self.ui.button_apply_exp.clicked.connect(self.apply_exp)
        self.ui.button_check_exp.clicked.connect(self.check_exp)
        self.ui.button_load_exp.clicked.connect(lambda: self.parent.show_history_dialog(mode="all"))
        self.ui.button_apply_all.clicked.connect(self.apply_exp_all)
        self.ui.button_duplicate.clicked.connect(self.duplicate_ticket)
        # блок кнопок
        if parent.opener == 'testing':
            self.ui.button_apply_exp.setEnabled(False)
        else:
            self.ui.button_apply_all.setEnabled(False)

    def set_up_init_values(self):
        """
        Задать начальные значения
        """
        self.ticket_files = []
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

    def _delete_json(self) -> None:
        """
        Удаляем json файл с диска
        """
        # получаем имя файла
        file_name = self.ui.exp_list.currentIndex().data()
        if file_name and not file_name in self.parent.protected_modes: # защита .json
            answer = show_choose_window(self, 'Удалить файл?')
            if answer:
                os.remove(os.path.join(TICKET_PATH,
                          file_name+'.json'))
                self.refresh_list() # обновляем список

    def label_total_update(self) -> None:
        """
        Обновляем значение лейблов
        """
        time_done = round(((self.parent.exp_list_params['total_tasks'] * 55) / 1000) / 60, 0) # todo: скорректировать время
        self.ui.label_count_tasks.setText(f"Всего тикетов: {self.parent.exp_list_params['total_tickets']}   Всего запросов к плате: {str(self.parent.exp_list_params['total_tasks'])}   Примерное время выполнения: {time_done} мин.")

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
            task_list, count = calculate_counts_for_ticket(self.parent.man, ticket.copy())
            self.parent.exp_list_params['total_tickets'] += 1
            self.parent.exp_list_params['total_tasks'] += count
            # 5 отображаем название тикета в списке
            self.parent.exp_list.append((ticket["name"], ticket.copy(), task_list.copy(), count))
            self._refresh_exp_list()
            # 6 обновляем значение лейблов
            self.label_total_update()
        except KeyError:
            show_warning_messagebox("Тикет не возможно прочитать!")

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
            self.parent.exp_list_params['total_tasks'] -= ticket_for_del[3]
            # 5 обновляем значение лейблов
            self.label_total_update()
            # обновляем список
            self._refresh_exp_list()
        except IndexError:
            show_warning_messagebox("Нечего удалять!")

    def _exp_list_up_exp(self, direction: int) -> None:
        """
        Движение по списку тикетов
        """
        exp_index = self.ui.plan_list.currentIndex().row()
        if exp_index == 0 and direction == -1:
            pass
        elif len(self.parent.exp_list)-1 == exp_index and direction == 1:
            pass
        else:
            self.parent.exp_list.insert(exp_index + direction, self.parent.exp_list.pop(exp_index))
            self._refresh_exp_list()
            self.ui.plan_list.setCurrentIndex(self.ui.plan_list.model().index(exp_index + direction,0))

    def _edit_ticket(self) -> None:
        """
        Правка тикета
        """
        # определяем номер тикета
        ticket_position = self.ui.plan_list.currentIndex().row()
        ticket = self.parent.exp_list[ticket_position][1].copy()
        # открываем для редактирования
        self.parent.show_signal_dialog(ticket, "edit")

    def apply_edit_to_exp_list(self) -> None:
        """
        Применить правки тикета
        """
        new_ticket = self.parent.read_ticket_from_disk("temp.json")
        os.remove(os.path.join(TICKET_PATH,"temp.json"))
        #указываем ячейку
        new_ticket["params"]["wl"] = self.parent.current_wl
        new_ticket["params"]["bl"] = self.parent.current_bl
        task_list, count = calculate_counts_for_ticket(self.parent.man, new_ticket.copy())
        ticket_position = self.ui.plan_list.currentIndex().row()
        self.parent.exp_list_params['total_tasks'] -= self.parent.exp_list[ticket_position][3]
        self.parent.exp_list_params['total_tasks'] += count
        self.parent.exp_list[ticket_position] = (new_ticket["name"],
                                                 new_ticket.copy(),
                                                 task_list.copy(),
                                                 count)
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
                show_warning_messagebox("Введите имя плана эксперимента!")
        else:
            show_warning_messagebox("Заполните план эксперимента!")

    def apply_exp_all(self) -> None:
        """
        Применить один эксперимент ко всем ячейкам
        """
        if self.parent.exp_list:
            # получить имя эксперимента
            exp_name = self.ui.exp_name.text()
            if exp_name:
                self.parent.exp_name = exp_name
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
            if self.parent.exp_list:
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

    def check_exp(self) -> None:
        """
        Проверить эксперимент
        """
        show_warning_messagebox("Пока не реализовано!")

    def load_tickets(self, exp_name: str, tickets: list) -> None:
        """
        Загрузка тикетов из истории
        """
        self.ui.exp_name.setText(exp_name)
        for ticket in tickets:
            tick = pickle.loads(ticket[0])
            self._add_exp_to_list(ticket=tick)

    def duplicate_ticket(self) -> None:
        """
        Дублировать сигнал
        """
        # определяем номер тикета
        ticket_position = self.ui.plan_list.currentIndex().row()
        ticket = deepcopy(self.parent.exp_list[ticket_position][1])
        task_list, count = calculate_counts_for_ticket(self.parent.man, deepcopy(ticket))
        # копируем выбранный тикет
        self.parent.exp_list.append((ticket["name"], deepcopy(ticket), deepcopy(task_list), count))
        # обновляем параметры
        self.parent.exp_list_params['total_tickets'] += 1
        self.parent.exp_list_params['total_tasks'] += count
        self._refresh_exp_list()
        self.label_total_update()
