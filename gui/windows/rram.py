"""
Окно работы с rram
"""

import os
import shutil
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtGui import QPixmap
from copy import deepcopy
from gui.src import show_warning_messagebox

class Rram(QDialog):
    """
    Работа с rram
    """

    GUI_PATH = os.path.join("gui","uies","rram.ui")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        # загрузка ui
        self.ui = uic.loadUi(self.GUI_PATH, self)
        # доп настройки
        self.setModal(True)
        # значения по умолчанию
        self.set_up_init_values()
        # обработчики кнопок
        self.ui.button_apply_tresh.clicked.connect(self.apply_tresh)
        self.ui.button_read.clicked.connect(self.parent.read_cell_all)
        self.ui.button_save_img.clicked.connect(self.save_heatmap)
        self.ui.button_save.clicked.connect(self.save_text)
        self.ui.button_load.clicked.connect(self.load_text)

    def set_up_init_values(self) -> None:
        """
        Установка значений по умолчанию
        """
        self.ui.button_interrupt.setEnabled(False)
        self.ui.text_write.clear()
        self.ui.text_read.clear()
        self.parent._snapshot(mode="rram", data=self.parent.snapshot)
        self.ui.label_rram_img.setPixmap(QPixmap(os.path.join("gui","uies","rram.png")))

    def apply_tresh(self) -> None:
        """
        Применение порога
        """
        tresh = self.ui.spin_tresh_read.value()
        rram_data = deepcopy(self.parent.all_resistances)
        for i in range(len(rram_data)):
            for j in range(len(rram_data[i])):
                if rram_data[i][j] >= tresh:
                    rram_data[i][j] = 1
                else:
                    rram_data[i][j] = 0
        self.parent._snapshot(mode="rram", data=rram_data)
        self.ui.label_rram_img.setPixmap(QPixmap(os.path.join("gui","uies","rram.png")))

    def save_heatmap(self) -> None:
        """
        Сохранение снимка
        """
        save_path = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
        save_path = os.path.join(save_path, "heatmap.png")
        picture_path = os.path.join("gui","uies","rram.png")
        shutil.copy(picture_path, save_path)
        show_warning_messagebox('Снимок сохранен в ' + save_path)

    def save_text(self) -> None:
        """
        Сохранение текста из поля ввода в файл
        """
        text = self.ui.text_read.toPlainText()
        if text:
            save_file = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
            save_file = os.path.join(save_file, "rram.txt")
            if save_file:
                with open(save_file, "w") as f:
                    f.write(text)
                    f.close()
                show_warning_messagebox("Сохранено в " + save_file)
        else:
            show_warning_messagebox("Нечего сохранять!")

    def load_text(self) -> None:
        """
        Загрузка текста из файла в поле ввода
        """
        load_file, _ = QFileDialog.getOpenFileName(self, 'Открыть файл', ".", "Текстовые файлы (*.txt)")
        if load_file:
            with open(load_file, "r+") as f:
                text = f.read()
                f.close()
            if text:
                self.ui.text_write.insertPlainText(text)
            else:
                show_warning_messagebox("Файл " + load_file + " пуст!")