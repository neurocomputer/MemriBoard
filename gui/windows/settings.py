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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # обработка кнопок
        self.ui.button_save.clicked.connect(self.save_settings)
        self.ui.button_cancel.clicked.connect(self.close)
        self.ui.button_update.clicked.connect(self.update_settings)
        self.ui.button_add_path.clicked.connect(self.add_path)
        self.ui.button_add_writable_cells_csv.clicked.connect(self.get_writable_cells)
        # заполнение параметров
        self.fill_settings()

    def fill_settings(self) -> None:
        """
        Заполнение основных настроек
        """
        self.ui.choose_adc_bit.setCurrentText(str(self.parent.man.adc_bit))
        self.ui.choose_gain.setValue(self.parent.man.gain)
        self.ui.choose_software_cc.setValue(self.parent.man.soft_cc)
        self.ui.lineedit_backup.setText(self.parent.man.get_meta_info()["backup"])

    def save_settings(self) -> None:
        """
        Сохранение настроек
        """
        backup_path = self.ui.lineedit_backup.text()
        writable_cells = self.ui.lineedit_writable_cells.text()
        if len(backup_path) != 0:
            if platform.system() == "Linux":
                backup_path = backup_path + "/"
            elif platform.system() == "Windows":
                backup_path = backup_path + '\\'
        if not os.path.isdir(backup_path):
            backup_path = os.path.join(os.getcwd(), "base.db")[:-7]
        if len(writable_cells) != 0:
            if not os.path.isfile(writable_cells):
                writable_cells = ''
                self.ui.lineedit_writable_cells.setText(writable_cells)
        self.parent.man.save_settings(adc_bit = self.ui.choose_adc_bit.currentText(),
                                      gain = str(self.ui.choose_gain.value()),
                                      soft_cc = str(self.ui.choose_software_cc.value()),
                                      backup = backup_path,
                                      writable_cells = writable_cells)
        self.close()

    def add_path(self) -> None:
        """
        Выбрать папку для бэкапа бд
        """
        path = QFileDialog.getExistingDirectory(self, "Выберите директорию для резервного копирования")
        if path[0]:
            self.ui.lineedit_backup.setText(path[0])

    def get_writable_cells(self) -> None:
        """
        Выбор csv с рабочими ячейками
        """
        path = QFileDialog.getOpenFileName(self, "Выберите файл ячеек", filter="*.csv")
        if path[0]:
            self.ui.lineedit_writable_cells.setText(path[0])

    def update_settings(self) -> None:
        """
        Считать настройки из файла и обновить
        """
        self.parent.man.read_settings()
        self.fill_settings()

    def closeEvent(self, event):
        """
        Закрытие
        """
        event.ignore()
        self.hide()
