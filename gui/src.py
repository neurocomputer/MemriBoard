"""
Вспомогательные окна и функции
"""

# pylint: disable=E0611

from PyQt5.QtWidgets import QMessageBox, QMainWindow, QFileDialog

def show_warning_messagebox(message: str) -> None:
    """
    Оповещение
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.setWindowTitle("Предупреждение")
    msg.setStandardButtons(QMessageBox.Ok)
    _ = msg.exec_()

def show_choose_window(parent: QMainWindow, message: str) -> bool:
    """
    Окно выбора
    """
    answer = 0
    reply = QMessageBox.question(parent,
                                 'Подтверждение',
                                 message,
                                 QMessageBox.Yes | QMessageBox.No,
                                 QMessageBox.No)
    if reply == QMessageBox.Yes:
        answer = 1
    return answer

def bool_to_label(value):
    """
    Преобразование логики в текст для вывода в таблице
    """
    answer = None
    if value == 1 or value is True:
        answer = "Выполнен"
    elif value == 2:
        answer = "Прерван"
    elif value == 0 or value is False:
        answer = "Не выполнен"
    return answer

def open_file_dialog(parent, file_types="All Files (*);;Text Files (*.txt);;CSV Files (*.csv)"):
    """
    Окно выбора файлов
    """
    file_path, _ = QFileDialog.getOpenFileName(parent,
                                               "Выбрать файл",
                                               "",
                                               file_types)
    return file_path
