"""
Модуль взаимодействия с платой по COM порту
"""

# pylint: disable=no-name-in-module

import time
from typing import Union
from logging import Logger
from configparser import ConfigParser
from manager.blanks import gather
from manager.service.drivers import get_driver_attr
from manager.service import v2d, a2r, d2v, r2a

class Connector:
    """
    Взаимодействие с платой
    
    WARNING: Коннектор переделан под новый формат тасков и выходных данных (напряжения передаются в вольтах,
    сопротивления возвращаются в Омах). Чтобы не переделывать таски в написанных программах и нейросетях, можно работать 
    в старом формате: при инициализации нужно прописать аргумент `task_format='adc'`.
    На выходе из `impact` теперь такой формат: (Сопротивление (Ом), id, adc). Чтобы работать по-старому, можно брать третий
    элемент кортэжа (`adc`) -- это то, что `impact` возвращал раньше.
    """

    silent: bool
    logger: Logger
    cb_type: str
    board_type: str
    driver_attr: Union[dict, None]
    request_id: int = 0
    meta_info = {'task_time': 0.0}

    serial = None # COM порт
    rasp_driver = None # драйвер для распберри плат

    # для симулятора
    config: ConfigParser

    def __init__(
        self, 
        silent: bool, 
        logger: Logger, 
        cb_type: str, 
        board_type: str, 
        driver_attr: Union[dict, None] = None, 
        task_format: str = 'SI',
        **kwargs
    ):
        """Connector class used for communicating with the measurement board.

        Args:
            silent (bool): If True, some logging at info level is omitted.
            logger (logging.Logger): Logger for the connector.
            cb_type (str): `simulator` for simulating the memristive crossbar array, 
                `real` for connecting to real measurement boards.
            board_type (str): Board type (driver name) for real measurement boards. Available
                drivers are listed in `MemriBoard/manager/service/drivers.py`.
            driver_attr (dict | None, optional): Dict with driver attributes. If None, takes default attributes from 
                `MemriBoard/manager/service/drivers.py`. Defaults to None.
            task_format (str, optional): Format of the tasks sent to connector: 
                'dac': voltage (task['vol']) in DAC count, pulse width is set by 't_us' and 't_ms'.
                'SI': voltage (task['vol']) in Volts, pulse width is set by 'pulse_width' key (in seconds).
        """
        self.silent = silent
        self.logger = logger
        self.cb_type = cb_type
        self.board_type = board_type
        if driver_attr is None:
            self.driver_attr = get_driver_attr(board_type)
        else:
            self.driver_attr = driver_attr
        # для симулятора
        if 'config' in kwargs:
            self.config = kwargs['config']
        if 'crossbar_serial' in kwargs:
            self.crossbar_serial = kwargs['crossbar_serial']
        if task_format.lower() not in ['dac', 'si']:
            raise RuntimeError(f'Initiating Connector: unknown task_format: {task_format}')
        self.task_format = task_format.lower()

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
        simulation_fallback = False
        if self.cb_type == 'simulator':
            # загрузка симулятора
            from simulator.src import BoardSimulator
            self.interface = BoardSimulator()
            open_flag = self.interface.connect(self.crossbar_serial)
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
                        try:
                            self.meta_info['task_time'] = self.interface.meta_info['task_time']
                        except AttributeError:
                            self.meta_info['task_time'] = 0
                        open_flag = True
                else:
                    self.logger.info('Fail to open %s', self.portnum)
            # для плат на базе Elbear
            elif self.board_type == 'elbear_nano':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    from MemriCORE.elbear_nano.rpi_ELBEAR import RPI_modes_ELBEAR  # type: ignore
                    self.interface = RPI_modes_ELBEAR(kwargs['com_port'])
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'elbear_multimode_WR':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    from MemriCORE.elbear_multimode.elbear_controller import ElbearController  # type: ignore
                    self.interface = ElbearController(kwargs['com_port'], mode=1)
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError as ex:
                    print(ex)
            elif self.board_type == 'elbear_multimode_MVM':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    from MemriCORE.elbear_multimode.elbear_controller import ElbearController  # type: ignore
                    self.interface = ElbearController(kwargs['com_port'], mode=2)
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError:
                    pass
            # для плат на базе Raspberry Pi 5
            elif self.board_type == 'rp5_python':
                try:
                    from MemriCORE.rp5_python.rpi_modes import RPI_modes  # type: ignore
                    self.interface = RPI_modes()
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_c':
                try:
                    import MemriCORE.rp5_c.mvmdriver_wrapper as driver  # type: ignore
                    self.interface = driver.MVMDriver()
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_fpga_python':
                try:
                    from MemriCORE.rp5_fpga_python.rpi_FPGAed import RPI_modes_FPGAed  # type: ignore
                    self.interface = RPI_modes_FPGAed()
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_fpga_c':
                try:
                    from MemriCORE.rp5_fpga_c.fpga_wrapper import create_mode_controller  # type: ignore
                    self.interface = create_mode_controller()
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_rram_elbear_nano':
                try:
                    self.portnum = kwargs['com_port']
                    self.attempts = kwargs['attempts']
                    import RRAMPiDriver.ReRAMPiDrv as driver  # type: ignore
                    self.interface = driver.RPI_modes_RRAM(kwargs['com_port'])
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = self.interface.check_connection(kwargs['attempts'])
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'rp5_rram_python':
                try:
                    import RRAMPiDriver.ReRAMPiDrv_GPIO as driver  # type: ignore
                    self.interface = driver.RPI_modes_RRAM()
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = True
                except ModuleNotFoundError:
                    pass
            elif self.board_type == 'pico_client':
                try:
                    self.portnum = kwargs['com_port']
                    self.addr = kwargs['addr']
                    self.interface = kwargs['pico']
                    self.interface.init(self.addr, mode=1) # MODE_7 = 1, MODE_MVM = 2, MODE_CORE = 3
                    time.sleep(10)
                    try:
                        self.meta_info['task_time'] = self.interface.meta_info['task_time']
                    except AttributeError:
                        self.meta_info['task_time'] = 0
                    open_flag = True
                except ModuleNotFoundError:
                    print("ModuleNotFound: pico_client")
            # Для VISA-инструментов
            elif self.board_type == 'ITC_1T1R_32x8_switched':
                # Checking row and column number
                if kwargs['row_num'] != 32 or kwargs['col_num'] != 8:
                    print('ERROR! Wrong crossbar shape for ITC_1T1R_32x8_switched driver. Correct shape: 32 rows, 8 columns.')
                    open_flag = False
                else:  # Connecting
                    try:
                        from RRAM_VISA_Drivers import ITC_1T1R_32x8_switched  # type: ignore
                        self.interface = ITC_1T1R_32x8_switched(
                            B2902B_1_address=kwargs['visa_addresses'][0],
                            B2902B_2_address=kwargs['visa_addresses'][1],
                            Switch_address=kwargs['visa_addresses'][2],
                            VISA_library_path=kwargs['visa_library_path']
                        )
                        open_flag = True
                        if self.interface.sim:
                            simulation_fallback = True  # Что-то не так с адресами, драйвер упал в режим симуляции
                    except ModuleNotFoundError:
                        pass
                    except ConnectionError:
                        open_flag = False
            elif self.board_type == 'ITC_1T1R_32x8_probe_station':
                try:
                    from RRAM_VISA_Drivers import ITC_1T1R_32x8_probe_station  # type: ignore
                    self.interface = ITC_1T1R_32x8_probe_station(
                        B2902B_1_address=kwargs['visa_addresses'][0],
                        B2902B_2_address=kwargs['visa_addresses'][1],
                        VISA_library_path=kwargs['visa_library_path']
                    )
                    open_flag = True
                    if self.interface.sim:
                        simulation_fallback = True
                except ModuleNotFoundError:
                    pass
                except ConnectionError:
                    open_flag = False
            elif self.board_type == 'ITC_probe_station':
                try:
                    from RRAM_VISA_Drivers import ITC_probe_station  # type: ignore
                    self.interface = ITC_probe_station(
                        B2902B_address=kwargs['visa_addresses'][0],
                        VISA_library_path=kwargs['visa_library_path']
                    )
                    open_flag = True
                    if self.interface.sim:
                        simulation_fallback = True
                except ModuleNotFoundError:
                    pass
                except ConnectionError:
                    open_flag = False
        return open_flag, simulation_fallback

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
            if self.driver_attr['disconnect'] == 'com_close':
                self.interface.com_close()
                if self.interface.com_is_open():
                    self.logger.info('Fail to close')
                else:
                    self.logger.info('Closed')
                    close_flag = True
            # для плат на базе Raspberry Pi 5
            elif self.driver_attr['disconnect'] is None:
                # todo: может нужно что-то еще
                close_flag = True
            # Для VISA-инструментов
            elif self.board_type in ['ITC_1T1R_32x8_switched', 'ITC_1T1R_32x8_probe_station', 'ITC_probe_station']:
                flag, response = self.interface.disconnect()
                if flag:
                    self.logger.info('VISA-instruments disconnected')
                    close_flag = False
                else:
                    self.logger.critical(f'Failed to disconnect VISA-instruments: {response}')
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
            if self.driver_attr['get_tech_info'] == '100':
                send_flag = self.push('100\n')
                self.interface.com_whait_ready(float(self.config['connector']['timeout']))
                if self.interface.com_can_read_line():
                    rx = self.interface.com_read_line()
                    try:
                        rec_data = str(rx, 'utf-8').strip().split(',')
                    except ValueError:
                        pass
            elif self.driver_attr['get_tech_info'] == 'rpi':
                send_flag = True
                rec_data = ['raspberry pi 5']
            elif self.driver_attr['get_tech_info'] == 'elbear':
                send_flag = True
                rec_data = ['elbear_nano']
            elif self.driver_attr['get_tech_info'] == 'pico':
                send_flag = True
                rec_data = ['pico_client']
                # todo: добавить служебную инфу в драйвер
            elif self.board_type in ['ITC_1T1R_32x8_switched', 'ITC_1T1R_32x8_probe_station', 'ITC_probe_station']:
                send_flag = True
                rec_data = self.interface.get_tech_data()
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
            if self.driver_attr['impact'] == 'arduino':
                self.inc_req_id() # увеличиваем счетчик id
                task = self.task_volt_to_dac(task.copy(), retain_key_order=True)  # TODO remove if driver changed
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
                    res = (self.a2r(res[0]), res[1], int(res[0]))  # Resistance(Ohm), id, adc
                    # else: print(f'{task["id"]}, {self.request_id}, {res[1]}, adc:{res[0]}')
                except (ValueError, IndexError):
                    self.logger.critical('ValueError, IndexError in board.py:pull!')
                    # res = tuple([0, self.request_id]) #todo: если не получили ответа нужно ли его занулять?
            elif self.driver_attr['impact'] == 'elbear':
                status = False
                task = self.task_volt_to_dac(task.copy())  # TODO remove on driver change
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
                            res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))  # Resistance(Ohm), id, adc
                            status = True
                        elif task['mode_flag'] == 9: # режим команды 9
                            adc = self.interface.mode_9(task['vol'], 0, task['wl'], task['bl'])
                            res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))  # Resistance(Ohm), id, adc
                            status = True
                    except TimeoutError as ex:
                        print(ex)
                        try:
                            #print('!!!')
                            self.interface.com_close()
                            time.sleep(1)
                            from MemriCORE.elbear_nano.rpi_ELBEAR import RPI_modes_ELBEAR  # type: ignore
                            self.interface = RPI_modes_ELBEAR(self.portnum)
                            try:
                                self.meta_info['task_time'] = self.interface.meta_info['task_time']
                            except AttributeError:
                                self.meta_info['task_time'] = 0
                            _ = self.interface.check_connection(self.attempts)
                        except ModuleNotFoundError:
                            pass
                    if status: 
                        break
            elif self.driver_attr['impact'] == 'rpi':
                task = self.task_volt_to_dac(task.copy())  # TODO remove on driver change
                if task['mode_flag'] == 7: # режим команды 7
                    task['vol'] = abs(task['vol'])
                    adc = self.interface.mode_7(task['vol'],
                                            task['t_ms'],
                                            task['t_us'],
                                            task['sign'],
                                            task['id'],
                                            task['wl'],
                                            task['bl']) # vDAC, tms, tus, rev, id, wl, bl
                    res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))  # Resistance(Ohm), id, adc
                elif task['mode_flag'] == 9: # режим команды 9
                    adc = self.interface.mode_9(task['vol'], 0, task['wl'], task['bl'])
                    res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))  # Resistance(Ohm), id, adc
                elif task['mode_flag'] == 10: # режим команды 10
                    #print(task['vol'])
                    adc = self.interface.mode_mvm(task['vol'],
                                                    0,
                                                    0,
                                                    0,
                                                    0,
                                                    task['wl'],
                                                    task["id"])
                    res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))  # Resistance(Ohm), id, adc
            elif self.board_type in ['ITC_1T1R_32x8_switched', 'ITC_1T1R_32x8_probe_station', 'ITC_probe_station']:  # Работа с VISA-инструментами
                self.interface.logger.info(f'Task: {task}')
                if not isinstance(task['mode_flag'], str) and task['mode_flag'] not in [7]:
                    self.logger.critical('Wrong task for VISA-driver!')
                    res = 0
                elif task['mode_flag'] == 'panic':
                    # Что-то пошло не так, пытаемся всё выключить
                    self.logger.critical('VISA instruments: Panic!')
                    flag, response = self.interface.panic()
                    if flag:
                        self.logger.critical('Panic resolved')
                    else:
                        self.logger.critical(f'Panic was not resolved!: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 'interrupt':  
                    # Сброс SMU в конце тикета или при срабатывании терминатора
                    flag = self.interface.clear_instruments()  
                    if not flag:
                        self.logger.critical('Could not clear instruments!')
                    res = int(flag)
                elif task['mode_flag'] == 'sense':
                    if 'triggered' in task:
                        trig_flag = task['triggered']
                    else:
                        trig_flag = False
                    if 'skip_one' in task and task['skip_one']:  # Skip one value for endurance
                        self.interface.sense(trigger=trig_flag)
                    if 'vol' in task:
                        if 'read' in task and task['read']:
                            vol = float(self.config['board']['vol_read'])
                        else:
                            vol = -task['vol'] if task['sign'] else task['vol']
                    else:
                        vol = None
                    sense_data = self.interface.sense(trigger=trig_flag, vol=vol)  # (R, timestamp)
                    if isinstance(sense_data, str):
                        self.logger.critical(f'Sense error: {sense_data}')
                        res = 0 
                    else:
                        # Читаем данные в процессе эксперимента
                        adc = r2a(
                            gain = float(self.config['board']['gain']),
                            res_load = float(self.config['board']['res_load']),
                            vol_read = float(self.config['board']['vol_read']),
                            adc_bit = int(self.config['board']['adc_bit']),
                            vol_ref_adc = float(self.config['board']['vol_ref_adc']),
                            res_switches = float(self.config['board']['res_switches']),
                            res = sense_data[0]
                        )
                        if 'crossbar_scan' in task and task['crossbar_scan']:
                            res = (sense_data[0], task['id'], task['wl'], task['bl'])
                        else:    
                            res = (sense_data[0], task['id'], adc, *sense_data[1:])
                elif task['mode_flag'] == 'trigger':
                    flag, response = self.interface.trigger()
                    if flag:
                        self.logger.debug(response)
                    else:
                        self.logger.critical(f'Could not send trigger: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 'config_iv_dc':
                    # Отправка конфигурации на инструменты
                    flag, response = self.interface.config_iv_dc(
                        trigger_interval = task['pulse_width'], 
                        v_start = task['v_start'],
                        v_stop = task['v_stop'],
                        n_points = task['n_points'],
                        double = task['double'],
                        current_compliance = task['current_compliance'],
                        sign = task['sign']
                    )
                    if flag:
                        self.logger.info(response)
                    else:
                        # Останавливаем эксперимент
                        self.logger.critical(f'Could not configure instruments: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 'read':
                    flag, response = self.interface.config_std(
                        pulse_width = task['pulse_width'],
                        pulse_sequence = [self.config['board']['vol_read']],
                        read_flags = [True],
                        current_compliance = task['current_compliance'],
                        sign = task['sign']
                    )
                    if flag:
                        self.logger.info(response)
                    else:
                        # Останавливаем эксперимент
                        self.logger.critical(f'Could not configure instruments: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 'config_std':
                    pulse_sequence, read_flags = [], []
                    for pulse in task['pulse_sequence']:
                        if pulse == 'read':
                            pulse_sequence.append(self.config['board']['vol_read'])
                            read_flags.append(True)
                        else:
                            pulse_sequence.append(float(pulse))
                            read_flags.append(False)
                    self.interface.logger.debug(f'config_std: pulse_sequence:\n{pulse_sequence}')
                    flag, response = self.interface.config_std(
                        pulse_width = task['pulse_width'],
                        pulse_sequence = pulse_sequence,
                        read_flags = read_flags,
                        current_compliance = task['current_compliance'],
                        sign = task['sign']
                    )
                    if flag:
                        self.logger.info(response)
                    else:
                        # Останавливаем эксперимент
                        self.logger.critical(f'Could not configure instruments: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 'config_pulsed_retention':
                    # TODO: remove trig interval check (?)
                    if 'dir_interval' in task:
                        trigger_interval = task['dir_interval']
                    else:
                        trigger_interval = 5 * (task['pulse_width'])
                    flag, response = self.interface.config_pulsed_retention(
                        pulse_width = task['pulse_width'], 
                        current_compliance = task['current_compliance'],
                        n_pulses = task['n_pulses'],
                        read_voltage = self.config['board']['vol_read'],
                        sign = 1,  # Reset
                        trigger_interval = trigger_interval
                    )
                    if flag:
                        self.logger.info(response)
                    else:
                        # Останавливаем эксперимент
                        self.logger.critical(f'Could not configure instruments: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 'config_endurance':
                    # TODO remove interval check (?)
                    if 'trigger_interval' in task:
                        trigger_interval = task['trigger_interval']
                    else:
                        trigger_interval = 5 * (task['pulse_width'])
                    flag, response = self.interface.config_endurance(
                        v_dir = task['v_dir'],
                        v_rev = task['v_rev'],
                        read_voltage = self.config['board']['vol_read'],
                        pulse_width = task['pulse_width'], 
                        trigger_interval = trigger_interval,
                        n_cycles = task['n_cycles'],
                        dir_cc = task['dir_cc'],
                        rev_cc = task['rev_cc']
                    )
                    if flag:
                        self.logger.info(response)
                    else:
                        # Останавливаем эксперимент
                        self.logger.critical(f'Could not configure instruments: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 'config_pot_dep':
                    # TODO remove interval check (?)
                    if 'trigger_interval' in task:
                        trigger_interval = task['trigger_interval']
                    else:
                        trigger_interval = 5 * (task['pulse_width'])
                    flag, response = self.interface.config_pot_dep(
                        voltage = task['vol'],
                        pulse_width = task['pulse_width'], 
                        trigger_interval = trigger_interval,
                        n_pulses = task['n_pulses'],
                        compliance = task['compliance'],
                        sign = task['sign']
                    )
                    if flag:
                        self.logger.info(response)
                    else:
                        # Останавливаем эксперимент
                        self.logger.critical(f'Could not configure instruments: {response}')
                    res = int(flag)
                elif task['mode_flag'] == 7:
                    flag, response, sense_data = self.interface.mode_7(
                        pulse_width = task['pulse_width'], 
                        apply_voltage = task['vol'],
                        read_voltage = self.config['board']['vol_read'],
                        current_compliance = task['current_compliance'],
                        sign = task['sign']
                    )
                    if flag:
                        adc = r2a(
                            gain = float(self.config['board']['gain']),
                            res_load = float(self.config['board']['res_load']),
                            vol_read = float(self.config['board']['vol_read']),
                            adc_bit = int(self.config['board']['adc_bit']),
                            vol_ref_adc = float(self.config['board']['vol_ref_adc']),
                            res_switches = float(self.config['board']['res_switches']),
                            res = sense_data[0]
                        )
                        res = (sense_data[0], task['id'], int(adc))
                    else:
                        self.logger.critical(f'Mode_7 error: {response}')
                        res = 0
                elif task['mode_flag'] == 'connect_cell':
                    # Подлкючение ячейки кроссбара, нумерация wl и bl начинается с 0
                    flag, response = self.interface.connect_cell(wl=task['wl'], bl=task['bl'])
                    if flag:
                        self.logger.info(response)
                    else:
                        self.logger.critical('Could not connect the cell!')
                    res = int(flag)
                elif task['mode_flag'] == 'standby':
                    # Переход в режим ожидания эксперимента
                    flag, response = self.interface.standby()
                    if flag:
                        self.logger.info(response)
                    res = int(flag)
                elif task['mode_flag'] == 'need_stop':
                    # Посылаем флаг need_stop драйверу, если он завис
                    self.interface.stop_experiment()
                    self.logger.info('Need stop sent to driver')
                    res = 1
                self.interface.logger.info(f'Impact: res = {res}')
            # можно добавить работу с другими платами
            elif self.driver_attr['impact'] == 'pico':
                task = self.task_volt_to_dac(task.copy())  # TODO remove on driver change
                if task['mode_flag'] == 7:
                    # self.interface.init(self.addr, mode=1) # MODE_7 = 1, MODE_MVM = 2, MODE_CORE = 3
                    task['vol'] = abs(task['vol'])
                    adc = self.interface.mode_7(addr=self.addr,
                                                vDAC=200, 
                                                tms=task['t_ms'], 
                                                tus=task['t_us'], 
                                                rev=task['sign'], 
                                                wl=task['wl'], 
                                                bl=task['bl'])
                    res = (self.a2r(adc), 0, adc)  # Resistance(Ohm), id, adc
            # time.sleep(55/1000)
        # режим симулятор
        elif self.cb_type == 'simulator':
            # TODO: симулятор, наверное, тоже не должен взаимодействовать с переводами в отсчеты и обратно
            # Можно переделать симулятор так, чтобы он работал в СИ, и убрать строку с переводом (ниже).
            task = self.task_volt_to_dac(task.copy())
            if task['mode_flag'] == 7: # режим команды 7
                task['vol'] = abs(task['vol'])
                adc = self.interface.mode_7(task['vol'],
                                        task['t_ms'],
                                        task['t_us'],
                                        task['sign'],
                                        task['id'],
                                        task['wl'],
                                        task['bl']) # vDAC, tms, tus, rev, id, wl, bl
                res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))
            elif task['mode_flag'] == 9: # режим команды 9
                adc = self.interface.mode_9(task['vol'], 0, task['wl'], task['bl'])
                res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))
            elif task['mode_flag'] == 10: # режим команды 10
                #print(task['vol'])
                adc = self.interface.mode_mvm(task['vol'],
                                                0,
                                                0,
                                                0,
                                                0,
                                                task['wl'],
                                                task["id"])
                res = (self.a2r(adc[0]), int(adc[1]), int(adc[0]))
        if not self.silent:
            self.logger.info('Send %s', str(task['mode_flag']))
        if not self.silent:
            self.logger.info('Received data: %s', str(res))
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
            if self.driver_attr['custom_impact'] == 'arduino':
                _ = self.push(command)
                while attempts:
                    time.sleep(timeout)
                    try:
                        res = self.pull()
                        if len(res) == 2:
                            res = (self.a2r(res[0]), res[1], int(res[0]))  # Resistance(Ohm), id, adc
                            break
                    except ValueError:
                        self.logger.critical('ValueError in board.py:pull!')
                    attempts -= 1
                    if attempts == 0:
                        break
            elif self.driver_attr['custom_impact'] is None:
                # todo: пока не реализован
                time.sleep(timeout)
                res = (0, 0, 0)
            elif self.driver_attr['custom_impact'] == 'visa':
                res = self.interface.terminal_command(command)
        # режим симулятор
        elif self.cb_type == 'simulator':
            time.sleep(timeout)
            res = (0, 0, 0)
        # можно добавить работу с другими платами
        return res
    
    def connect_cell_to_external(self, mode: str, wl: int, bl: int):
        """
        Connect cell to the external terminals on the board
        """
        if self.cb_type == 'real':
            if self.driver_attr['connect_to_ext'] == 'arduino':
                if mode == 'connect':
                    self.push(f'3,{wl},{bl},333\n')
                    connected = False
                    for _ in range(10):
                        res = self.pull()
                        if res[0] == 333:
                            connected = True
                            break
                        time.sleep(0.01)
                    if not connected:
                        raise ConnectionError('Could not connect the cell!')
                else:
                    disconnected = False
                    self.push('4,444')
                    for _ in range(10):
                        res = self.pull()
                        if res[0] == 444:
                            disconnected = True
                            break
                        time.sleep(0.01)
                    if not disconnected:
                        raise ConnectionError('Could not disconnect the cell!')
            elif self.driver_attr['connect_to_ext'] == 'visa':
                if mode == 'connect':
                    flag, resp = self.interface.connect_cell(wl, bl)
                    if not flag:
                        raise Exception(str(resp))
                else:
                    flag, resp = self.interface.standby()
                    if not flag:
                        raise Exception(str(resp))

    def inc_req_id(self):
        """
        Инкремент id запроса
        """
        if self.request_id < 4096: #todo: вынести в настройки
            self.request_id += 1
        else:
            self.request_id = 0
            
    def v2d(self, vol: float) -> int:
        """Convert voltage to DAC counts (integer)"""
        return v2d(int(self.config['board']['dac_bit']), 
                   float(self.config['board']['vol_ref_dac']), 
                   abs(float(vol)))
        
    def a2r(self, adc: int) -> int:
        """Convert resistance from ADC voltage to Ohms (integer)"""
        return a2r(float(self.config['board']['gain']),
                   float(self.config['board']['res_load']),
                   float(self.config['board']['vol_read']),
                   int(self.config['board']['adc_bit']),
                   float(self.config['board']['vol_ref_adc']),
                   float(self.config['board']['res_switches']),
                   int(adc))
            
    def task_volt_to_dac(self, task: dict, retain_key_order: bool = False) -> dict:
        """
        Convert task from SI format (vol in Volts, pulse_width in seconds) to dac format (vol in dac bits, t_us, t_ms)
        If retain_key_order argument is True, retains key order of the returned task (for use with `gather` function).
        
        """
        if self.task_format == 'dac':  # The format is already right
            return task
        if hasattr(task['vol'], '__iter__'):  # If there is an array of voltages (mode_mvm)
            for i in range(len(task['vol'])):
                task['vol'][i] = self.v2d(task['vol'][i])
        else:
            task['vol'] = self.v2d(task['vol'])
        if 'pulse_width' in task:
            if task['pulse_width'] < 1e-3:  # Write in us
                task['t_us'] = int(task['pulse_width'] * 1e6)
                task['t_ms'] = 0
            else:  # Write in ms
                task['t_ms'] = int(task['pulse_width'] * 1e3)
                task['t_us'] = 0
            del task['pulse_width']
        if not retain_key_order:
            return task  # Not ordered! t_ms and t_us are at the end of the dict
        # Ordering task keys
        key_order = ['mode_flag', 'vol', 't_ms', 't_us', 'sign', 'id', 'wl', 'bl']
        ordered_task = {}
        for key in key_order:
            if key in task:
                ordered_task[key] = task[key]
        return ordered_task
    