"""
Диалоговое окно сигнала
"""
# pylint: disable=E0611,W0401,W0611,R0903,R0915,R0912,C0301,C0103

import os
import json
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QComboBox, QSpinBox, QShortcut
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeySequence

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from manager.service.plots import plot_for_signal_graph
from manager.service.global_settings import TICKET_PATH
from manager.terminate import terminators
from manager.menu import Menu
from gui.src import show_warning_messagebox, show_choose_window, convert_ticket_to_reduced_format
from gui.widgets.SignalParametersConfig import SignalParameters
from gui.widgets.MplGraphicsView import MplGraphicsView
from gui.widgets.ScientificQLineEdit import ScientificQLineEdit

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
    total_task_count: int # счетчик тасков в тикете
    one_value_terminators: list # терминаторы с одним значением
    base_json: dict # базовый тикет
    base_ticket_name: str # имя тикета (по имени файла)
    file_saved: bool # флаг сохраненности файла
    mode: str # режим запуска (create, edit)
    lang_pack: dict

    def __init__(self, base_ticket_name, mode, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # Linting widget types
        self.graph: MplGraphicsView
        self.terminate_left: ScientificQLineEdit
        self.terminate_right: ScientificQLineEdit
        self.signal_mode: QComboBox
        self.direction_combobox: QComboBox
        self.repeat_count: QSpinBox
        self.batch_size: QSpinBox
        self.menu: Menu = self.parent.man.menu
        # Adding widgets
        self.signal_param = SignalParameters(self)
        self.horizontalLayout_2.addWidget(self.signal_param)
        self._init_plot()
        # Filling terminator values
        self.terminator_combobox.addItems(list(terminators.keys()))
        self.terminator_combobox.activated.connect(self._choose_terminator)
        self.terminate_left.bad_value.connect(lambda text: self.warn_scientific_widget(self.terminate_left, text))
        self.terminate_right.bad_value.connect(lambda text: self.warn_scientific_widget(self.terminate_right, text))
        # Filling signal modes
        self.signal_mode.addItems(list(self.menu.alias_to_mode().keys()))
        self.signal_mode.currentTextChanged.connect(self._change_signal_mode)
        # UI stuff
        self.change_language()
        self.setModal(True)
        # обработчики кнопок
        self.ui.button_graph.clicked.connect(self._plot_ticket)
        self.ui.button_save.clicked.connect(self._save_json)
        self.ui.button_save_to_file.clicked.connect(self._save_to_file)
        self.ui.button_cancel.clicked.connect(self.close)
        # Shortcut for plot
        shortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        shortcut.activated.connect(self._plot_ticket)
        shortcut = QShortcut(QKeySequence(Qt.Key_Enter), self)
        shortcut.activated.connect(self._plot_ticket)
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
            self.ui.button_save_to_file.setEnabled(False)
            self.ui.json_name.setEnabled(False)
        elif self.mode == 'edit_for_programming':
            self.base_ticket_name = base_ticket_name["name"]
            self.base_json = base_ticket_name
            self.ui.terminator_combobox.setEnabled(False)
            self.ui.json_name.setEnabled(False)
            self.ui.button_save_to_file.setEnabled(False)
        self._load_json() # загружаем blank или для редактирования
        # Centering QSplitter after the window is rendered
        QTimer.singleShot(0, self.center_splitter)

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("signal")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.groupBox_signal_settings.setTitle(self.lang_pack.get("signal_settings"))
            self.ui.groupBox_sending_settings.setTitle(self.lang_pack.get("sending_settings"))
            self.ui.groupBox_terminate.setTitle(self.lang_pack.get("stop_condition"))
            self.ui.groupBox_graph.setTitle(self.lang_pack.get("graph"))
            self.ui.label_signal_mode.setText(self.lang_pack.get("signal_mode"))
            self.ui.label_sending_order.setText(self.lang_pack.get("sending_order"))
            self.ui.label_repeat_times.setText(self.lang_pack.get("times"))
            self.ui.label_repeat.setText(self.lang_pack.get("repeat"))
            self.ui.direction_combobox.setItemText(0, self.lang_pack.get("forth-back"))
            self.ui.direction_combobox.setItemText(1, self.lang_pack.get("back-forth"))
            self.ui.label_batch_size.setText(self.lang_pack.get("batch_size"))
            self.ui.label_batch_size_unit.setText(self.lang_pack.get("pulses"))
            self.ui.label_batch_size.setToolTip(self.lang_pack.get("batch_size_tooltip"))
            self.ui.label_batch_size_unit.setToolTip(self.lang_pack.get("batch_size_tooltip"))
            self.batch_size.setToolTip(self.lang_pack.get("batch_size_tooltip"))
            self.ui.button_graph.setText(self.lang_pack.get("plot"))
            self.ui.label_board_req.setText(self.lang_pack.get("board_req"))
            self.ui.label_exp_name.setText(self.lang_pack.get("exp_name"))
            self.ui.button_save.setText(self.lang_pack.get("save"))
            self.ui.button_save_to_file.setText(self.lang_pack.get("save_to_folder"))
            self.ui.button_cancel.setText(self.lang_pack.get("cancel"))
            self.ui.label_terminate_type.setText(self.lang_pack.get("condition_type"))
            self._choose_terminator()
            self.terminate_left.set_unit(self.lang_pack.get('ohm'))
            self.terminate_right.set_unit(self.lang_pack.get('ohm'))
            # Scientific widgets
            ok, scientific_lang_pack = self.parent.read_language_json("ScientificQLineEdit")
            if ok:
                self.terminate_left.change_prefix_dict(scientific_lang_pack)
                self.terminate_right.change_prefix_dict(scientific_lang_pack)
            # Parameters widget
            ok, params_lang_pack = self.parent.read_language_json("signal_parameters")
            if ok:
                self.signal_param.change_language(params_lang_pack, scientific_lang_pack)
                self._change_signal_mode()  # Update signal mode ui

    def set_up_init_values(self) -> None:
        """
        Задать начальные значения
        """
        self.total_task_count = 0
        self.one_value_terminators = ['==', '>', '<']
        self.base_json = {}
        self.file_saved = False
            
    def warn_scientific_widget(self, widget, text):
        """Warn if scientific widget has a bad value"""
        if not widget.isModified(): # Avoiding Qt bug where warning is shown twice
            return
        widget.setModified(False)
        show_warning_messagebox(parent=self, message=self.lang_pack.get("symbol_incorrect") + f'\n"{text}"')
            
    def _init_plot(self) -> None:
        """
        Initialize the matplotlib widget
        """
        self.toolbar = NavigationToolbar(self.graph.canvas, self)
        self.groupBox_graph.layout().addWidget(self.toolbar)
        
    def _change_signal_mode(self) -> None:
        """
        Change ui based on the signal mode
        """
        signal_mode = self.menu.alias_to_mode()[self.signal_mode.currentText()]
        self.signal_param.set_mode(signal_mode)
        
    def _plot_ticket(self) -> None:
        """
        Просмотр json
        """
        self.ui.button_graph.setFocus()
        plot_type = self.ui.json_plot_type.currentText()
        plot_limits = {  # Maximum number of pulses (tasks) on the plot
            'stem': 10000,
            'plot': 10000
        }
        if self._make_json(): # если json сделан
            json_for_plot = self.base_json.copy()
            # Plotting
            self.total_task_count, limit_hit = plot_for_signal_graph(
                manager=self.parent.man,
                ticket=json_for_plot,
                plot_type=plot_type,
                ax=self.graph.ax,
                plot_limits=plot_limits
            )
            # Labels
            self.graph.ax.set_ylabel(self.lang_pack.get("plot_voltage"))
            if plot_type == 'stem':
                self.graph.ax.set_xlabel(self.lang_pack.get("plot_pulse_count"))
            else:
                self.graph.ax.set_xlabel(self.lang_pack.get("plot_time"))
            self.graph.canvas.draw_idle()
            # Label with plot limit
            if limit_hit:
                self.ui.groupBox_graph.setTitle(self.lang_pack.get("graph") + \
                                                self.lang_pack.get("plot_limit_reached") + str(plot_limits[plot_type]) + ')')
            else:
                self.ui.groupBox_graph.setTitle(self.lang_pack.get("graph"))
            # указываем сколько будет задач
            self.ui.label_count_tasks.setText(str(self.total_task_count))

    def _make_json(self) -> bool:
        """
        Создание json без сохранения

        Returns:
        status -- успех
        """
        status = False
        try:
            self.base_json['name'] = self.ui.json_name.text().strip()
            if self.base_json['name'] == '':
                show_warning_messagebox(parent=self, message=self.lang_pack.get("fill_in_filename"))
                return False
            
            # Signal mode
            self.base_json['mode'] = self.menu.alias_to_mode()[self.signal_mode.currentText()]
            
            # Filling signal parameters
            status, self.base_json = self.signal_param.fill_params_to_ticket(self.base_json)
            if not status:
                raise ValueError
            
            # Other parameters
            self.base_json['params']['count'] = self.repeat_count.value()
            self.base_json['params']['reverse'] = self.direction_combobox.currentIndex()
            self.base_json['params']['id'] = 0
            self.base_json['params']['wl'] = 0
            self.base_json['params']['bl'] = 0

            # терминаторы
            term = self.ui.terminator_combobox.currentText()
            self.base_json['terminate']['type'] = term
            if term == 'pass':
                self.base_json['terminate']['value'] = 0
            elif term in self.one_value_terminators:
                if self.terminate_left.get_value() is None:
                    raise ValueError
                self.base_json['terminate']['value'] = self.terminate_left.get_value()
            else:
                if self.terminate_left.get_value() is None:
                    raise ValueError
                if self.terminate_right.get_value() is None:
                    raise ValueError
                # сортируем
                term_values = [self.terminate_left.get_value(), self.terminate_right.get_value()]
                term_values.sort()
                self.base_json['terminate']['value'] = term_values

            status = True
        except ValueError:
            show_warning_messagebox(parent=self, message=self.lang_pack.get("symbol_incorrect"))
        return status

    def _save_json(self) -> None:
        """
        Сохранение json
        """
        # создать json
        if self._make_json():
            if self.mode == 'create':
                self._save_to_file()
            elif self.mode == "edit":
                self.parent.exp_settings_dialog.apply_edit_to_exp_list(self.base_json)
            elif self.mode == "edit_for_programming":
                self.parent.new_ann_dialog.apply_edit_to_prog_ticket(self.base_json)
            self.file_saved = True
            self.close()
                
    def _save_to_file(self) -> None:
        """
        Сохранение тикета в папку
        """
        # создать json
        if self._make_json():
            if self.mode == "edit":
                self.parent.exp_settings_dialog.apply_edit_to_exp_list(self.base_json)
            elif self.mode == "edit_for_programming":
                self.parent.new_ann_dialog.apply_edit_to_prog_ticket(self.base_json)
            if self.base_json['name'] in self.parent.protected_modes:
                show_warning_messagebox(self, self.lang_pack.get("ticket_protected"))
                return
            save_path = os.path.join(TICKET_PATH, self.base_json['name']+'.json')
            if os.path.exists(save_path):
                if not show_choose_window(self, self.lang_pack.get("ticket_name") + "'" + self.base_json['name'] + "'" + self.lang_pack.get('already_exists')):
                    return
            # открываем файл и пишем
            try:
                with open(save_path, 'w', encoding='utf-8') as outfile:
                    json.dump(self.base_json, outfile, ensure_ascii=False, indent=4)
                self.file_saved = True
            except Exception as e:
                show_warning_messagebox(parent=self, message=self.lang_pack.get("could_not_save") + f'{type(e).__name__}: {e}')
            if self.file_saved:
                self.close()

    def _load_json(self) -> None:
        """
        Загрузка json файла
        """
        if not self.menu.check_mode_compatibility(self.base_json['mode']):
            show_warning_messagebox(self, self.lang_pack.get("other_driver"))
            QTimer.singleShot(0, self.close)
            return

        file_name = self.base_ticket_name
        self.ui.json_name.setText(file_name)
            
        # Converting to new format for backward compatibility
        if 'v_dir_strt_inc' in self.base_json['params']:
            try:
                self.base_json = convert_ticket_to_reduced_format(manager=self.parent.man, ticket=self.base_json)
            except Exception as e:
                show_warning_messagebox(self, self.lang_pack.get("could_not_convert") + f'\n{type(e).__name__}: {e}')
                QTimer.singleShot(0, self.close)
                return
            
        # Signal mode
        signal_mode = self.menu.mode_to_alias()[self.base_json['mode']]
        self.signal_mode.setCurrentText(signal_mode)
        self._change_signal_mode()
        
        # Params
        try:
            self.signal_param.load_ticket_to_ui(self.base_json)
        except KeyError as e:
            show_warning_messagebox(self, self.lang_pack.get("other_driver") + f'\nKeyError: {e}')
            QTimer.singleShot(0, self.close)
            return
        self.direction_combobox.setCurrentIndex(self.base_json['params']['reverse'])
        self.repeat_count.setValue(self.base_json['params']['count'])

        # Terminators
        self.ui.terminator_combobox.setCurrentText(self.base_json['terminate']['type'])
        self._choose_terminator()
        if self.base_json['terminate']['type'] in self.one_value_terminators:
            self.terminate_left.set_value(self.base_json['terminate']['value'])
        elif self.base_json['terminate']['type'] != 'pass':
            term_values = [self.base_json['terminate']['value'][0], self.base_json['terminate']['value'][1]]
            term_values.sort()
            self.terminate_left.set_value(term_values[0])
            self.terminate_right.set_value(term_values[1])

    def _choose_terminator(self) -> None:
        """
        Изменение отображения терминатора
        """
        term = self.ui.terminator_combobox.currentText()
        if term == 'pass':  # Hiding all widgets
            self.ui.label_terminate_left.hide()
            self.ui.label_terminate_right.hide()
            self.terminate_left.hide()
            self.terminate_right.hide()
        elif term == '==':
            self.ui.label_terminate_left.setText(self.lang_pack.get("R=="))
            self.terminate_left.setPlaceholderText(self.lang_pack.get("value"))
            self.ui.label_terminate_left.show()
            self.terminate_left.show()
            self.ui.label_terminate_right.hide()
            self.terminate_right.hide()
        elif term == '>':
            self.ui.label_terminate_left.setText(self.lang_pack.get("R>"))
            self.terminate_left.setPlaceholderText(self.lang_pack.get("value"))
            self.ui.label_terminate_left.show()
            self.terminate_left.show()
            self.ui.label_terminate_right.hide()
            self.terminate_right.hide()
        elif term == '<':
            self.ui.label_terminate_left.setText(self.lang_pack.get("R<"))
            self.terminate_left.setPlaceholderText(self.lang_pack.get("value"))
            self.ui.label_terminate_left.show()
            self.terminate_left.show()
            self.ui.label_terminate_right.hide()
            self.terminate_right.hide()
        elif term == '><':
            self.terminate_left.setPlaceholderText(self.lang_pack.get("min"))
            self.terminate_right.setPlaceholderText(self.lang_pack.get("max"))
            self.ui.label_terminate_left.hide()
            self.terminate_left.show()
            self.ui.label_terminate_right.setText(self.lang_pack.get("R><"))
            self.ui.label_terminate_right.show()
            self.terminate_right.show()
        elif term == '<>':
            self.terminate_left.setPlaceholderText(self.lang_pack.get("min"))
            self.terminate_right.setPlaceholderText(self.lang_pack.get("max"))
            self.ui.label_terminate_left.setText(self.lang_pack.get("R<"))
            self.ui.label_terminate_left.show()
            self.terminate_left.show()
            self.ui.label_terminate_right.setText(self.lang_pack.get("R>+"))
            self.ui.label_terminate_right.show()
            self.terminate_right.show()
        elif term == '<>a':
            self.terminate_left.setPlaceholderText(self.lang_pack.get("min"))
            self.terminate_right.setPlaceholderText(self.lang_pack.get("max"))
            self.ui.label_terminate_left.setText(self.lang_pack.get("R<a"))
            self.ui.label_terminate_left.show()
            self.terminate_left.show()
            self.ui.label_terminate_right.setText(self.lang_pack.get("R>a"))
            self.ui.label_terminate_right.show()
            self.terminate_right.show()
        
    def center_splitter(self) -> None:
        """
        Center the QSplitter widget
        """
        sizes = self.splitter.sizes()
        s1 = int(sum(sizes) / 2)
        s2 = sum(sizes) - s1
        self.splitter.setSizes([s1, s2])
        
    def show_batch_size(self, unit: str, max_size: int) -> None:
        """
        Show the batch size widgets
        """
        self.ui.label_batch_size.show()
        self.ui.label_batch_size_unit.show()
        self.ui.label_batch_size_unit.setText(self.lang_pack.get(unit))
        self.batch_size.show()
        self.batch_size.setMaximum(max_size)
        self.batch_size.setValue(max_size)
    
    def hide_batch_size(self) -> None:
        """
        Hide the batch size widgets
        """
        self.ui.label_batch_size.hide()
        self.ui.label_batch_size_unit.hide()
        self.batch_size.hide()

    def closeEvent(self, event):
        """
        Закрытие окна
        """
        if self.file_saved and self.mode in ['create', 'edit']: # событие вызвала кнопка сохранить
            # обновляем список
            self.parent.exp_settings_dialog.refresh_list()
        self.set_up_init_values()
        event.accept()
