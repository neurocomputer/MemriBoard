"""
Окно подключения
"""

# pylint: disable=E0611,C0301

import os
from sys import platform
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtSerialPort import QSerialPortInfo

from gui.src import show_choose_window, show_warning_messagebox
from manager.service.drivers import get_driver_list, get_driver_attr

class ConnectDialog(QDialog):
    """
    Окно подключения
    """

    GUI_PATH = os.path.join("gui","uies","connect.ui")
    connect_flag: bool = False
    cb_serial: str
    com_port: str = ''
    lang_pack: dict
    core_scanned = False

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        self.setModal(True)
        # обработки кнопок
        self.ui.button_update.clicked.connect(self.update_port_list)
        self.ui.button_connect.clicked.connect(self.connect)
        self.ui.button_quit.clicked.connect(self.close)
        self.ui.button_settings.clicked.connect(self._settings)
        self.ui.button_new_crossbar.clicked.connect(lambda: self.show_new_cb_layout(True))
        self.ui.button_scan_core.clicked.connect(self.core_scan)
        # обработка комбо
        self.ui.combo_com_name.currentIndexChanged.connect(self.on_com_name_changed)
        self.ui.edit_com_name.textChanged.connect(self.on_com_name_changed)
        self.ui.combo_board_type.currentIndexChanged.connect(self.on_combo_board_type_changed)
        self.ui.combo_core_name.currentIndexChanged.connect(self.on_core_name_changed)
        # обновление отображения
        self.show_new_cb_layout(False)
        self.update_crossbar_list()
        self.update_board_list()
        self.on_combo_board_type_changed()
        # блокировка выбора плат
        self.ui.combo_board_type.setDisabled(self.parent.man.get_meta_info()["lock_board_type"])
        # Предупреждаем, если изменились настройки в settings.ini
        if self.parent.man.new_config_keys is not None:
            show_warning_messagebox(parent=self, message=self.lang_pack.get('new_settings') + '\n'.join(self.parent.man.new_config_keys))

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("connect")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.label.setText(self.lang_pack.get("crossbar"))
            self.ui.button_new_crossbar.setText(self.lang_pack.get("new"))
            self.ui.label_4.setText(self.lang_pack.get("serial"))
            self.ui.label_5.setText(self.lang_pack.get("comm"))
            self.ui.label_6.setText(self.lang_pack.get("bl"))
            self.ui.label_7.setText(self.lang_pack.get("wl"))
            self.ui.label_8.setText(self.lang_pack.get("crossbar_type"))
            self.ui.label_2.setText(self.lang_pack.get("board"))
            self.ui.label_com_promt.setText(self.lang_pack.get("com_port"))
            self.ui.button_update.setText(self.lang_pack.get("update"))
            self.ui.label_com_entry.setText(self.lang_pack.get("or_write"))
            self.ui.button_connect.setText(self.lang_pack.get("connect"))
            self.ui.button_settings.setText(self.lang_pack.get("settings"))
            self.ui.button_quit.setText(self.lang_pack.get("quit"))
            self.ui.label_status.setText(self.lang_pack.get("status"))

    def on_com_name_changed(self) -> None:
        """
        Выбрали порт
        """
        combo_com_name = self.ui.combo_com_name.currentText()
        edit_com_name = self.ui.edit_com_name.text()
        # адрес COM порта
        if edit_com_name: # адрес введен вручную
            self.com_port = edit_com_name
        else: # адрес в списке
            self.com_port = combo_com_name

    def on_core_name_changed(self) -> None:
        """
        Выбрали core
        """
        self.addr = self.ui.combo_core_name.currentData()

    def show_new_cb_layout(self, state) -> None:
        """
        Показать настройки нового кроссбара
        """
        self.ui.edit_cb_serial.setVisible(state)
        self.ui.edit_cb_comment.setVisible(state)
        self.ui.edit_cb_bl.setVisible(state)
        self.ui.edit_cb_wl.setVisible(state)
        self.ui.combo_cb_type.setVisible(state)
        self.ui.label_4.setVisible(state)
        self.ui.label_5.setVisible(state)
        self.ui.label_6.setVisible(state)
        self.ui.label_7.setVisible(state)
        self.ui.label_8.setVisible(state)

    def show_com_settings_layout(self, state):
        """
        Показать параметры COM если плата с портом
        """
        self.ui.label_com_promt.setVisible(state)
        self.ui.combo_com_name.setVisible(state)
        self.ui.button_update.setVisible(state)
        self.ui.label_com_entry.setVisible(state)
        self.ui.edit_com_name.setVisible(state)

    def show_core_settings_layout(self, state):
        """
        Показать параметры CORE если в COM выбран pico драйвер
        """
        self.ui.label_core_name.setVisible(state)
        self.ui.combo_core_name.setVisible(state)
        self.ui.button_scan_core.setVisible(state)

    def _settings(self) -> None:
        """
        Настройки
        """
        self.parent.show_settings_dialog()

    def update_port_list(self) -> None:
        """
        Обновление списка портов
        """
        # список портов
        port_list = []
        ports = QSerialPortInfo().availablePorts()
        com_port = None
        for port in ports:
            if platform == "linux" or platform == "linux2":
                com_port = "/dev/" + port.portName()
            elif platform == "darwin":
                com_port = "/dev/" + port.portName()
            elif platform == "win32":
                com_port = port.portName()
            port_list.append(com_port)
        port_list.insert(0, self.parent.man.ap_config["connector"]["com_port"]) # default
        self.ui.combo_com_name.clear()
        self.ui.combo_com_name.addItems(port_list)

    def update_crossbar_list(self) -> None:
        """
        Обновление списка кроссбаров
        """
        # список кроссбаров
        status, cb_list = self.parent.man.db.get_cb_list()
        try:
            last_serial = self.parent.man.ap_config["gui"]["last_crossbar_serial"]
            if last_serial:
                cb_list.insert(0, last_serial)
        except Exception: # pylint: disable=W0718
            pass
        if status:
            self.ui.combo_cb_serial.clear()
            self.ui.combo_cb_serial.addItems(cb_list)

    def update_board_list(self):
        """
        Обновить список плат
        """
        board_list = ['offline', *get_driver_list()]
        try:
            last_board = self.parent.man.ap_config["board"]["board_type"]
            if last_board:
                board_list.insert(0, last_board)
        except Exception: # pylint: disable=W0718
            pass
        self.ui.combo_board_type.clear()
        self.ui.combo_board_type.addItems(board_list)

    def update_window_size(self):
        """
        обновить размер окна
        """
        self.ui.central_layout.invalidate()
        self.ui.widget.setVisible(False)
        self.ui.widget.setVisible(True)
        self.widget.updateGeometry()
        self.updateGeometry()
        self.adjustSize()

    def on_combo_board_type_changed(self) -> None:
        """
        Выбор типа платы
        """
        combo_board_type = self.ui.combo_board_type.currentText()
        if combo_board_type == 'offline':
            self.update_window_size()
            return
        if get_driver_attr(combo_board_type)['connect_args'] == 'com_port':
            self.show_com_settings_layout(True) # показать настройки для COM-порта
            self.update_port_list() # обновить доступные порты
            self.on_com_name_changed() # считать порт
            self.ui.label_status.setText(self.lang_pack.get("status_1"))
            if get_driver_attr(combo_board_type)['core_scan']:
                self.show_core_settings_layout(True)
            else:
                self.show_core_settings_layout(False)
        else:
            self.show_com_settings_layout(False)
            self.show_core_settings_layout(False)
            self.ui.label_status.setText(self.lang_pack.get("status"))
        self.update_window_size()

    def connect(self) -> None:
        """
        Подключение к плате
        """
        # получим данные из интерфейса о кроссбаре
        combo_cb_serial = self.ui.combo_cb_serial.currentText()
        edit_cb_serial = self.ui.edit_cb_serial.text()
        if edit_cb_serial:
            # проверить все ли поля заполнены
            cb_comment = self.ui.edit_cb_comment.text()
            bl = self.edit_cb_bl.value()
            wl = self.edit_cb_wl.value()
            cb_type = self.ui.combo_cb_type.currentText()
            if not cb_comment:
                self.ui.label_status.setText(self.lang_pack.get("status_2"))
                return
            # пытаемся создать новый
            status_add = self.parent.man.add_chip(serial = edit_cb_serial,
                                                  comment = cb_comment,
                                                  row_num = bl,
                                                  col_num = wl,
                                                  cb_type = cb_type)
            if not status_add:
                self.ui.label_status.setText(self.lang_pack.get("status_3"))
                return
            # используем новый
            self.cb_serial = edit_cb_serial
        elif combo_cb_serial:
            # используем из списка
            self.cb_serial = combo_cb_serial
        else:
            self.ui.label_status.setText(self.lang_pack.get("status_4"))
            return
        # выбираем чип
        status, _ = self.parent.man.use_chip(self.cb_serial)
        if status: # если в базе есть данные по чипу
            combo_board_type = self.ui.combo_board_type.currentText()
            self.parent.man.init_board(combo_board_type)  # Initializing board in manager
            if self.parent.man.cb_type != 'simulator':
                # попытка подключения
                if combo_board_type == 'offline':
                    self.parent.ui.button_rram.setEnabled(False)
                    self.parent.ui.button_net.setEnabled(False)
                    self.parent.ui.button_tests.setEnabled(False)
                    self.parent.ui.button_math.setEnabled(False)
                    self.accept_connet()
                else:
                    if get_driver_attr(combo_board_type)['connect_args'] == 'com_port':
                        if get_driver_attr(combo_board_type)['core_scan']:
                            if self.core_scanned:
                                connected_flag = self.parent.man.connect(com_port=self.com_port, addr=self.addr, pico=self.pico)
                            else:
                                self.ui.label_status.setText("Core не выбран")    
                                return
                        connected_flag = self.parent.man.connect(com_port=self.com_port)
                    else:
                        connected_flag = self.parent.man.connect()
                    if connected_flag:
                        self.accept_connet()
                    else:
                        message = self.lang_pack.get("board_error") + str(combo_board_type)
                        self.ui.label_status.setText(message)
            else:
                connected_flag = self.parent.man.connect()
                if connected_flag:
                    self.accept_connet()
                else:
                    self.ui.label_status.setText(self.lang_pack.get("status_5"))
        else:    
            self.ui.label_status.setText('Не могу получить данные из БД!')

    def accept_connet(self) -> None:
        """
        Успешный коннект
        """
        # todo: перенести в crossbar.py
        # обновляем конфиг
        self.parent.man.save_settings(last_crossbar_serial = self.cb_serial,
                                      com_port = self.com_port,
                                      board_type = self.parent.man.board_type)
        # продолжим работу
        self.connect_flag = True
        self.ui.label_status.setText("Успешно!")
        # все сопротивления
        self.parent.number_cells = self.parent.man.col_num*self.parent.man.row_num
        self.parent.all_resistances = [[0 for _ in range(self.parent.man.col_num)] for _ in range(self.parent.man.row_num)]
        self.close()

    def core_scan(self):
        """
        Сканирование CORE
        """
        try:
            from MemriCORE.Pico_PC.pico_client import PicoClient  # type: ignore
            pico = PicoClient.over_serial(self.com_port, 115200)
            addrs = pico.scan()
            for addr in addrs:
                self.ui.combo_core_name.addItem(
                    f'0x{addr:02X}',
                    addr
                )
            self.pico = pico
            self.core_scanned = True
        except ImportError:
            print("Нет драйвера PicoClient")
        except Exception as e:
            print(f"Ошибка при инициализации CORE: {e}")

    def closeEvent(self, event): # pylint: disable=C0103,W0613
        """
        Закрытие окна подключения
        """
        if self.connect_flag:
            self.parent.close_modal_flag = False
            self.parent.fill_table() # заполнить таблицу
            self.parent.color_table() # раскрасить ячейки
            self.parent.show() # показываем родительское окно
            event.accept()
        else:
            answer = show_choose_window(self, self.lang_pack.get("quit_now"))
            if answer:
                self.parent.close_modal_flag = True
                self.parent.close() # вызывает выход функцией родительского окна
                event.accept()
            else:
                event.ignore()
