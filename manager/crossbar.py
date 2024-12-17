"""
Класс для работы с кроссбаром
Возможно развивать в сторону расширения функционала
работы именно с кроссбаром
"""

import os
import json
from manager import Manager
from manager.service.global_settings import TICKET_PATH

class CrossbarManager(Manager):
    """
    Менеджер кроссбара
    """

    flag_mem_open: bool = False # флаг открытия ячейки

    def send_ticket_all(self, ticket):
        """
        Послать одинаковый тикет на все ячейки
        """
        counter = 0
        for i in range(self.col_num):
            for j in range(self.row_num):
                ticket["params"]["wl"] = i
                ticket["params"]["bl"] = j
                ticket["params"]["id"] = counter
                self.send_ticket(ticket)
                counter += 1

    def read_one_cell(self, wl, bl):
        """
        Прочитать значение одной ячейки
        """
        ticket_name = self.ap_config['gui']['measure_ticket']
        fname = os.path.join(TICKET_PATH, ticket_name)
        with open(fname, encoding='utf-8') as file:
            ticket = json.load(file)

    def open_mem(self, wl: int, bl: int):
        """
        Открыть заданную строку и столбец
        """
        _ = self.conn.push(f'3,{int(wl)},{int(bl)},0\n')
        self.flag_mem_open = True # поднимаем флаг

    def close_mem(self):
        """
        Закрыть доступ к строке и столбцу
        """
        _ = self.conn.push('4,0\n')
        self.flag_mem_open = False # опускаем флаг
