"""
Менеджер взаимодействия с платой
"""

# pylint: disable=W0401,W0614,R0902,R1732

import os
import time
from threading import Thread, Lock
from queue import Queue
from queue import Full
from queue import Empty
from manager.app import Application
from manager.board import Connector
from manager.service.saves import save_list_to_bytearray
from manager.service import a2r
from manager.model.src import create_empty_db_crossbar
from manager.service.global_settings import *
from manager.model.db import DBOperate
from simulator.src import create_crossbar_array

class Manager(Application):
    """
    Менеджер взаимодействия с платой

    Arguments:
        tickets -- очередь тикетов
        tasks -- очередь задач
        results -- очередь результатов
        lock -- блокировщик потоков
        save_flag -- флаг сохранения результатов
        connected_flag -- флаг подключения к порту
        crossbar_id -- id подключенного кроссбара
        conn -- конектор к плате
        _admin_thread -- поток администратора
        _worker_thread -- поток рабочего
        _save_thread -- поток сохранения результата
        _need_stop -- флаг остановки воркера
        _need_clear -- почистить очередь        
        _accepted_tickets -- принято тикетов с момента остановки
        _total_accepted_tickets -- всего принятых тикетов
        _done_tickets -- выполнено тикетов с момента остановки
        _total_done_tickets -- всего выполнено тикетов
        _recorded_results -- сколько результатов записано
        _saver_read_results -- сейвер прочитал результатов
        _admin_work_state -- работает ли админ
        _worker_work_state -- работает ли воркер
        _need_save -- запущен сейвер
    """

    tickets: Queue
    tasks: Queue
    results: Queue
    lock: Lock
    save_flag: bool = False
    connected_flag: bool = False
    crossbar_id: int
    cb_type: str
    c_type: str
    conn: Connector
    _admin_thread: Thread
    _worker_thread: Thread
    _save_thread: Thread
    _need_stop: bool = False
    _need_clear: bool = False
    _accepted_tickets: int = 0
    _total_accepted_tickets: int = 0
    _done_tickets: int = 0
    _total_done_tickets: int = 0
    _recorded_results: int = 0
    _saver_read_results: int = 0
    _admin_work_state: bool = False
    _worker_work_state: bool = False
    _need_save: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock() # мьютекс
        self.tickets = Queue() # тикеты
        self.tasks = Queue() # задачи
        # результаты
        self.results = Queue(maxsize=int(self.ap_config['queues']['resmax']))

    def use_chip(self, serial: str):
        """
        Использовать чип
        """
        status, chip_data = self.db.get_chip_data(serial)
        if status:
            self.crossbar_id = chip_data[0]
            self.row_num = chip_data[1]
            self.col_num = chip_data[2]
            self.cb_type = chip_data[3]
            self.c_type = chip_data[4]
        return status, chip_data

    def add_chip(self,
                 serial: str,
                 comment: str = "",
                 row_num: int = 32,
                 col_num: int = 8,
                 cb_type: str = 'simulator',
                 c_type: str = 'simulator') -> bool:
        """
        Добавление чипа в базу
        """
        status_add = False
        status, chip_data = self.db.get_chip_data(serial) # проверка наличия в базе
        if status:
            self.ap_logger.critical('crossbar #%d with serial %s already in db', chip_data[0], serial)
        else:
            status, crossbar_id = create_empty_db_crossbar(DB_PATH,
                                                           serial,
                                                           comment,
                                                           row_num,
                                                           col_num,
                                                           cb_type,
                                                           c_type)
            if status:
                self.ap_logger.info('crossbar #%d with serial %s added', crossbar_id, serial)
                status_add = status
                if cb_type == 'simulator': # создаем модель кроссбара
                    create_crossbar_array(serial, row_num, col_num)
        return status_add

    def get_recorded_results(self) -> bool:
        """
        Получить значение счетчика записанных результатов
        Для каждого тикета результатов будет равно:
        кол-во тасков + 2 (метка начала и конца)
        """
        self.lock.acquire()
        res = self._recorded_results
        self.lock.release()
        return res

    def connect(self, port) -> bool:
        """
        Подключение к плате
        """
        self.conn = Connector(int(self.ap_config['connector']['silent']),
                               self.ap_logger,
                               self.ap_config,
                               self.blank_type,
                               self.cb_type)
        self.connected_flag = self.conn.open_serial(port) # подключаемся к плате
        return self.connected_flag

    def try_connect(self) -> None:
        """
        Попытка открыть COM порт
        """
        if not self.connected_flag:
            self.connected_flag = self.conn.open_serial(self._port) # подключаемся к плате

    def _admin(self) -> None:
        """
        Администратор очередей
        """
        db = DBOperate()
        ticket_count = 0 # счетчик принятых тикетов
        # цикл работает пока не поднят флаг _need_stop
        while not self._need_stop:
            self.lock.acquire()
            # пришла команда остановить очередь
            if self._need_clear: # админ не работает
                self._admin_work_state = False
                self.lock.release()
                continue
            # админ продолжил работу
            self._admin_work_state = True
            try: # ждем тикет
                ticket = self.tickets.get_nowait()
            except Empty: # пока пустой
                self.lock.release()
                continue
            # пришел тикет
            self.tickets.task_done() # тикет взят в обработку
            # принятых текущих тикетов +1
            self._accepted_tickets += 1
            self._total_accepted_tickets += 1
            # сохраняем в БД
            status, exp_id, mem_id = db.add_not_completed_ticket(ticket, self.crossbar_id)
            assert status # ошибка БД не возможно добавить тикет
            # добавляем в очередь генератор задач
            ticket_count += 1
            self.ap_logger.info('%s accepted for processing #%d', ticket['mode'],
                             ticket_count)
            # был тикет, а для воркера станет таск генератором
            self.tasks.put([self.menu[ticket['mode']],
                            (ticket['params'].copy(), ticket['terminate'].copy(), self.blank_type),
                            (exp_id,
                             mem_id)])
            self.lock.release()
        self.ap_logger.info('admin finished. %d tickets accepted', ticket_count)

    def _worker(self) -> None:
        """
        Работник с платой
        """
        db = DBOperate()
        total_task_count = 0 # счетчик задач всего сделано
        ticket_count = 0 # счетчик всего принято тикетов
        # цикл работает пока не поднят флаг _need_stop
        while not self._need_stop:
            self.lock.acquire()
            # пришла команда остановить очередь
            if self._need_clear: #  воркер не работает
                self._worker_work_state = False
                self.lock.release()
                continue
            # воркер продолжил работу
            self._worker_work_state = True
            try: # ждем генератор задач
                tasks_gen = self.tasks.get_nowait()
            except Empty:
                self.lock.release()
                continue
            # генератор принят
            self.tasks.task_done()
            ticket_count += 1
            ticket_id = str(tasks_gen[1][0]['id']) # ['params']['id']
            self.ap_logger.info('worker got ticket id-%s!', ticket_id)
            # извлекаем информацию
            exp_id = tasks_gen[2][0]
            mem_id = tasks_gen[2][1]
            # cохранение не реализовано внутри цикла
            # новое имя файла для тикета
            # self._result_file_name = 'name'
            # сохраняем метаданные эксперимента
            # pass сохранение в цикле генератора замедлит скорость
            # задачи взаимодействия с платой берем из генератора
            tasks_in_ticket_done = 0 # счетчик задач из тикета сделано
            # кладем метку начала тикета
            try:
                self.results.put(f'начало_{exp_id}', block=False)
            except Full: # очередь результатов переполнена
                # удалять или сгружать на диск?
                self._clear(self.results)
                self.ap_logger.critical('Results queue cleared!')
                self.results.put(f'начало_{exp_id}', block=False)
            # учитываем результат
            self._recorded_results += 1 # выполнил тикет
            # этот цикл можем переделать в отедльный процесс
            # и создавать процесс для каждого тикета
            result = 0 # если в тикете нет задач то result = 0
            self.lock.release()
            start_time = time.time() # фиксируем начало работы
            for task in tasks_gen[0](*tasks_gen[1]):
                self.lock.acquire()
                # ВАЖНО: всё что в теле цикла влияет на быстродействие
                # посылаем задачу в плату
                result = self.conn.impact(task[0])
                # добавляем результат в журнал эксперимента
                try:
                    self.results.put((task[0], result[0]), block=False)
                except Full: # очередь результатов переполнена, смываем
                    self._clear(self.results)
                    self.ap_logger.critical('Results queue cleared!')
                    self.results.put((task[0], result[0]), block=False)
                # учитываем результат
                self._recorded_results += 1 # выполнил тикет
                # учитываем выполненную задачу
                tasks_in_ticket_done += 1
                # проверка прерывания тикета
                interrupt = task[1](result)
                if interrupt or self._need_clear or self._need_stop:
                    self.ap_logger.warning('%d terminate ticket id-%s, \
                                           %d tasks done (code: %d%d%d)!',
                                        result[0],
                                        ticket_id,
                                        tasks_in_ticket_done,
                                        int(interrupt),
                                        int(self._need_clear),
                                        int(self._need_stop))
                    self.lock.release()
                    break # прерываем выполнение тикета
                self.lock.release()
            self.lock.acquire()
            stop_time = time.time() # фиксируем конец работы
            total_task_count += tasks_in_ticket_done # всего сделали
            self._done_tickets += 1 # выполнил тикет
            self._total_done_tickets += 1 # всего выполнено тикетов
            # кладем метку конца тикета
            try:
                self.results.put('конец', block=False)
            except Full: # очередь результатов переполнена, смываем
                self._clear(self.results)
                self.ap_logger.critical('Results queue cleared!')
                self.results.put('конец', block=False)
            # учитываем результат
            self._recorded_results += 1 # выполнил тикет
            # журналируем
            self.ap_logger.info('ticket id-%s done with %d tasks in %.2f sec',
                             ticket_id,
                             tasks_in_ticket_done,
                             round(stop_time-start_time,2))
            self.ap_logger.info('%d - accepted %d - done',
                             self._accepted_tickets,
                             self._done_tickets)
            # сохраняем в БД
            if result:
                last_resistance = int(a2r(self.gain,
                                          self.res_load,
                                          self.vol_read,
                                          self.adc_bit,
                                          self.vol_ref_adc,
                                          self.res_switches,
                                          result[0]))
                status_update_complited_ticket = db.update_complited_ticket(exp_id, mem_id, last_resistance)
                if not status_update_complited_ticket:
                    self.ap_logger.critical("db exp_id:%d mem_id:%d result:%s", exp_id, mem_id, str(result))
            else:
                self.ap_logger.critical("exp_id:%d mem_id:%d result:%s", exp_id, mem_id, str(result))
            self.lock.release()
        self.ap_logger.info('worker finished. %d tasks done in %d tickets',
                         total_task_count,
                         ticket_count)

    def _clear(self, queue_for_clear: Queue) -> None:
        """
        Очистка очереди

        Arguments:
            queue_for_clear -- очередь для очистки
        """
        with queue_for_clear.mutex:
            queue_for_clear.queue.clear()
            queue_for_clear.unfinished_tasks = 0
            queue_for_clear.not_full.notify()
            queue_for_clear.all_tasks_done.notifyAll()

    def _save_results(self, transit_queue: Queue = None, transit=False) -> None:
        """
        Поток сохранения результата
        Результат - начало (н), данные (д), конец (к)
        Флаг сохранения - True (t), False (f)
        Флаг открытости файла - True (о), False (з)
        1) дtо - записать в файл
        2) нз - создать имя файла
        3) дtз - открыть файл и записать
        4) ко - закрыть файл
        5) но - Exception
        6) всё остальное pass
        """
        db = DBOperate()
        files_created = 0 # счетчик файлов
        file_opened = False # флаг открытия файла
        file = None
        saved_results = 0
        try:
            while not self._need_stop:
                self.lock.acquire()
                try: # ждем результат
                    result = self.results.get_nowait()
                except Empty:
                    self.lock.release()
                    continue
                # результат считан
                self.results.task_done()
                self._saver_read_results += 1
                # 1 записать в файл
                if isinstance(result, tuple) and self.save_flag and file_opened:
                    save_list_to_bytearray(file, result[0]['vol'], result[1])
                    saved_results += 1
                # 2 создать имя файла
                elif isinstance(result, str) and 'начало' in result.split('_') and not file_opened:
                    fname = time.strftime("%Y%m%d-%H%M%S")
                    file_path = os.path.join(os.getcwd(),'results', fname)
                    # сохраняем в БД
                    exp_id = int(result.split('_')[1])
                    _ = db.update_ticket_result_path(exp_id, fname) 
                # 3 открыть файл и записать
                elif isinstance(result, tuple) and self.save_flag and not file_opened:
                    file = open(file_path, 'wb')
                    file_opened = True
                    files_created += 1
                    self.ap_logger.info('file %s created!', fname)
                    save_list_to_bytearray(file, result[0]['vol'], result[1])
                    saved_results += 1
                # 4 закрыть файл
                elif result == 'конец' and file_opened:
                    file.close() # закрываем файл
                    file_opened = False # флаг открытия файла
                    self.ap_logger.info('file %s closed!', fname)
                    # todo: добавить удаление файла и запись его в БД
                # 5 Exception
                elif isinstance(result, str) and 'начало' in result.split('_') and file_opened:
                    raise ValueError
                # перекладываем в транзитную очередь
                if transit:
                    try:
                        transit_queue.put(result, block=False)
                    except Full: # транзитная очередь переполнена
                        # очищаем
                        self._clear(transit_queue)
                        self.ap_logger.critical('Transit queue cleared!')
                        self.results.put(result, block=False)
                self.lock.release()
        except ValueError:
            self.ap_logger.critical('Saver broken!!!')
            self.lock.release()
        # прекращение работы, закрываем файл
        if file_opened:
            file.close() # закрываем файл
            file_opened = False # флаг открытия файла
            self.ap_logger.info('file %s closed!', fname)
        # журналируем
        self.ap_logger.info('save thread finished. %d results read. %d files created.',
                        saved_results,
                        files_created)

    def start(self) -> None:
        """
        Запуск потоков
        """
        self._admin_thread = Thread(target=self._admin)
        self._admin_thread.start() # администратор очередей
        self._worker_thread = Thread(target=self._worker, daemon=True)
        self._worker_thread.start() # обработчик

    def start_saver(self, transit_queue: Queue = None, transit=False) -> None:
        """
        Сохранять результат
        """
        self._need_save = True
        self._save_thread = Thread(target=self._save_results, args=(transit_queue, transit,))
        self._save_thread.start() # сохранение результата

    def set_save_flag(self, flag: bool) -> None:
        """
        Установить флаг сохранения
        """
        self.lock.acquire()
        self.save_flag = flag
        self.lock.release()
        self.ap_logger.info('set save flag %r', flag)

    def send_ticket(self, ticket: dict) -> None:
        """
        Послать тикет. В тикете значения напряжений и параметры
        терминатора должны быть указаны в dac и adc.

        Arguments:
            ticket -- тикет
        """
        self.tickets.put(ticket.copy())
        self.tickets.join()

    def wait(self) -> None:
        """
        Ждем гарантированного завершения
        """
        time.sleep(0.1)
        while self._accepted_tickets != self._done_tickets:
            continue
        if self._need_save:
            while self._recorded_results != self._saver_read_results:
                time.sleep(0.01)
                continue

    def abort(self) -> None:
        """
        Прервать выполнение очереди задач
        """
        self.ap_logger.warning('Need break!')
        # поднимаем флаг
        self.lock.acquire()
        self._need_clear = True
        self.lock.release()
        # убеждаемся что воркер и админ перешли в ожидание
        while self._admin_work_state or self._worker_work_state:
            continue
        self.ap_logger.warning('Admin and worker break!')
        # очищаем очереди
        self._clear(self.tickets)
        self._clear(self.tasks)
        # убеждаемся что всё очищено
        self.tickets.join()
        self.tasks.join()
        # подчищаем счетчики
        self.lock.acquire()
        self._accepted_tickets = 0
        self._done_tickets = 0
        self.lock.release()
        # опускаем флаги
        self.lock.acquire()
        self._need_clear = False
        self.lock.release()
        # делаем запись
        self.ap_logger.warning('All tasks canceled!')

    def get_term_values(self, terminate: dict) -> int:
        """
        Извлечь значения терминатора
        """
        term_type = terminate['type']
        term_value = terminate['value'] # adc
        if term_type == 'pass':
            term_left = 0
            term_right = 0
        else:
            if isinstance(term_value, int):
                term_left = term_value
                term_right = 0
            elif isinstance(term_value, list):
                term_left = term_value[0]
                term_right = term_value[1]
        return term_left, term_right # adc

    def close(self) -> None:
        """
        Закрыть менеджер
        """
        # поднимаем флаг
        self._need_stop = True
        # очищаем очереди
        self._clear(self.tickets)
        self._clear(self.tasks)
        self._clear(self.results)
        # убеждаемся что всё очищено
        self.tickets.join()
        self.tasks.join()
        self.results.join()
        # закрываем COM порт
        if self.connected_flag:
            self.conn.close_serial()
        # проверяем потоки
        try:
            while self._admin_thread.is_alive():
                continue
            while self._worker_thread.is_alive():
                continue
        except AttributeError:
            pass
        if self._need_save:
            while self._save_thread.is_alive():
                continue
        # делаем запись
        self.ap_logger.info('Manager closed!')
