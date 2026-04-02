"""
Модуль взаимодействия с платой по COM порту
"""

# pylint: disable=no-name-in-module

import time
from logging import Logger
from configparser import ConfigParser
from manager.blanks import gather
from manager.service import d2v
from simulator.src import (load_crossbar_array,
                           send_mode_7_to_crossbar,
                           send_mode_9_to_crossbar,
                           send_mode_mvm_to_crossbar)

class Connector():
    """
    Взаимодействие с платой
    """

    silent: int
    logger: Logger
    cb_type: str
    board_type: str
    request_id: int = 0

    serial = None # COM порт
    rasp_driver = None # драйвер для распберри плат

    # для симулятора
    config: ConfigParser
    crossbar_serial: str
    crossbar_array: list

    def __init__(self, silent, logger, cb_type, board_type, **kwargs):
        self.silent = silent
        self.logger = logger
        self.cb_type = cb_type
        self.board_type = board_type
        # для симулятора
        if 'config' in kwargs:
            self.config = kwargs['config']
        if 'crossbar_serial' in kwargs:
            self.crossbar_serial = kwargs['crossbar_serial']

    def _kick_board(self, attempts: int) -> bool:
        """
        Опрашиваем плату по COM-порту пока не ответит

        Arguments:
            attempts -- количество попыток

        Returns:
            not_rec_flag -- флаг успеха
        """
        rec_data = []
        count = 1
        not_rec_flag = False
        while not rec_data:
            self.logger.info('Try %d', count)
            if count > attempts:
                not_rec_flag = True
                break
            command = '7,0,0,0,0,0,0,0\n'
            _ = self.push(command)
            rec_data = self.pull()
            count += 1
        return not_rec_flag

    def open_port(self, **kwargs) -> bool:
        """
        Открытие соединения

        Returns:
            open_flag -- статус открытия
        """

        open_flag = False
        if self.cb_type == 'simulator':
            # загрузка симулятора
            open_flag, self.crossbar_array = load_crossbar_array(self.crossbar_serial)
        elif self.cb_type == 'real':
            # для плат на базе Arduino
            if self.board_type in ['memardboard_single', 'memardboard_crossbar']:
                from manager.comport import Serial # pylint: disable=C0415
                self.interface = Serial()
                # кол-во попыток получить данные
                self.portnum = kwargs['com_port']
                self.attempts = kwargs['attempts']
                timeout = kwargs['timeout']
                self.interface.com_open(self.portnum, timeout=timeout)
                if self.interface.com_is_open():
                    not_rec_flag = self._kick_board(self.attempts)
                    if not_rec_flag:
                        self.logger.info('Fail to receive %s', self.portnum)
                    else:
                        self.logger.info('Opened %s', self.portnum)
                        open_flag = True
                else:
                    self.logger.info('Fail to open %s', self.portnum)
            # для плат на базе Elbear
            elif self.board_type == 'elbear_nano':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    from MemriCORE.elbear_nano.rpi_ELBEAR import RPI_modes_ELBEAR
                    self.interface = RPI_modes_ELBEAR(kwargs['com_port'])
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'elbear_multimode_WR':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    from MemriCORE.elbear_multimode.elbear_controller import ElbearController
                    self.interface = ElbearController(kwargs['com_port'], mode=1)
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError as ex:
                    print(ex)
            elif self.board_type == 'elbear_multimode_MVM':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    from MemriCORE.elbear_multimode.elbear_controller import ElbearController
                    self.interface = ElbearController(kwargs['com_port'], mode=2)
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError:
                    pass
            # для плат на базе Raspberry Pi 5
            elif self.board_type == 'rp5_python':
                try:
                    from MemriCORE.rp5_python.rpi_modes import RPI_modes # pylint: disable=C0415
                    self.interface = RPI_modes()
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_c':
                try:
                    import MemriCORE.rp5_c.mvmdriver_wrapper as driver # pylint: disable=C0415,E0401
                    self.interface = driver.MVMDriver()
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_fpga_python':
                try:
                    from MemriCORE.rp5_fpga_python.rpi_FPGAed import RPI_modes_FPGAed # pylint: disable=C0415
                    self.interface = RPI_modes_FPGAed()
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_fpga_c':
                try:
                    from MemriCORE.rp5_fpga_c.fpga_wrapper import create_mode_controller # pylint: disable=C0415,E0401
                    self.interface = create_mode_controller()
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_rram_elbear_nano':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    import RRAMPiDriver.ReRAMPiDrv as driver
                    self.interface = driver.RPI_modes_RRAM(kwargs['com_port'])
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_rram_python':
                try:
                    import RRAMPiDriver.ReRAMPiDrv_GPIO as driver
                    self.interface = driver.RPI_modes_RRAM()
                    open_flag = True
                except ModuleNotFoundError:
                    pass
        return open_flag

    def close_port(self) -> bool:
        """
        Закрыть соединение

        Returns:
            close_flag -- статус закрытия
        """
        close_flag = False
        if self.cb_type == 'simulator':
            close_flag = True
        elif self.cb_type == 'real':
            # для плат на базе Arduino
            if self.board_type in ['memardboard_single', 'memardboard_crossbar', 'elbear_nano', 'rp5_rram_elbear_nano',  'elbear_multimode_WR', 'elbear_multimode_MVM']:
                self.interface.com_close()
                if self.interface.com_is_open():
                    self.logger.info('Fail to close')
                else:
                    self.logger.info('Closed')
                    close_flag = True
            # для плат на базе Raspberry Pi 5
            elif self.board_type in ['rp5_python', 'rp5_c', 'rp5_fpga_python', 'rp5_fpga_c', 'rp5_rram_python']:
                # todo: может нужно что-то еще
                close_flag = True
        return close_flag

    def push(self, send_data: str) -> bool:
        """
        Функция отправки данных по COM порту

        Arguments:
            data -- данные для отправки

        Returns:
            send_flag -- статус отправки
        """
        #start_time = time.time()
        send_flag = False
        if self.interface.com_is_open():
            if not self.silent:
                self.logger.info('Send %s', send_data.rstrip())
            check = self.interface.com_write(send_data.encode())
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
        self.interface.com_whait_ready(float(self.config['connector']['timeout']))
        if self.interface.com_can_read_line():
            rx = self.interface.com_read_line()
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
            if self.board_type in ['memardboard_single', 'memardboard_crossbar']:
                send_flag = self.push('100\n')
                self.interface.com_whait_ready(float(self.config['connector']['timeout']))
                if self.interface.com_can_read_line():
                    rx = self.interface.com_read_line()
                    try:
                        rec_data = str(rx, 'utf-8').strip().split(',')
                    except ValueError:
                        pass
            elif self.board_type in ['rp5_python', 'rp5_c', 'rp5_fpga_python', 'rp5_fpga_c', 'rp5_rram_python', 'rp5_rram_elbear_nano']:
                send_flag = True
                rec_data = ['raspberry pi 5']
            elif self.board_type in ['elbear_nano', 'elbear_multimode_WR', 'elbear_multimode_MVM']:
                send_flag = True
                rec_data = ['elbear_nano']
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
            if self.board_type in ['memardboard_single', 'memardboard_crossbar']:
                self.inc_req_id() # увеличиваем счечик id
                task["id"] = self.request_id # записываем id в тикет
                task['vol'] = abs(task['vol'])
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
            elif self.board_type in ['elbear_nano', 'elbear_multimode_WR', 'elbear_multimode_MVM']:
                status = False
                for _ in range(100):
                    try:
                        if task['mode_flag'] == 7: # режим команды 7
                            task['vol'] = abs(task['vol'])
                            adc = self.interface.mode_7(task['vol'],
                                                    task['t_ms'],
                                                    task['t_us'],
                                                    task['sign'],
                                                    task['id'],
                                                    task['wl'],
                                                    task['bl']) # vDAC, tms, tus, rev, id, wl, bl
                            res = (int(adc[0]), int(adc[1]))
                            status = True
                        elif task['mode_flag'] == 9: # режим команды 9
                            adc = self.interface.mode_9(task['vol'], 0, task['wl'], task['bl'])
                            res = (int(adc[0]), int(adc[1]))
                            status = True
                    except TimeoutError as ex:
                        print(ex)
                        try:
                            #print('!!!')
                            self.interface.com_close()
                            time.sleep(1)
                            from MemriCORE.elbear_nano.rpi_ELBEAR import RPI_modes_ELBEAR
                            self.interface = RPI_modes_ELBEAR(self.portnum)
                            _ = self.interface.check_connection(self.attempts)
                        except ModuleNotFoundError:
                            pass
                        pass
                    if status: break
            elif self.board_type in ['rp5_python', 'rp5_c', 'rp5_fpga_python', 'rp5_fpga_c', 'rp5_rram_python', 'rp5_rram_elbear_nano']:
                if task['mode_flag'] == 7: # режим команды 7
                    task['vol'] = abs(task['vol'])
                    adc = self.interface.mode_7(task['vol'],
                                            task['t_ms'],
                                            task['t_us'],
                                            task['sign'],
                                            task['id'],
                                            task['wl'],
                                            task['bl']) # vDAC, tms, tus, rev, id, wl, bl
                    res = (int(adc[0]), int(adc[1]))
                elif task['mode_flag'] == 9: # режим команды 9
                    adc = self.interface.mode_9(task['vol'], 0, task['wl'], task['bl'])
                    res = (int(adc[0]), int(adc[1]))
                elif task['mode_flag'] == 10: # режим команды 10
                    #print(task['vol'])
                    adc = self.interface.mode_mvm(task['vol'],
                                                    0,
                                                    0,
                                                    0,
                                                    0,
                                                    task['wl'],
                                                    task["id"])
                    res = (int(adc[0]), int(adc[1]))
            # можно добавить работу с другими платами
            # time.sleep(55/1000)
        # режим симулятор
        elif self.cb_type == 'simulator':
            task_id = task["id"]
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
            if task['mode_flag'] == 7: # режим команды 7
                vol = d2v(int(self.config['board']['dac_bit']),
                        float(self.config['board']['vol_ref_dac']),
                        task['vol'],
                        sign=task['sign'])
                duration = task['t_ms'] * 1000 + task['t_us']
                res = (send_mode_7_to_crossbar(self.crossbar_serial,
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
            elif task['mode_flag'] == 9: # режим команды 9
                vol = d2v(int(self.config['board']['dac_bit']),
                        float(self.config['board']['vol_ref_dac']),
                        task['vol'])
                if vol >= 0.3:
                    vol = 0.3
                res = (send_mode_9_to_crossbar(self.crossbar_array,
                                               vol = vol,
                                               wl = wl,
                                               bl = bl,
                                               res_load = float(self.config['board']['res_load']),
                                               res_switches = float(self.config['board']['res_switches']),
                                               gain = float(self.config['board']['gain']),
                                               adc_bit = int(self.config['board']['adc_bit']),
                                               vol_ref_adc = float(self.config['board']['vol_ref_adc'])
                                               ), task_id)
            elif task['mode_flag'] == 10: # режим команды 10
                vol = []
                for item in task['vol']:
                    vol.append(d2v(int(self.config['board']['dac_bit']),
                               float(self.config['board']['vol_ref_dac']),
                               item))
                res = (send_mode_mvm_to_crossbar(self.crossbar_array,
                                                vol = vol,
                                                wl = wl,
                                                gain = float(self.config['board']['gain']),
                                                sum_gain = float(self.config['board']['sum_gain']),
                                                adc_bit = int(self.config['board']['adc_bit']),
                                                vol_ref_adc = float(self.config['board']['vol_ref_adc'])
                                                ), task_id)
            if not self.silent:
                self.logger.info('Send %s', str(task['mode_flag']))
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
            if self.board_type in ['memardboard_single', 'memardboard_crossbar']:
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
            elif self.board_type in ['rp5_python', 'rp5_c', 'rp5_fpga_python', 'rp5_fpga_c', 'rp5_rram_python', 'rp5_rram_elbear_nano', 'elbear_multimode_WR', 'elbear_multimode_MVM']:
                # todo: пока не реализован
                time.sleep(timeout)
                res = (0, 0)
        # режим симулятор
        elif self.cb_type == 'simulator':
            time.sleep(timeout)
            res = (0, 0)
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
