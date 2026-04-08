"""
Окно настроек
"""

# pylint: disable=E0611, C0103, R0903, W0212

import os
import platform
import requests
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog

class Settings(QDialog):
    """
    Окно настроек
    """

    GUI_PATH = os.path.join("gui","uies","settings.ui")
    lang_pack = {}
    uri: str

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        # доп настройки
        self.setModal(True)
        # обработка кнопок
        self.ui.button_save.clicked.connect(self.save_settings)
        self.ui.button_cancel.clicked.connect(self.close)
        self.ui.button_update.clicked.connect(self.update_settings)
        self.ui.button_add_path.clicked.connect(self.add_path)
        self.ui.button_add_writable_cells_csv.clicked.connect(self.get_writable_cells)
        self.ui.button_connect.clicked.connect(self.connect)
        self.ui.button_get_all.clicked.connect(self.get_all)
        self.ui.button_get_task.clicked.connect(self.get_task)
        self.ui.button_get_result.clicked.connect(self.get_result)
        self.ui.button_disconnect.clicked.connect(self.disconnect)
        # заполнение параметров
        self.uri = '127.0.0.1:5000'
        self.fill_settings()
        self.activate_buttons(False)

    def activate_buttons(self, mode):
        self.ui.button_get_task.setEnabled(mode)
        self.ui.button_get_result.setEnabled(mode)
        self.ui.button_get_all.setEnabled(mode)

    def connect(self):
        self.uri = 'http://' + self.ui.lineedit_uri.text()
        try:
            self.ui.text_log.append(f'Подключение к {self.uri}')
            response = requests.get(self.uri + '/ping')
            if response.status_code == 200:
                self.ui.text_log.append(f'Успех')
                self.activate_buttons(True)
            else:
                self.ui.text_log.append(f'Ошибка')
                self.activate_buttons(False)
        except Exception as e:
            self.ui.text_log.append(f'Ошибка: {e}')

    def get_all(self):
        response = requests.get(self.uri + "/get_all")
        if response.status_code == 200:
            data = response.json()
            self.ui.text_log.append(f"Data: {data.get('data', [])}")

    def get_task(self):
        response = requests.get(self.uri + "/get_task")
        if response.status_code == 200:
            data = response.json()
            self.ui.text_log.append(f'Task: {data.get('data', [])}')

    def get_result(self):
        response = requests.get(self.uri + "/get_result")
        if response.status_code == 200:
            data = response.json()
            self.ui.text_log.append(f'Result: {data.get('data', [])}')
    
    def disconnect(self):
        self.ui.text_log.clear()
        self.close()

    def change_language(self):
        """
        Изменение языка интерфейса
        """
        ok, self.lang_pack = self.parent.read_language_json("settings")
        if ok:
            self.ui.setWindowTitle(self.lang_pack.get("name"))
            self.ui.label_3.setText(self.lang_pack.get("update_from_ini_file"))
            self.ui.button_update.setText(self.lang_pack.get("update_button"))
            self.ui.label.setText(self.lang_pack.get("capacity"))
            self.ui.label_6.setText(self.lang_pack.get("bits"))
            self.ui.label_2.setText(self.lang_pack.get("caliber_coef"))
            self.ui.label_5.setText(self.lang_pack.get("program_cc"))
            self.ui.label_7.setText(self.lang_pack.get("a"))
            self.ui.label_4.setText(self.lang_pack.get("db_savepath"))
            self.ui.label_8.setText(self.lang_pack.get("working_cells_filepath"))
            self.ui.label_9.setText(self.lang_pack.get("language"))
            self.ui.button_save.setText(self.lang_pack.get("save"))
            self.ui.button_cancel.setText(self.lang_pack.get("cancel"))

    def fill_settings(self) -> None:
        """
        Заполнение основных настроек
        """
        self.ui.choose_adc_bit.setCurrentText(str(self.parent.man.adc_bit))
        self.ui.choose_gain.setValue(self.parent.man.gain)
        self.ui.choose_software_cc.setValue(self.parent.man.soft_cc)
        self.ui.lineedit_backup.setText(self.parent.man.get_meta_info()["backup"])
        self.ui.lineedit_writable_cells.setText(self.parent.man.get_meta_info()["writable_cells"])
        if self.parent.man.get_meta_info()["language"] in ["English", "Русский"]:
            self.ui.choose_language.setCurrentText(self.parent.man.get_meta_info()["language"])

    def save_settings(self) -> None:
        """
        Сохранение настроек
        """
        backup_path = self.ui.lineedit_backup.text()
        writable_cells = self.ui.lineedit_writable_cells.text()
        language = self.ui.choose_language.currentText()
        if len(backup_path) != 0:
            if platform.system() == "Linux" and backup_path[len(backup_path)-1] != "/":
                backup_path = backup_path + "/"
            elif platform.system() == "Windows" and backup_path[len(backup_path)-1] != '\\':
                backup_path = backup_path + '\\'
        if not os.path.isdir(backup_path):
            backup_path = os.path.join(os.getcwd(), "base.db")[:-7]
        if len(writable_cells) != 0:
            if not os.path.isfile(writable_cells):
                writable_cells = ''
        self.parent.man.save_settings(adc_bit = self.ui.choose_adc_bit.currentText(),
                                      gain = str(self.ui.choose_gain.value()),
                                      soft_cc = str(self.ui.choose_software_cc.value()),
                                      backup = backup_path,
                                      writable_cells = writable_cells,
                                      language = language)
        if self.parent.connect_dialog:
            self.parent.connect_dialog.change_language()
        self.parent.change_language()
        self.close()

    def add_path(self) -> None:
        """
        Выбрать папку для бэкапа бд
        """
        path = QFileDialog.getExistingDirectory(self, self.lang_pack.get("pick_backup"))
        if path[0]:
            self.ui.lineedit_backup.setText(path[0])

    def get_writable_cells(self) -> None:
        """
        Выбор csv с рабочими ячейками
        """
        path = QFileDialog.getOpenFileName(self, self.lang_pack.get("pick_cells"), filter="*.csv")
        if path[0]:
            self.ui.lineedit_writable_cells.setText(path[0])

    def update_settings(self) -> None:
        """
        Считать настройки из файла и обновить
        """
        self.parent.man.read_settings()
        self.fill_settings()

    def showEvent(self, event):
        event.ignore()
        self.change_language()

    def closeEvent(self, event):
        """
        Закрытие
        """
        event.ignore()
        self.hide()
