"""
Вспомогательные окна и функции
"""

# pylint: disable=E0611

import csv
import pandas as pd  # TODO: add to requirements + xlsxwriter for save_xlsx
import json
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
    
    
# Methods for saving matrix in different formats

def save_matrix_text_format(filename: str, data: list, sep: int = '\t') -> None:
    """Save matrix in a text document where sep is the column separator"""
    with open(filename, 'w') as file:
        file.write(f'   {sep}' + sep.join([f'WL{i}' for  i in range(len(data[0]))]) + '\n')
        for j, row in enumerate(data):
            file.write(f'BL{j}{sep}' + sep.join(map(str, row)) + '\n')
  

def save_matrix_txt(filename: str, data: list) -> None:
    """Save matrix as txt"""
    save_matrix_text_format(filename, data, sep='\t')  
  
    
def save_matrix_csv(filename: str, data: list) -> None:
    """Save matrix as csv"""
    save_matrix_text_format(filename, data, sep=',')
    
    
def save_matrix_json(filename: str, data: list) -> None:
    """Save matrix as json"""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    
    
def save_matrix_xlsx(filename: str, data: list) -> None:
    """Save matrix as csv"""
    n_rows = len(data)  # bl
    n_cols = len(data[0])  # wl
    d = [[None] * n_cols] * n_rows
    df = pd.DataFrame(data=d, index = [str(i + 1) for i in range(n_rows)], 
                    columns = [str(i + 1) for i in range(n_cols)])
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    workbook  = writer.book
    worksheet = writer.sheets['Sheet1']
    centered_format = workbook.add_format({'valign': "center", 
                                            'align': "center"})
    for i in range(n_rows + 1):
        worksheet.set_row(i, 20)
        if i != 0:
            worksheet.write(i, 0, f'BL {i - 1}', centered_format)
    worksheet.set_column(0, n_cols, 7)
    for i in range(1, n_cols + 1):
        worksheet.write(0, i, f'WL {i - 1}', centered_format)
    
    for i, row in enumerate(data):
            for j, col in enumerate(row):
                 worksheet.write(i + 1, j + 1, col, centered_format)
    writer.close()