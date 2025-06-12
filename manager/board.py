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
from manager.service import d2v
from simulator.src import load_crossbar_array, send_task_to_crossbar

class Connector():
    """
    Взаимодействие с платой по COM порту
    """

    serial: Serial
    silent: int
    logger: Logger
    config: ConfigParser
    c_type: str
    # для симулятора
    crossbar_array: list
    crossbar_serial: str
    request_id: int = 0

    def __init__(self, silent, logger, config, c_type, cb_type, **kwargs):
        self.serial = Serial()
        self.silent = silent
        self.logger = logger
        self.config = config
        self.c_type = c_type
        self.cb_type = cb_type
        # self.cb_type = 'raspberry'
        # для симулятора
        if 'crossbar_serial' in kwargs:
            self.crossbar_serial = kwargs['crossbar_serial']

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
            # загрузка симулятора
            open_flag, self.crossbar_array = load_crossbar_array(self.crossbar_serial)
        elif self.cb_type == 'real':
            # для плат на базе Arduino
            if self.c_type == 'memardboard_single' or self.c_type == 'memardboard_crossbar':
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
            # для плат на базе Raspberry Pi
            elif self.c_type == 'memricore':
                from MemriCORE.rpi_modes import RPI_modes
                self.rasp_driver = RPI_modes()
                open_flag = True
        return open_flag

    def close_serial(self) -> bool:
        """
        Закрыть COM порт

        Returns:
            close_flag -- статус закрытия
        """
        close_flag = False
        if self.cb_type == 'simulator':
            close_flag = True
        elif self.cb_type == 'real':
            # для плат на базе Arduino
            if self.c_type == 'memardboard_single' or self.c_type == 'memardboard_crossbar':
                self.serial.com_close()
                if self.serial.com_is_open():
                    self.logger.info('Fail to close')
                else:
                    self.logger.info('Closed')
                    close_flag = True
            # для плат на базе Raspberry Pi
            elif self.c_type == 'memricore':
                #todo: может нужно что-то еще
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
        # работа с реальным кроссбаром
        rec_data = []
        send_flag = False
        if self.cb_type == 'real':
            if self.c_type == 'memardboard_single' or self.c_type == 'memardboard_crossbar':
                send_flag = self.push('100\n')
                self.serial.com_whait_ready(float(self.config['connector']['timeout']))
                if self.serial.com_can_read_line():
                    rx = self.serial.com_read_line()
                    try:
                        rec_data = str(rx, 'utf-8').strip().split(',')
                    except ValueError:
                        pass
            elif self.c_type == 'memricore':
                send_flag = True
                rec_data = ['raspberry']
                # todo: добавить служебную инфу в драйвер
        # режим симулятор
        elif self.cb_type == 'simulator':
            send_flag = True
            rec_data = ['simulator']            
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
            if self.c_type == 'memardboard_single' or self.c_type == 'memardboard_crossbar':    
                self.inc_req_id() # увеличиваем счечик id
                task["id"] = self.request_id # записываем id в тикет
                _ = self.push(gather(task))
                try:
                    res = self.pull()
                    if not res: # если нет результата
                        time.sleep(task["t_ms"]/1000) # ждем
                        res = self.pull() # снова пытаемся получить
                    if res[1] != self.request_id:
                        print(f'Не совпадение id: req:{res[1]}, ans:{self.request_id} (adc:{res[0]})')
                        raise ValueError
                    # else: print(f'{task["id"]}, {self.request_id}, {res[1]}, adc:{res[0]}')
                except (ValueError, IndexError):
                    self.logger.critical('ValueError, IndexError in board.py:pull!')
                    # res = tuple([0, self.request_id]) #todo: если не получили ответа нужно ли его занулять?
            elif self.c_type == 'memricore':
                adc = self.rasp_driver.mode_7(task['vol'],
                                          task['t_ms'],
                                          task['t_us'],
                                          task['sign'],
                                          task['id'],
                                          task['wl'],
                                          task['bl']) # vDAC, tms, tus, rev, id, wl, bl
                res = (int(adc[0]), int(adc[1]))
            # можно добавить работу с другими платами
        # режим симулятор
        elif self.cb_type == 'simulator':
            task_id = task["id"]
            vol = d2v(int(self.config['board']['dac_bit']),
                      float(self.config['board']['vol_ref_dac']),
                      task['vol'],
                      sign=task['sign'])
            duration = task['t_ms'] * 1000 + task['t_us']
            # если выбрали систему комманд для сигнальной платы
            #todo: возможно логику нужно переделать, пока не понятно
            if not 'wl' in task:
                wl = 0
            else:
                wl = task['wl']
            if not 'bl' in task:
                bl = 0
            else:
                bl = task['bl']
            res = (send_task_to_crossbar(self.crossbar_serial,
                                         self.crossbar_array,
                                         vol = vol,
                                         duration = duration,
                                         wl = wl,
                                         bl = bl,
                                         vol_read = float(self.config['board']['vol_read']),
                                         res_load = float(self.config['board']['res_load']),
                                         res_switches = float(self.config['board']['res_switches']),
                                         gain = float(self.config['board']['gain']),
                                         adc_bit = int(self.config['board']['adc_bit']),
                                         vol_ref_adc = float(self.config['board']['vol_ref_adc'])
                                         ), task_id)
            task = gather(task) # собираем из словаря строку
            if not self.silent:
                self.logger.info('Send %s', task.rstrip())
            time.sleep(1/1000)
            if not self.silent:
                self.logger.info('Recieved data: %s', str(res))
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

    def inc_req_id(self):
        """
        Инкремент id запроса
        """
        if self.request_id < 4096: #todo: вынести в настройки
            self.request_id += 1
        else:
            self.request_id = 0
