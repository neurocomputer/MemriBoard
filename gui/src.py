"""
Вспомогательные окна и функции
"""

# pylint: disable=E0611

import csv
import matplotlib.pyplot as plt
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

def choose_cells(filepath, wl_max, bl_max):
    """
    Выбор ячеек
    """
    cells = []
    message = ''
    with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Пропускаем заголовок
        # Проверяем, что в заголовке есть нужные колонки.
        if header != ['wl', 'bl']:
            raise ValueError("Файл CSV должен иметь столбцы 'wl' и 'bl' в указанном порядке")
        for row in reader:
            try:
                if len(row) > 2:
                    raise ArithmeticError("В строке больше 2-х значений")
                else:
                    wl = int(row[0]) # Преобразуем в число
                    bl = int(row[1])
                    if wl > wl_max or bl > bl_max:
                        raise ArithmeticError("WL или BL имеют не корректное значение")
                    if [wl, bl] not in cells: # Без дубликатов
                        cells.append((wl, bl)) # Заполняем список
            except (ValueError, IndexError):
                message = f"Ошибка при преобразовании строки в числа: {row}"
            except ArithmeticError as e:
                message = f"Ошибка: {e}"
            continue # переходим к следующей строке
    return cells, message

def write_csv_data(fpath, header, coordinates):
    """
    Записать координаты ячеек
    """
    with open(fpath, 'w',newline='', encoding='utf-8') as file:
        file_wr = csv.writer(file, delimiter=",")
        file_wr.writerow(header)
        for item in coordinates:
            file_wr.writerow(item)

def snapshot(data) -> None:
    """
    Картинка с кнопки снимок
    """
    plt.clf()
    if data is not None:
        plt.imshow(data)
        plt.show()
