"""
Окно настроек
"""

# pylint: disable=E0611, C0103, R0903, W0212

import os
import platform
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog

class Settings(QDialog):
    """
    Окно настроек
    """

    GUI_PATH = os.path.join("gui","uies","settings.ui")
    lang_pack = {}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        self.change_language()
        # доп настройки
        self.setModal(True)
        # logging levels
        log_items = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        self.ui.comboBox_app_log.addItems(log_items)
        self.ui.comboBox_db_log.addItems(log_items)
        # обработка кнопок
        self.ui.button_save.clicked.connect(self.save_settings)
        self.ui.button_cancel.clicked.connect(self.close)
        self.ui.button_update.clicked.connect(self.update_settings)
        self.ui.button_add_path.clicked.connect(self.add_path)
        self.ui.button_add_writable_cells_csv.clicked.connect(self.get_writable_cells)
        # заполнение параметров
        self.fill_settings()

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
            self.ui.groupBox_logging.setTitle(self.lang_pack.get("logging"))
            self.ui.label_app_log.setText(self.lang_pack.get("app_log"))
            self.ui.label_db_log.setText(self.lang_pack.get("db_log"))
            self.ui.label_app_log_level.setText(self.lang_pack.get("level"))
            self.ui.label_db_log_level.setText(self.lang_pack.get("level"))
            self.ui.checkBox_app_log.setText(self.lang_pack.get("rewrite_file"))
            self.ui.checkBox_db_log.setText(self.lang_pack.get("rewrite_file"))

    def fill_settings(self) -> None:
        """
        Заполнение основных настроек
        """
        self.ui.choose_adc_bit.setCurrentText(str(self.parent.man.adc_bit))
        self.ui.choose_gain.setValue(self.parent.man.gain)
        self.ui.choose_software_cc.setValue(self.parent.man.soft_cc)
        app_meta_info: dict = self.parent.man.get_meta_info()
        self.ui.lineedit_backup.setText(app_meta_info["backup"])
        self.ui.lineedit_writable_cells.setText(app_meta_info["writable_cells"])
        if self.parent.man.get_meta_info()["language"] in ["English", "Русский"]:
            self.ui.choose_language.setCurrentText(app_meta_info["language"])
        self.ui.comboBox_app_log.setCurrentText(app_meta_info["app_logging_level"])
        self.ui.comboBox_db_log.setCurrentText(app_meta_info["db_logging_level"])
        self.ui.checkBox_app_log.setChecked(bool(app_meta_info["app_log_rewrite_on_start"]))
        self.ui.checkBox_app_log.setChecked(bool(app_meta_info["db_log_rewrite_on_start"]))

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
                                      language = language,
                                      app_logging_level=self.ui.comboBox_app_log.currentText(),
                                      db_logging_level=self.ui.comboBox_db_log.currentText(),
                                      app_log_rewrite_on_start=str(int(self.ui.checkBox_app_log.isChecked())),
                                      db_log_rewrite_on_start=str(int(self.ui.checkBox_db_log.isChecked())))                          
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
