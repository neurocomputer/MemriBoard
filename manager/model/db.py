"""
База данных
"""

import pickle
import datetime
import sqlite3
from manager.service.global_settings import *

# todo: добавить логгер базы
TIMEOUT = 5
class DBOperate():

    def db_connect(self):
        """
        Подключиться к БД
        """
        try:
            self.db_connection = sqlite3.connect(DB_PATH) # выполняется подключение к базе данных
            self.db_cursor = self.db_connection.cursor() # позволяет выполнять SQLite-запросы
            status = True
            # self.logger.info("Соединение с базой открыто")
        except sqlite3.Error:
            status = False
            # self.logger.critical("Ошибка при подключении к базе данных!")
        return status

    def db_disconnect(self):
        """
        Отключение от БД
        """
        if self.db_connection:
            self.db_connection.close() # закрываем соединение
            status = True
            # self.logger.info("Соединение с базой закрыто")
        else:
            status = False
            # self.logger.critical("Соединение с базой не было открыто!")
        return status

    def get_memristor_id(self, wl, bl, crossbar_id):
        """
        Получить id мемристора
        """
        self.db_connect()
        memristor_id = 0
        status = False
        if self.db_connection:
            try:
                QUERY = f"""SELECT id FROM Memristors
                    WHERE wl={wl} AND bl={bl} AND crossbar_id={crossbar_id}"""
                self.db_cursor.execute(QUERY)
                memristor_id = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error:
                pass
        self.db_disconnect()
        return status, memristor_id

    def add_experiment(self, name, memristor_id):
        """
        Добавить эксперимент
        """
        self.db_connect()
        status = False
        experiment_id = 0
        if self.db_connection:
            try:
                QUERY = """INSERT INTO Experiments
                (datestamp, name, status, memristor_id)
                VALUES (?,?,?,?);"""
                datestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                self.db_cursor.execute(QUERY, (datestamp,
                                               name,
                                               0,
                                               memristor_id))
                self.db_connection.commit() # сохранить изменение
                experiment_id = self.db_cursor.lastrowid
                status = True
            except sqlite3.Error:
                pass
        self.db_disconnect()
        return status, experiment_id

    def update_experiment_status(self, experiment_id, experiment_status):
        """
        Обновить статус эксперимента
        """
        self.db_connect()
        status = False
        if self.db_connection:
            try:
                QUERY = f"""UPDATE Experiments
                SET status=(?)
                WHERE id={experiment_id}"""
                self.db_cursor.execute(QUERY, (experiment_status,))
                self.db_connection.commit() # сохранить изменение
                status = True
            except sqlite3.Error:
                pass
        self.db_disconnect()
        return status

    def add_ticket(self, ticket, experiment_id):
        """
        Добавляем пустой тикет при примке в работу админом
        memristor_id <- wl, bl, crossbar_id
        """
        self.db_connect()
        ticket_id = 0
        status = False
        if self.db_connection:
            try:
                QUERY = """INSERT INTO Tickets
                (datestamp, ticket_name, ticket, status, experiment_id)
                VALUES (?,?,?,?,?);"""
                datestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                ticket_name = ticket['name']
                ticket = pickle.dumps(ticket)
                status = False
                self.db_cursor.execute(QUERY, (datestamp,
                                               ticket_name,
                                               ticket,
                                               status,
                                               experiment_id))
                self.db_connection.commit() # сохранить изменение
                ticket_id = self.db_cursor.lastrowid
                status = True
            except sqlite3.Error:
                pass
        self.db_disconnect()
        return status, ticket_id

    def update_ticket(self, ticket_id, name, value):
        """
        Обновить тикет
        """
        self.db_connect()
        status = False
        if self.db_connection:
            try:
                QUERY = f"""UPDATE Tickets
                SET {name}=(?)
                WHERE id={ticket_id}"""
                self.db_cursor.execute(QUERY, (value,))
                self.db_connection.commit() # сохранить изменение
                status = True
            except sqlite3.Error as er:
                print('update_ticket',er)
        self.db_disconnect()
        return status

    def update_experiment(self, experiment_id, name, value):
        """
        Обновить тикет
        """
        self.db_connect()
        status = False
        if self.db_connection:
            try:
                QUERY = f"""UPDATE Experiments
                SET {name}=(?)
                WHERE id={experiment_id}"""
                self.db_cursor.execute(QUERY, (value,))
                self.db_connection.commit() # сохранить изменение
                status = True
            except sqlite3.Error as er:
                print('update_experiment',er)
        self.db_disconnect()
        return status

    def update_last_resistance(self, memristor_id, last_resistance):
        """
        Обновить значение сопротивления
        """
        self.db_connect()
        status = False
        if self.db_connection:
            try:
                QUERY = f"""UPDATE Memristors
                SET last_resistance={last_resistance}
                WHERE id={memristor_id}
                """
                self.db_cursor.execute(QUERY)
                self.db_connection.commit() # сохранить изменение
                status = True
            except sqlite3.Error as er:
                print('update_last_resistance',er)
        self.db_disconnect()
        return status

    def get_chip_data(self, serial):
        """
        Получить id кроссбара по серийному номеру
        """
        self.db_connect()
        status = False
        chip_data = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT id, bl, wl, cb_type, c_type FROM Crossbars
                WHERE serial='{serial}'"""
                self.db_cursor.execute(QUERY)
                chip_data = self.db_cursor.fetchall()[0]
                status = True
            except sqlite3.Error as er:
                print('get_chip_data',er)
            except TypeError as er:
                print('get_chip_data',er)
            except IndexError as er:
                print('get_chip_data',er)
        self.db_disconnect()
        return status, chip_data

    def get_cb_list(self):
        """
        Список кроссбаров
        """
        self.db_connect()
        status = False
        cb_list = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT serial FROM Crossbars"""
                self.db_cursor.execute(QUERY)
                for item in self.db_cursor.fetchall():
                    cb_list.append(item[0])
                status = True
            except sqlite3.Error as er:
                print('get_cb_list',er)
            except TypeError as er:
                print('get_cb_list',er)
        self.db_disconnect()
        return status, cb_list

    def get_cb_list_cb_type(self, cb_type):
        """
        Список кроссбаров по типу
        """
        self.db_connect()
        status = False
        cb_list = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT serial FROM Crossbars WHERE cb_type='{cb_type}'"""
                self.db_cursor.execute(QUERY)
                for item in self.db_cursor.fetchall():
                    cb_list.append(item[0])
                status = True
            except sqlite3.Error as er:
                print('get_cb_list_cb_type',er)
            except TypeError as er:
                print('get_cb_list_cb_type',er)
        self.db_disconnect()
        return status, cb_list

    def get_exp_name(self, experiment_id):
        """
        Имя эксперимента
        """
        self.db_connect()
        status = False
        exp_name = ''
        if self.db_connection:
            try:
                QUERY = f"""SELECT name FROM Experiments
                WHERE id={experiment_id}"""
                self.db_cursor.execute(QUERY)
                exp_name = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_exp_name',er)
            except TypeError as er:
                print('get_exp_name',er)
        self.db_disconnect()
        return status, exp_name
    
    def get_experiment_tickets(self, experiment_id):
        """
        Тикеты эксперимента
        """
        self.db_connect()
        status = False
        history = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT id, datestamp, ticket_name, status FROM Tickets
                WHERE experiment_id={experiment_id}"""
                self.db_cursor.execute(QUERY)
                history = self.db_cursor.fetchall()
                status = True
            except sqlite3.Error as er:
                print('get_experiment_tickets',er)
            except TypeError as er:
                print('get_experiment_tickets',er)
        self.db_disconnect()
        return status, history

    def get_memristor_experiments(self, memristor_id):
        """
        История всех экспериментов с мемристором
        """
        self.db_connect()
        status = False
        history = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT id, datestamp, name, status FROM Experiments
                WHERE memristor_id={memristor_id} ORDER BY id DESC"""
                self.db_cursor.execute(QUERY)
                history = self.db_cursor.fetchall()
                status = True
            except sqlite3.Error as er:
                print('get_memristor_experiments',er)
            except TypeError as er:
                print('get_memristor_experiments',er)
        self.db_disconnect()
        return status, history

    def get_experiments(self, crossbar_id):
        """
        История всех экспериментов с кроссбаром
        Можно переделать для всех экспериментов в базе
        """
        self.db_connect()
        status = False
        history = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT e.id, e.datestamp, e.name, e.status FROM Crossbars AS c JOIN Memristors AS m ON m.crossbar_id=c.id JOIN Experiments AS e ON e.memristor_id=m.id WHERE m.crossbar_id={crossbar_id} ORDER BY e.datestamp DESC"""
                self.db_cursor.execute(QUERY)
                history = self.db_cursor.fetchall()
                status = True
            except sqlite3.Error as er:
                print('get_experiments',er)
            except TypeError as er:
                print('get_experiments',er)
        self.db_disconnect()
        return status, history

    def get_last_resistance(self, memristor_id):
        """
        Последнее сопротивление
        """
        self.db_connect()
        status = False
        resistance = 0
        if self.db_connection:
            try:
                QUERY = f"""SELECT last_resistance FROM Memristors
                WHERE id={memristor_id}"""
                self.db_cursor.execute(QUERY)
                resistance = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_last_resistance',er)
            except TypeError as er:
                print('get_last_resistance',er)
        self.db_disconnect()
        return status, resistance

    def get_all_resistances(self, crossbar_id):
        """
        Последнее сопротивление
        """
        self.db_connect()
        status = False
        resistances = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT bl, wl, last_resistance from Memristors
                WHERE crossbar_id={crossbar_id};"""
                self.db_cursor.execute(QUERY)
                resistances = self.db_cursor.fetchall()
                status = True
            except sqlite3.Error as er:
                print('get_all_resistances',er)
            except TypeError as er:
                print('get_all_resistances',er)
        self.db_disconnect()
        return status, resistances

    def get_img_experiment(self, experiment_id):
        """
        Получить рисунок эксперимента из базы
        """
        self.db_connect()
        status = False
        img = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT image from Experiments
                WHERE id={experiment_id};"""
                self.db_cursor.execute(QUERY)
                img = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_img_experiment',er)
            except TypeError as er:
                print('get_img_experiment',er)
        self.db_disconnect()
        return status, img

    def get_tickets(self, experiment_id):
        """
        Получить тикеты одного эксперимента
        """
        self.db_connect()
        status = False
        tickets = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT ticket FROM Tickets
                WHERE experiment_id={experiment_id}"""
                self.db_cursor.execute(QUERY)
                tickets = self.db_cursor.fetchall()
                status = True
            except sqlite3.Error as er:
                print('get_tickets',er)
            except TypeError as er:
                print('get_tickets',er)
        self.db_disconnect()
        return status, tickets
    
    def get_ticket_from_id(self, ticket_id):
        """
        Получить тикет по id
        """
        self.db_connect()
        status = False
        ticket = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT result FROM Tickets
                WHERE id={ticket_id}"""
                self.db_cursor.execute(QUERY)
                ticket = self.db_cursor.fetchall()
                status = True
            except sqlite3.Error as er:
                print('get_ticket_from_id',er)
            except TypeError as er:
                print('get_ticket_from_id',er)
        self.db_disconnect()
        return status, ticket
    
    def get_crossbar_serial_from_id(self, crossbar_id):
        """
        Получить серийный номер кроссбара по id
        """
        self.db_connect()
        status = False
        serial = ''
        if self.db_connection:
            try:
                QUERY = f"""SELECT serial FROM Crossbars
                WHERE id={crossbar_id}"""
                self.db_cursor.execute(QUERY)
                serial = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_crossbar_serial_from_id',er)
            except TypeError as er:
                print('get_crossbar_serial_from_id',er)
        self.db_disconnect()
        return status, serial

    def get_memristor_id_from_experiment_id(self, experiment_id):
        """
        Получить id мемрезистора из эксперимента
        """
        self.db_connect()
        status = False
        mem_id = ''
        if self.db_connection:
            try:
                QUERY = f"""SELECT memristor_id FROM Experiments
                WHERE id={experiment_id}"""
                self.db_cursor.execute(QUERY)
                mem_id = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_memristor_id_from_experiment_id',er)
            except TypeError as er:
                print('get_memristor_id_from_experiment_id',er)
        self.db_disconnect()
        return status, mem_id
    
    def get_crossbar_id_from_memristor_id(self, memristor_id):
        """
        Получить id кроссбара из мемрезистора
        """
        self.db_connect()
        status = False
        crb_id = ''
        if self.db_connection:
            try:
                QUERY = f"""SELECT crossbar_id FROM Memristors
                WHERE id={memristor_id}"""
                self.db_cursor.execute(QUERY)
                crb_id = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_crossbar_id_from_memristor_id',er)
            except TypeError as er:
                print('get_crossbar_id_from_memristor_id',er)
        self.db_disconnect()
        return status, crb_id
    
    def get_wl_from_memristor_id(self, memristor_id):
        """
        Получить WL из мемрезистора
        """
        self.db_connect()
        status = False
        wl = ''
        if self.db_connection:
            try:
                QUERY = f"""SELECT wl FROM Memristors
                WHERE id={memristor_id}"""
                self.db_cursor.execute(QUERY)
                wl = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_wl_from_memristor_id',er)
            except TypeError as er:
                print('get_wl_from_memristor_id',er)
        self.db_disconnect()
        return status, wl
    
    def get_bl_from_memristor_id(self, memristor_id):
        """
        Получить BL из мемрезистора
        """
        self.db_connect()
        status = False
        bl = ''
        if self.db_connection:
            try:
                QUERY = f"""SELECT bl FROM Memristors
                WHERE id={memristor_id}"""
                self.db_cursor.execute(QUERY)
                bl = self.db_cursor.fetchone()[0]
                status = True
            except sqlite3.Error as er:
                print('get_bl_from_memristor_id',er)
            except TypeError as er:
                print('get_bl_from_memristor_id',er)
        self.db_disconnect()
        return status, bl

    def get_cb_info(self, cb_id):
        """
        Получить полную информацию о кроссбаре
        """
        self.db_connect()
        status = False
        info = []
        if self.db_connection:
            try:
                QUERY = f"""SELECT * FROM Crossbars
                WHERE id={cb_id}"""
                self.db_cursor.execute(QUERY)
                info = self.db_cursor.fetchall()
                status = True
            except sqlite3.Error as er:
                print('get_cb_info',er)
            except TypeError as er:
                print('get_cb_info',er)
        self.db_disconnect()
        return status, info