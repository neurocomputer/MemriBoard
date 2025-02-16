"""
Окно подключения
"""

# pylint: disable=E0611,C0301

import os
from sys import platform
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtSerialPort import QSerialPortInfo

from gui.src import show_choose_window

class ConnectDialog(QDialog):
    """
    Окно подключения
    """

    GUI_PATH = os.path.join("gui","uies","connect.ui")
    connect_flag = False
    cb_serial: str
    com_port: str

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.setModal(True)
        self.show_new_cb_layout(False)
        # обработки кнопок
        self.ui.button_update.clicked.connect(self._update_port_list)
        self.ui.button_connect.clicked.connect(self._connect)
        self.ui.button_quit.clicked.connect(self.close)
        self.ui.button_settings.clicked.connect(self._settings)
        self.ui.button_new_crossbar.clicked.connect(lambda: self.show_new_cb_layout(True))
        # обработка комбо
        self.ui.combo_com_name.currentIndexChanged.connect(self.on_com_name_changed)
        self.ui.edit_com_name.textChanged.connect(self.on_com_name_changed)
        # обновление отображения
        self._update_port_list()
        self.on_com_name_changed()
        self.ui.combo_cb_type.setEnabled(False)
        self.ui.combo_cb_serial.clear()
        self.ui.combo_cb_serial.addItems([self.parent.man.ap_config["gui"]["last_crossbar_serial"],])
        # обновление спинбоксов
        self.edit_cb_bl.valueChanged.connect(self.on_edit_cb_wl_bl_changed)
        self.edit_cb_wl.valueChanged.connect(self.on_edit_cb_wl_bl_changed)

    def on_edit_cb_wl_bl_changed(self) -> None:
        """
        Задание WL, BL
        """
        bl = self.edit_cb_bl.value()
        wl = self.edit_cb_wl.value()
        if bl > 1 or wl > 1:
            self.ui.combo_c_type.setCurrentText('memardboard_crossbar')

    def on_com_name_changed(self) -> None:
        """
        Выбрали порт
        """
        combo_com_name = self.ui.combo_com_name.currentText()
        edit_com_name = self.ui.edit_com_name.text()
        # адрес COM порта
        if edit_com_name: # адрес введен вручную
            self.com_port = combo_com_name
        else: # адрес в списке
            self.com_port = combo_com_name
        # обновляем списки
        if self.com_port == 'simulator':
            self._update_crossbar_list('simulator')
            self.ui.combo_cb_type.setCurrentText('simulator')
        else:
            self._update_crossbar_list('real')
            self.ui.combo_cb_type.setCurrentText('real')

    def show_new_cb_layout(self, state) -> None:
        """
        Показать настройки нового кроссбара
        """
        self.ui.edit_cb_serial.setVisible(state)
        self.ui.edit_cb_comment.setVisible(state)
        self.ui.edit_cb_bl.setVisible(state)
        self.ui.edit_cb_wl.setVisible(state)
        self.ui.combo_cb_type.setVisible(state)
        self.ui.combo_c_type.setVisible(state)
        self.ui.label_4.setVisible(state)
        self.ui.label_5.setVisible(state)
        self.ui.label_6.setVisible(state)
        self.ui.label_7.setVisible(state)
        self.ui.label_8.setVisible(state)
        self.ui.label_9.setVisible(state)
        self.adjustSize()

    def _settings(self) -> None:
        """
        Настройки
        """
        self.parent.show_settings_dialog()

    def _update_port_list(self) -> None:
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
        port_list.append("simulator")
        port_list.append("offline")
        port_list.insert(0, self.parent.man.ap_config["connector"]["com_port"]) # default
        self.ui.combo_com_name.clear()
        self.ui.combo_com_name.addItems(port_list)

    def _update_crossbar_list(self, cb_type: str) -> None:
        """
        Обновление списка кроссбаров
        """
        # список кроссбаров
        status, cb_list = self.parent.man.db.get_cb_list_cb_type(cb_type)
        if status:
            self.ui.combo_cb_serial.clear()
            self.ui.combo_cb_serial.addItems(cb_list)

    def _connect(self) -> None:
        """
        Подключение к плате
        """
        if self.com_port == 'choose...':
            self.ui.label_status.setText('Выберете порт для подключения!')
        else:
            # получим данные из интерфейса о кроссбаре
            combo_cb_serial = self.ui.combo_cb_serial.currentText()
            edit_cb_serial = self.ui.edit_cb_serial.text()
            if edit_cb_serial:
                # проверить все ли поля заполнены
                cb_comment = self.ui.edit_cb_comment.text()
                bl = self.edit_cb_bl.value()
                wl = self.edit_cb_wl.value()
                cb_type = self.ui.combo_cb_type.currentText()
                c_type = self.ui.combo_c_type.currentText()
                if not cb_comment:
                    self.ui.label_status.setText('Добавьте коммент!')
                    return
                # пытаемся создать новый
                status_add = self.parent.man.add_chip(serial = edit_cb_serial,
                                                    comment = cb_comment,
                                                    row_num = bl,
                                                    col_num = wl,
                                                    cb_type = cb_type,
                                                    c_type = c_type)
                if not status_add:
                    self.ui.label_status.setText('Ошибка добавления в БД! Возможно такое устройство уже есть!')
                    return
                # используем новый
                self.cb_serial = edit_cb_serial
            elif combo_cb_serial:
                # используем из списка
                self.cb_serial = combo_cb_serial
            else:
                self.ui.label_status.setText('Выберете кроссбар!')
                return
            # выбираем чип
            _, _ = self.parent.man.use_chip(self.cb_serial)
            # попытка подключения
            if self.com_port == 'offline':
                self.accept_connet()
            elif self.parent.man.connect(self.com_port):
                self.accept_connet()
            else:
                message = f"К порту \"{self.com_port}\" нет подключения!"
                self.ui.label_status.setText(message)

    def accept_connet(self) -> None:
        """
        Успешный коннект
        """
        # todo: перенести в crossbar.py
        # обновляем конфиг
        self.parent.man.save_settings(last_crossbar_serial = self.cb_serial,
                                      com_port = self.com_port,
                                      c_type = self.parent.man.c_type)
        # продолжим работу
        self.connect_flag = True
        self.ui.label_status.setText("Успешно!")
        # все сопротивления
        self.parent.number_cells = self.parent.man.col_num*self.parent.man.row_num
        self.parent.all_resistances = [[0 for _ in range(self.parent.man.col_num)] for _ in range(self.parent.man.row_num)]
        # if self.com_port != 'simulator': #todo: починить
        #     self.parent.check_connection_start() # проверка подключения порта по таймеру
        self.close()

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
            answer = show_choose_window(self, 'Выходим?')
            if answer:
                self.parent.close_modal_flag = True
                self.parent.close() # вызывает выход функцией родительского окна
                event.accept()
            else:
                event.ignore()
