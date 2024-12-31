"""
Модуль взаимодействия с платой по COM порту
"""

# pylint: disable=no-name-in-module

import random
import time
from logging import Logger
from configparser import ConfigParser
from manager.comport import Serial
from manager.blanks import blanks, fill_blank, gather

class Connector():
    """
    Взаимодействие с платой по COM порту
    """

    serial: Serial
    silent: int
    logger: Logger
    config: ConfigParser
    c_type: str

    def __init__(self, silent, logger, config, c_type, cb_type):
        self.serial = Serial()
        self.silent = silent
        self.logger = logger
        self.config = config
        self.c_type = c_type
        self.cb_type = cb_type

    def _kick_board(self, attempts: int) -> bool:
        """
        Опрашиваем плату пока не ответит

        Arguments:
            attempts -- количество попыток

        Returns:
            not_rec_flag -- флаг успеха
        """
        rec_data = []
        count = 1
        not_rec_flag = False
        data = {'vol': 0,
                't_ms': 0,
                't_us': 0,
                'sign': 0,
                'id': count}
        while not rec_data:
            self.logger.info('Try %d', count)
            if count > attempts:
                not_rec_flag = True
                break
            command = gather(fill_blank(blanks[self.c_type], data))
            _ = self.push(command)
            rec_data = self.pull()
            count += 1
            data['id'] = count
        return not_rec_flag

    def open_serial(self, portnum: str) -> bool:
        """
        Открытие COM порта

        Arguments:
            portnum -- номер порта в формате 'comX'

        Returns:
            open_flag -- статус открытия
        """
        open_flag = False
        if self.cb_type == 'simulator':
            open_flag = True
        else:
            # кол-во попыток получить данные
            attempts = int(self.config['connector']['attempts_to_kick'])
            self.serial.com_open(portnum, timeout=float(self.config["connector"]["timeout"]))
            if self.serial.com_is_open():
                not_rec_flag = self._kick_board(attempts)
                if not_rec_flag:
                    self.logger.info('Fail to receive %s', portnum)
                else:
                    self.logger.info('Opened %s', portnum)
                    open_flag = True
            else:
                self.logger.info('Fail to open %s', portnum)
        return open_flag

    def close_serial(self) -> bool:
        """
        Закрыть COM порт

        Returns:
            close_flag -- статус закрытия
        """
        close_flag = False
        self.serial.com_close()
        if self.serial.com_is_open():
            self.logger.info('Fail to close')
        else:
            self.logger.info('Closed')
            close_flag = True
        return close_flag

    def push(self, send_data: str) -> bool:
        """
        Функция отправки данных

        Arguments:
            data -- данные для отправки

        Returns:
            send_flag -- статус отправки
        """
        #start_time = time.time()
        send_flag = False
        if self.serial.com_is_open():
            if not self.silent:
                self.logger.info('Send %s', send_data.rstrip())
            check = self.serial.com_write(send_data.encode())
            if check == -1:
                if not self.silent:
                    self.logger.warning('Fail to send data')
                send_flag = False
            else:
                if not self.silent:
                    self.logger.info('Data sent')
                send_flag = True
        else:
            if not self.silent:
                self.logger.critical('Port isnt opened')
            send_flag = False
        #print(time.time() - start_time)
        return send_flag

    def pull(self) -> list:
        """
        Функция приема данных по COM порту

        Returns:
            rec_data -- принятые данные
        """
        #start_time = time.time()
        rec_data = []
        self.serial.com_whait_ready(float(self.config['connector']['timeout']))
        if self.serial.com_can_read_line():
            rx = self.serial.com_read_line()
            # print("rx",rx)
            # порезать и разбить по запятым
            try:
                rec_data = list(map(int, str(rx, 'utf-8').strip().split(',')))
            except ValueError:
                pass
            except TypeError:
                pass
            # записать в журнал
            if not self.silent:
                self.logger.info('Recieved data: %s', rx)
        #print(time.time() - start_time)
        return tuple(rec_data)

    def get_tech_info(self):
        """
        Получить техническую информацию
        """
        rec_data = []
        send_flag = self.push('100\n')
        self.serial.com_whait_ready(float(self.config['connector']['timeout']))
        if self.serial.com_can_read_line():
            rx = self.serial.com_read_line()
            try:
                rec_data = str(rx, 'utf-8').strip().split(',')
            except ValueError:
                pass
        return send_flag, rec_data

    def impact(self, task: dict):
        """
        Подача команды плате

        Arguments:
            task -- команда для платы

        Returns:
            res -- результат команды
        """
        # работа с реальным кроссбаром
        if self.cb_type == 'real':
            _ = self.push(gather(task))
            try:
                res = self.pull()
            except ValueError:
                self.logger.critical('ValueError in board.py:pull!')
        # режим симулятор
        elif self.cb_type == 'simulator':
            task_id = task["id"]
            task = gather(task) # собираем из словаря строку
            if not self.silent:
                self.logger.info('Send %s', task.rstrip())
            res = (random.randint(0,2**int(self.config['board']['adc_bit'])), task_id)
            time.sleep(0.06)
            if not self.silent:
                self.logger.info('Recieved data: %s', str(res))
        # можно добавить работу с другими платами
        return res

    def custom_impact(self, command: str, timeout: float, attempts: int):
        """
        Кастомная команда для отладки

        Arguments:
            command -- команда которая посылается на плату

        Returns:
            res -- результат команды
        """
        # работа с реальным кроссбаром
        if self.cb_type == 'real':
            _ = self.push(command)
            while attempts:
                time.sleep(timeout)
                try:
                    res = self.pull()
                    if len(res) == 2:
                        break
                except ValueError:
                    self.logger.critical('ValueError in board.py:pull!')
                attempts -= 1
                if attempts == 0:
                    break
        # режим симулятор
        elif self.cb_type == 'simulator':
            time.sleep(timeout)
            res = (random.randint(0,2**int(self.config['board']['adc_bit'])), 0)
        # можно добавить работу с другими платами
        return res
