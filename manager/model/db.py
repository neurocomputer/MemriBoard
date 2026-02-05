"""
База данных
"""

import pickle
import datetime
import sqlite3
import sqlalchemy as sqla
from sqlalchemy import ForeignKey, LargeBinary, DateTime, String, Integer, select, update, insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from datetime import datetime
from typing import Optional
from manager.service.global_settings import DB_PATH

# pylint: disable=C0103,W0718

# todo: добавить логгер базы

class Base(DeclarativeBase):
    pass

class Crossbars(Base):
    __tablename__ = 'crossbars'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    serial: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    comment: Mapped[str] = mapped_column(String, nullable=False)
    bl: Mapped[int] = mapped_column(Integer, nullable=False)
    wl: Mapped[int] = mapped_column(Integer, nullable=False)
    cb_type: Mapped[str] = mapped_column(String, nullable=False)

    # для удобства отладки
    def __repr__(self):
        return f"<Crossbar(id={self.id}, serial='{self.serial}', {self.bl}x{self.wl})>"

class Memristors(Base):
    __tablename__ = 'memristors'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    bl: Mapped[int] = mapped_column(Integer, nullable=False)
    wl: Mapped[int] = mapped_column(Integer, nullable=False)
    last_resistance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # внешний ключ
    crossbar_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('crossbars.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # для удобства отладки
    def __repr__(self):
        return f"<Memristor(id={self.id}, bl={self.bl}, wl={self.wl})>"

class Experiments(Base):
    __tablename__ = 'experiments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_resistance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # внешний ключ
    memristor_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('memristors.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # для удобства отладки
    def __repr__(self):
        return f"<Experiment(id={self.id}, name='{self.name}')>"

class Tickets(Base):
    __tablename__ = 'tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    ticket_name: Mapped[str] = mapped_column(String, nullable=False)
    ticket: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # внешний ключ
    experiment_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('experiments.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # для удобства отладки
    def __repr__(self):
        return f"<Ticket(id={self.id}, name='{self.ticket_name}', status={self.status})>"
    
class DBOperate():
    """
    Методы работы с базой
    """
    db_cursor = None
    db_connection = None
    
    engine = None

    def __init__(self, parent):
        """
        Инициализация
        """
        self.parent = parent
        try:
            self.engine = sqla.create_engine(f'sqlite:///{DB_PATH}')
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в подключении к базе: {e}")

    # БОЛЬШЕ НЕ НУЖНО
    def check_connect(self):
        try:
            self.db_connection.cursor()
            return True
        except Exception as ex:
            return False

    # БОЛЬШЕ НЕ НУЖНО
    def db_connect(self, func_name):
        """
        Подключиться к БД
        """
        status = False
        try:
            self.db_connection = sqlite3.connect(DB_PATH) # выполняется подключение к базе данных
            #self.db_connection.execute("PRAGMA journal_mode = WAL")
            #self.db_connection.execute("PRAGMA busy_timeout = 5000")
            #self.db_connection.execute("PRAGMA synchronous = NORMAL")
            self.db_cursor = self.db_connection.cursor() # позволяет выполнять SQLite-запросы
            self.parent.db_logger.info(f"Cоединение с базой открыто! ({func_name})")
            status = True
        except Exception as ex:
            self.parent.db_logger.critical(f"Ошибка при подключении к БД: {ex}! ({func_name})")
        return status

    # БОЛЬШЕ НЕ НУЖНО
    def db_disconnect(self, func_name):
        """
        Отключение от БД
        """
        if self.check_connect():
            self.db_connection.close() # закрываем соединение
            status = True
            self.parent.db_logger.info(f"Соединение с базой закрыто! ({func_name})")
        else:
            status = False
            self.parent.db_logger.warning(f"Закрыть не удалось! ({func_name})")
        return status
    
    # ФУНКЦИОНАЛ РАБОТЫ С БАЗОЙ

    def get_memristor_id(self, wl: int, bl: int, crossbar_id: int):
        """
        Получить id мемристора
        """
        memristor_id = 0
        status = False
        
        try:
            with Session(self.engine) as session:
                output = select(Memristors.id).where(
                    Memristors.wl == wl,
                    Memristors.bl == bl,
                    Memristors.crossbar_id == crossbar_id
                )
                result = session.scalars(output).one()
                memristor_id = result
                status = True
            
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: wl={wl}, bl={bl}, crossbar={crossbar_id}")
            return False, 0
        except sqla.exc.MultipleResultsFound:
            self.parent.db_logger.error(f"Найдено несколько мемристоров: wl={wl}, bl={bl}, crossbar={crossbar_id}")
            return False, 0
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_memristor_id: {e}")
        
        return status, memristor_id

    def add_experiment(self, name, memristor_id):
        """
        Добавить эксперимент
        """
        self.db_connect('add_experiment')
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
            except Exception as er:
                self.parent.db_logger.critical(f'Ошибка в add_experiment:{er}')
        self.db_disconnect('add_experiment')
        return status, experiment_id

    def update_experiment_status(self, experiment_id, experiment_status):
        """
        Обновить статус эксперимента
        """
        self.db_connect('update_experiment_status')
        status = False
        if self.db_connection:
            try:
                QUERY = f"""UPDATE Experiments
                SET status=(?)
                WHERE id={experiment_id}"""
                self.db_cursor.execute(QUERY, (experiment_status,))
                self.db_connection.commit() # сохранить изменение
                status = True
            except Exception as er:
                self.parent.db_logger.critical(f'Ошибка в update_experiment_status:{er}')
        self.db_disconnect('update_experiment_status')
        return status

    def add_ticket(self, ticket, experiment_id):
        """
        Добавляем пустой тикет при примке в работу админом
        memristor_id <- wl, bl, crossbar_id
        """
        self.db_connect('add_ticket')
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
            except Exception as er:
                self.parent.db_logger.critical(f'Ошибка в add_ticket:{er}')
        self.db_disconnect('add_ticket')
        return status, ticket_id

    def update_ticket(self, ticket_id, name, value):
        """
        Обновить тикет
        """
        self.db_connect('update_ticket')
        status = False
        if self.db_connection:
            try:
                QUERY = f"""UPDATE Tickets
                SET {name}=(?)
                WHERE id={ticket_id}"""
                self.db_cursor.execute(QUERY, (value,))
                self.db_connection.commit() # сохранить изменение
                status = True
            except Exception as er:
                self.parent.db_logger.critical(f'Ошибка в update_ticket:{er}')
        self.db_disconnect('update_ticket')
        return status

    def update_experiment(self, experiment_id, name, value):
        """
        Обновить тикет
        """
        self.db_connect('update_experiment')
        status = False
        if self.db_connection:
            try:
                QUERY = f"""UPDATE Experiments
                SET {name}=(?)
                WHERE id={experiment_id}"""
                self.db_cursor.execute(QUERY, (value,))
                self.db_connection.commit() # сохранить изменение
                status = True
            except Exception as er:
                self.parent.db_logger.critical(f'Ошибка в update_experiment:{er}')
        self.db_disconnect('update_experiment')
        return status

    def update_last_resistance(self, memristor_id, last_resistance):
        """
        Обновить значение сопротивления
        """
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
            except Exception as er:
                self.parent.db_logger.critical(f'Ошибка в update_last_resistance:{er}')
        self.db_disconnect('update_last_resistance')
        return status

    def get_chip_data(self, serial: str):
        """
        Получить данные кроссбара по серийному номеру
        """
        try:
            with Session(self.engine) as session:
                output = select(
                    Crossbars.id, 
                    Crossbars.bl, 
                    Crossbars.wl, 
                    Crossbars.cb_type
                ).where(Crossbars.serial == serial)
                
                row = session.execute(output).one()
                chip_data = list(row)
                return True, chip_data
                
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: serial='{serial}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько кроссбаров с serial='{serial}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_chip_data: {e}")
            return False, []
    
    def get_cb_list(self):
        """
        Список кроссбаров
        """
        status = False
        cb_list = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT serial FROM Crossbars"))
                cb_list = [item[0] for item in result.fetchall()]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_cb_list: {e}")
        return status, cb_list

    def get_cb_list_cb_type(self, cb_type):
        """
        Список кроссбаров по типу
        """
        status = False
        cb_list = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT serial FROM Crossbars WHERE cb_type='{cb_type}'"))
                cb_list = result.fetchall()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_cb_list_cb_type: {e}")
        return status, cb_list

    def get_exp_name(self, experiment_id):
        """
        Имя эксперимента
        """
        status = False
        exp_name = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT name FROM Experiments WHERE id={experiment_id}"))
                exp_name = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_exp_name: {e}")
        return status, exp_name

    def get_experiment_tickets(self, experiment_id):
        """
        Тикеты эксперимента
        """
        status = False
        history = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT id, datestamp, ticket_name, status FROM Tickets WHERE experiment_id={experiment_id}"))
                history = result.fetchall()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_experiment_tickets: {e}")
        return status, history

    def get_memristor_experiments(self, memristor_id):
        """
        История всех экспериментов с мемристором
        """
        status = False
        history = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT id, datestamp, name, status, last_resistance FROM Experiments WHERE memristor_id={memristor_id} ORDER BY id DESC"))
                history = result.fetchall()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_memristor_experiments: {e}")
        return status, history

    def get_experiments(self, crossbar_id):
        """
        История всех экспериментов с кроссбаром
        Можно переделать для всех экспериментов в базе
        """
        status = False
        history = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT e.id, e.datestamp, e.name, e.status, e.last_resistance FROM Crossbars AS c JOIN Memristors AS m ON m.crossbar_id=c.id JOIN Experiments AS e ON e.memristor_id=m.id WHERE m.crossbar_id={crossbar_id} ORDER BY e.datestamp DESC"))
                history = result.fetchall()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_experiments: {e}")
        return status, history

    def get_last_resistance(self, memristor_id):
        """
        Последнее сопротивление
        """
        status = False
        resistance = 0
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT last_resistance FROM Memristors WHERE id={memristor_id}"))
                resistance = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_last_resistance: {e}")
        return status, resistance

    def get_all_resistances(self, crossbar_id):
        """
        Последнее сопротивление
        """
        status = False
        resistances = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT bl, wl, last_resistance from Memristors WHERE crossbar_id={crossbar_id};"))
                resistances = result.fetchall()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_all_resistances: {e}")
        return status, resistances

    def get_img_experiment(self, experiment_id):
        """
        Получить рисунок эксперимента из базы
        """
        status = False
        img = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT image from Experiments WHERE id={experiment_id};"))
                img = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_img_experiment: {e}")
        return status, img

    def get_tickets(self, experiment_id):
        """
        Получить тикеты одного эксперимента
        """
        status = False
        tickets = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT ticket FROM Tickets WHERE experiment_id={experiment_id}"))
                tickets = result.fetchall()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_tickets: {e}")
        return status, tickets

    def get_ticket_from_id(self, ticket_id):
        """
        Получить тикет по id
        """
        status = False
        ticket = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT result FROM Tickets WHERE id={ticket_id}"))
                ticket = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_ticket_from_id: {e}")
        return status, ticket

    def get_crossbar_serial_from_id(self, crossbar_id):
        """
        Получить серийный номер кроссбара по id
        """
        status = False
        serial = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT serial FROM Crossbars WHERE id={crossbar_id}"))
                serial = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_crossbar_serial_from_id: {e}")
        return status, serial

    def get_memristor_id_from_experiment_id(self, experiment_id):
        """
        Получить id мемрезистора из эксперимента
        """
        status = False
        mem_id = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT memristor_id FROM Experiments WHERE id={experiment_id}"))
                mem_id = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_memristor_id_from_experiment_id: {e}")
        return status, mem_id

    def get_crossbar_id_from_memristor_id(self, memristor_id):
        """
        Получить id кроссбара из мемрезистора
        """
        status = False
        crb_id = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT crossbar_id FROM Memristors WHERE id={memristor_id}"))
                crb_id = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_crossbar_id_from_memristor_id: {e}")
        return status, crb_id

    def get_wl_from_memristor_id(self, memristor_id):
        """
        Получить WL из мемрезистора
        """
        status = False
        wl = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT wl FROM Memristors WHERE id={memristor_id}"))
                wl = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_wl_from_memristor_id: {e}")
        return status, wl

    def get_bl_from_memristor_id(self, memristor_id):
        """
        Получить BL из мемрезистора
        """
        status = False
        bl = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT bl FROM Memristors WHERE id={memristor_id}"))
                bl = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_bl_from_memristor_id: {e}")
        return status, bl

    def get_cb_info(self, cb_id):
        """
        Получить полную информацию о кроссбаре
        """
        status = False
        info = []
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT * FROM Crossbars WHERE id={cb_id}"))
                info = result.fetchall()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_cb_info: {e}")
        return status, info

    def add_column_if_not_exist(self, table_name, column_name, column_type):
        """
        Добавить столбец если не существует
        """
        self.db_connect('add_column_if_not_exist')
        status = False
        if self.db_connection:
            try:
                QUERY = f'PRAGMA table_info({table_name})'
                self.db_cursor.execute(QUERY)
                info = self.db_cursor.fetchall()
                column_names = []
                for item in info:
                    column_names.append(item[1])
                if column_name not in column_names:
                    # добавление столбца
                    ADD_COLUMN_LAST_RES = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
                    self.db_cursor.execute(ADD_COLUMN_LAST_RES)
                    status = True
            except Exception as er:
                self.parent.db_logger.critical(f'Ошибка в add_column_if_not_exist:{er}')
        self.db_disconnect('add_column_if_not_exist')
        return status

    def get_last_experiment(self):
        """
        Получить id последнего запроса
        """
        status = False
        last = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT MAX(id) FROM Experiments"))
                last = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_last_experiment: {e}")
        return status, last

    def get_BLOB_from_ticket_id(self, ticket_id):
        """
        Получить BLOB тикета
        """
        status = False
        blob = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT ticket FROM Tickets WHERE id = {ticket_id}"))
                blob = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_BLOB_from_ticket_id: {e}")
        return status, blob

    def get_meta_info_from_experiment_id(self, experiment_id):
        """
        Получить метаинформацию об эксперименте по experiment_id
        """
        status = False
        meta_info = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT meta_info FROM Experiments WHERE id={experiment_id}"))
                meta_info = result.fetchone()[0]
                meta_info = pickle.loads(meta_info)
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_meta_info_from_experiment_id: {e}")
        return status, meta_info

    def get_experiment_id_from_ticket_id(self, ticket_id):
        """
        Получить experiment_id по ticket_id
        """
        status = False
        experiment_id = ''
        try:
            with self.engine.connect() as db:
                result = db.execute(sqla.text(f"SELECT experiment_id FROM Tickets WHERE id = {ticket_id}"))
                experiment_id = result.fetchone()[0]
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_experiment_id_from_ticket_id: {e}")
        return status, experiment_id
    
    def db_backup(self, backup_path) -> None:
        """
        Резервное копирование базы
        """
        status = False
        try:
            base = sqlite3.connect(DB_PATH)
            backup = sqlite3.connect(backup_path + 'backup.db')
            base.backup(backup)
            backup.close()
            base.close()
        except sqlite3.Error as er:
            self.parent.db_logger.critical("bd_backup",er)
        return status