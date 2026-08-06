"""
Вспомогательные окна и функции
"""

# pylint: disable=E0611

import csv
from typing import Union
import pandas as pd
import json
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from manager.service import d2v, a2r


lang_pack: dict = {}  # Language for src functions

def change_src_language(new_lang_pack) -> None:
    """
    Change lang pack, called from crossbar window on language change.
    """
    global lang_pack
    lang_pack = new_lang_pack

def show_warning_messagebox(parent = None, message: Union[str, None] = None) -> None:
    """
    Оповещение
    """
    QMessageBox.warning(parent, lang_pack.get('warn'), message, QMessageBox.Ok)

def show_choose_window(parent = None, message: Union[str, None] = None) -> bool:
    """
    Окно выбора
    """
    answer = 0
    reply = QMessageBox.question(parent,
                                 lang_pack.get("confirm"),
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
        answer = lang_pack.get("done")
    elif value == 2:
        answer = lang_pack.get("interrupted")
    elif value == 0 or value is False:
        answer = lang_pack.get("not_done")
    return answer

def open_file_dialog(parent, file_types="All Files (*);;Text Files (*.txt);;CSV Files (*.csv)"):
    """
    Окно выбора файлов
    """
    file_path, _ = QFileDialog.getOpenFileName(parent,
                                               lang_pack.get("pick_file"),
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
            raise ValueError(lang_pack.get("wl_bl_order_wrong"))
        for row in reader:
            try:
                if len(row) > 2:
                    raise ArithmeticError(lang_pack.get("more_than_2_values"))
                else:
                    wl = int(row[0]) # Преобразуем в число
                    bl = int(row[1])
                    if wl > wl_max or bl > bl_max:
                        raise ArithmeticError(lang_pack.get("wl_bl_incorrect"))
                    if [wl, bl] not in cells: # Без дубликатов
                        cells.append((wl, bl)) # Заполняем список
            except (ValueError, IndexError):
                message = lang_pack.get("string_to_int_error") + str(row)
            except ArithmeticError as e:
                message = lang_pack.get("error") + e
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

def save_matrix_text_format(filename: str, data: list, sep: str = '\t') -> None:
    """Save matrix in a text document where sep is the column separator"""
    with open(filename, 'w') as file:
        file.write(f'   {sep}' + sep.join([f'WL{i}' for  i in range(len(data[0]))]) + '\n')
        file.writelines(f'BL{j}{sep}' + sep.join(map(str, row)) + '\n' for j, row in enumerate(data))
  

def save_matrix_txt(filename: str, data: list) -> None:
    """Save matrix as txt"""
    save_matrix_text_format(filename, data, sep='\t')  
  
    
def save_matrix_csv(filename: str, data: list) -> None:
    """Save matrix as csv"""
    header = ['   '] + [f'WL{i}' for  i in range(len(data[0]))]
    for i in range(len(data)):
        data[i] = [f'BL{i}'] + data[i]
    write_csv_data(filename, header, data)
    
    
def save_matrix_json(filename: str, data: list) -> None:
    """Save matrix as json"""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    
    
def save_matrix_xlsx(filename: str, data: list) -> None:
    """Save matrix as xls or xlsx"""
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
    

def convert_ticket_to_reduced_format(manager, ticket: dict, mode_to_convert: str = 'volt_sweep') -> dict:
    """Convert ticket from old (full) format to reduced format (for backwards compatibility)"""
    if mode_to_convert not in ['volt_sweep', 'endurance', 'pot-dep', 'retention']:
        raise RuntimeError(f'Converting ticket to reduced format: unknown mode {mode_to_convert}')
    new_ticket = {
        'name': ticket['name'],
        'mode': mode_to_convert,
        'params': {},
        'terminate': {}
    }
    if mode_to_convert == 'volt_sweep':
        # Sweep
        new_ticket['params']['start_dir'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_dir_strt_inc'])
        new_ticket['params']['stop_dir'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_dir_stop_inc'])
        new_ticket['params']['step_dir'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_dir_step_inc'])
        new_ticket['params']['start_rev'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_rev_strt_inc'])
        new_ticket['params']['stop_rev'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_rev_stop_inc'])
        new_ticket['params']['step_rev'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_rev_step_inc'])
        # Time
        new_ticket['params']['pulse_width_dir'] = ticket['params']['t_dir_msec_inc'] * 1e-3 + ticket['params']['t_dir_usec_inc'] * 1e-6
        new_ticket['params']['pulse_width_rev'] = ticket['params']['t_rev_msec_inc'] * 1e-3 + ticket['params']['t_rev_usec_inc'] * 1e-6
        # Sweep params
        new_ticket['params']['amount_dir'] = ticket['params']['dir_inc_countr']
        new_ticket['params']['amount_rev'] = ticket['params']['rev_inc_countr']
        new_ticket['params']['double_dir'] = bool(ticket['params']['dir_dec_countr'])
        new_ticket['params']['double_rev'] = bool(ticket['params']['rev_dec_countr'])
    elif mode_to_convert in ['endurance', 'pot-dep']:
        # Amplitude
        new_ticket['params']['amplitude_dir'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_dir_stop_inc'])
        new_ticket['params']['amplitude_rev'] = d2v(manager.dac_bit, manager.vol_ref_dac, ticket['params']['v_rev_stop_inc'])
        # Time
        new_ticket['params']['pulse_width_dir'] = ticket['params']['t_dir_msec_inc'] * 1e-3 + ticket['params']['t_dir_usec_inc'] * 1e-6
        new_ticket['params']['pulse_width_rev'] = ticket['params']['t_rev_msec_inc'] * 1e-3 + ticket['params']['t_rev_usec_inc'] * 1e-6
        # Amount params
        new_ticket['params']['amount_dir'] = ticket['params']['dir_inc_countr']
        new_ticket['params']['amount_rev'] = ticket['params']['rev_inc_countr']
    elif mode_to_convert == 'retention':
        pass  # No parameters
    # Other values
    for key in ['count', 'reverse', 'id', 'wl', 'bl']:
        new_ticket['params'][key] = ticket['params'][key]
    # Terminators
    new_ticket['terminate']['type'] = ticket['terminate']['type']
    if hasattr(ticket['terminate']['value'], '__iter__'):  # Two-value terminator
        new_term = []
        for term in ticket['terminate']['value']:
            new_term.append(
                int(a2r(manager.gain,
                        manager.res_load,
                        manager.vol_read,
                        manager.adc_bit,
                        manager.vol_ref_adc,
                        manager.res_switches,
                        term))
            )
    else:
        new_term = int(a2r(manager.gain,
                           manager.res_load,
                           manager.vol_read,
                           manager.adc_bit,
                           manager.vol_ref_adc,
                           manager.res_switches,
                           ticket['terminate']['value']))
    new_ticket['terminate']['value'] = new_term
    return new_ticket        
    