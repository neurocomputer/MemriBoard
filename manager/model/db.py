"""
База данных
"""

import os
import pickle
import datetime
import sqlalchemy as sqla
from sqlalchemy import ForeignKey, LargeBinary, String, Integer, select, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError, NoResultFound, MultipleResultsFound
from datetime import datetime
from typing import Optional, List
from manager.service.saves import results_from_bytes
# from manager.service.global_settings import DB_PATH

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

    memristors: Mapped[List['Memristors']] = relationship(
        back_populates='crossbar', 
        cascade='all, delete-orphan'
    )

    # для удобства отладки
    def __repr__(self):
        return f"<Crossbar(id={self.id}, serial='{self.serial}', {self.bl}x{self.wl})>"

class Memristors(Base):
    __tablename__ = 'memristors'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    bl: Mapped[int] = mapped_column(Integer, nullable=False)
    wl: Mapped[int] = mapped_column(Integer, nullable=False)
    last_resistance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # внешний ключ
    crossbar_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('crossbars.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    crossbar: Mapped['Crossbars'] = relationship(back_populates='memristors')
    experiments: Mapped[List['Experiments']] = relationship(
        back_populates='memristor',
        cascade='all, delete-orphan'
    )
    
    # для удобства отладки
    def __repr__(self):
        return f"<Memristor(id={self.id}, bl={self.bl}, wl={self.wl})>"

class Experiments(Base):
    __tablename__ = 'experiments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    datestamp: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    status: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)
    last_resistance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta_info: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    
    # внешний ключ
    memristor_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('memristors.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    memristor: Mapped['Memristors'] = relationship(back_populates='experiments')
    tickets: Mapped[List['Tickets']] = relationship(
        back_populates='experiment',
        cascade='all, delete-orphan'
    )
    
    # для удобства отладки
    def __repr__(self):
        return f"<Experiment(id={self.id}, name='{self.name}')>"

class Tickets(Base):
    __tablename__ = 'tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    datestamp: Mapped[str] = mapped_column(String, nullable=False)
    ticket_name: Mapped[str] = mapped_column(String, nullable=False)
    ticket: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)
    
    # внешний ключ
    experiment_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('experiments.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    experiment: Mapped['Experiments'] = relationship(back_populates='tickets')

    # для удобства отладки
    def __repr__(self):
        return f"<Ticket(id={self.id}, name='{self.ticket_name}', status={self.status})>"

class DBOperate():

    engine = None
    def __init__(self, parent):
        """
        Инициализация
        """
        self.parent = parent
        try:
            base = self.parent.get_meta_info()["database_mode"]
            if base == 'sqlite':
                self.engine = sqla.create_engine('sqlite:///base.db')
            elif base == 'postgress':
                # поднятие сервера
                data_dir = os.path.join(os.getcwd(), 'postgress')
                import pgembed as pg
                server = pg.get_server(data_dir)
                uri = server.get_uri()
                # создание базы, если отсутствует
                engine = sqla.create_engine(uri)
                with engine.connect() as conn:
                    conn.execute(sqla.text("COMMIT"))
                    result = conn.execute(sqla.text("SELECT 1 FROM pg_database WHERE datname='base'"))
                    if not result.fetchone():
                        conn.execute(sqla.text("CREATE DATABASE base"))
                        print("База данных 'base' создана")
                    # проверка соединения с базой
                    db_info = conn.execute(
                    sqla.text("""
                        SELECT datname, datdba, encoding, datcollate, datctype 
                        FROM pg_database 
                        WHERE datname = 'base'
                        """)
                    ).fetchone()
                    if not db_info:
                        print("Не удалось получить информацию о базе 'base'")
                        raise Exception("Не удалось получить информацию о базе 'base'")
                    else:
                        new_uri = uri[:-8]+'base'
                        self.engine = sqla.create_engine(new_uri)
            self.alter_memristors_table()
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в подключении к базе: {e}")

    # ФУНКЦИОНАЛ РАБОТЫ С БАЗОЙ

    def create_empty_db_crossbar(self,
                                serial="ННГУ-1_для_отладки",
                                comment="Кроссбар 32х8 1T1R",
                                bl_num=32,
                                wl_num=8,
                                cb_type='simulator'):
        """
        Создание таблиц и их заполнение
        """

        if self.engine is None:
            print("Ошибка: engine не инициализирован")
            return False, 0
    
        status = False
        crossbar_id = 0
        try:
            session = None
            Base.metadata.create_all(self.engine)
            print("Все таблицы созданы")
            
            Session = sessionmaker(bind=self.engine)
            session = Session()
            print("База данных создана и успешно подключена к SQLAlchemy")

            existing = session.query(Crossbars).filter_by(serial=serial).first()
            if existing:
                print(f"Кроссбар с серийным номером '{serial}' уже существует (id={existing.id})")
                return True, existing.id
            
            new_crossbar = Crossbars(
                serial=serial,
                comment=comment,
                bl=bl_num,
                wl=wl_num,
                cb_type=cb_type
            )
            
            session.add(new_crossbar)
            session.flush()
            crossbar_id = new_crossbar.id
            print("Таблица Crossbars создана и заполнена")
            
            memristors = [
                Memristors(bl=i, wl=j, last_resistance=0, crossbar_id=crossbar_id)
                for i in range(bl_num)
                for j in range(wl_num)
            ]
            session.add_all(memristors)
            session.commit()
            print("Таблица Memristors создана и заполнена")
            
            status = True
        except SQLAlchemyError as error:
            print("Ошибка при подключении к базе данных:", error)
            if session:
                session.rollback()
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
        finally:
            if session:
                session.close()
        return status, crossbar_id

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
                memristor_id = session.scalars(output).one()
                status = True
                return status, memristor_id
        except NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: wl={wl}, bl={bl}, crossbar={crossbar_id}")
            return False, 0
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Найдено несколько мемристоров: wl={wl}, bl={bl}, crossbar={crossbar_id}")
            return False, 0
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_memristor_id: {e}")

    def add_experiment(self, name, memristor_id):
        """
        Добавить эксперимент
        """
        status = False
        experiment_id = 0
        try:
            with Session(self.engine) as session:
                datestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                new_experiment = Experiments(
                    datestamp=datestamp,
                    name=name,
                    status=0,
                    memristor_id=memristor_id
                )
                session.add(new_experiment)
                session.commit()
                experiment_id = new_experiment.id
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f'Ошибка в add_experiment:{e}')
        return status, experiment_id
    
    def update_experiment_status(self, experiment_id, experiment_status):
        """
        Обновить статус эксперимента
        """
        status = False
        try:
            with Session(self.engine) as session:
                experiment = session.get(Experiments, experiment_id)
                if experiment:
                    experiment.status = experiment_status
                    session.commit()
                    status = True
                else:
                    self.parent.db_logger.warning(f"Эксперимент не найден: id={experiment_id}")
        except Exception as e:
            self.parent.db_logger.critical(f'Ошибка в update_experiment_status:{e}')
            
        return status

    def add_ticket(self, ticket, experiment_id):
        """
        Добавляем пустой тикет при примке в работу админом
        """
        ticket_id = 0
        status = False
        try:
            with Session(self.engine) as session:
                datestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                ticket_name = ticket['name']
                ticket_data = pickle.dumps(ticket)
                new_ticket = Tickets(
                    datestamp=datestamp,
                    ticket_name=ticket_name,
                    ticket=ticket_data,
                    status=False,
                    experiment_id=experiment_id
                )
                session.add(new_ticket)
                session.commit()
                ticket_id = new_ticket.id
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f'Ошибка в add_ticket:{e}')
        return status, ticket_id

    def update_ticket(self, ticket_id, name, value):
        """
        Обновить тикет
        """
        status = False
        try:
            with Session(self.engine) as session:
                ticket = session.get(Tickets, ticket_id)
                if ticket:
                    if hasattr(ticket, name):
                        setattr(ticket, name, value)
                        session.commit()
                        status = True
                    else:
                        self.parent.db_logger.error(f"Поле '{name}' не найдено в таблице Tickets")
                else:
                    self.parent.db_logger.warning(f"Тикет не найден: id={ticket_id}")
        except Exception as e:
            self.parent.db_logger.critical(f'Ошибка в update_ticket:{e}')
        return status

    def update_experiment(self, experiment_id, name, value):
        """
        Обновить тикет
        """
        status = False
        try:
            with Session(self.engine) as session:
                experiment = session.get(Experiments, experiment_id)
                if experiment:
                    if hasattr(experiment, name):
                        setattr(experiment, name, value)
                        session.commit()
                        status = True
                    else:
                        self.parent.db_logger.error(f"Поле '{name}' не найдено в таблице Experiments")
                else:
                    self.parent.db_logger.warning(f"Эксперимент не найден: id={experiment_id}")
        except Exception as e:
            self.parent.db_logger.critical(f'Ошибка в update_experiment:{e}')
        return status

    def update_last_resistance(self, memristor_id, last_resistance):
        """
        Обновить значение сопротивления
        """
        status = False
        try:
            with Session(self.engine) as session:
                memristor = session.get(Memristors, memristor_id)
                if memristor:
                    memristor.last_resistance = last_resistance
                    session.commit()
                    status = True
                else:
                    self.parent.db_logger.warning(f"Мемристор не найден: id={memristor_id}")
        except Exception as e:
            self.parent.db_logger.critical(f'Ошибка в update_last_resistance:{e}')
        return status

    def get_chip_data(self, serial: str):
        """
        Получить данные кроссбара по серийному номеру
        """
        chip_data = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Crossbars.id,
                    Crossbars.bl,
                    Crossbars.wl,
                    Crossbars.cb_type
                ).where(Crossbars.serial == serial)
                chip_data = session.execute(output).all()[0]
                status = True
                return status, chip_data
        except NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: serial='{serial}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько кроссбаров с serial='{serial}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_chip_data: {e}")
            return False, []
    
    def get_cb_list(self):
        """
        Список кроссбаров
        """
        if self.engine is None:
            print("Ошибка в get_cb_list: engine не инициализирован")
            return False, 0
        
        cb_list = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(Crossbars.serial)
                cb_list = session.scalars(output).all()
                status = True
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_cb_list: {e}")
        return status, cb_list

    def get_cb_list_cb_type(self, cb_type):
        """
        Список кроссбаров по типу
        """        
        cb_list = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(Crossbars.serial).where(Crossbars.cb_type == cb_type)
                cb_list = session.execute(output).all()
                status = True
                return status, cb_list
        except NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: cb_type='{cb_type}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько кроссбаров с cb_type='{cb_type}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_cb_list_cb_type: {e}")

    def get_exp_name(self, experiment_id):
        """
        Имя эксперимента
        """
        exp_name = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Experiments.name
                ).where(Experiments.id == experiment_id)
                exp_name = session.scalars(output).one()
                status = True
                return status, exp_name
        except NoResultFound:
            self.parent.db_logger.warning(f"Имя эксперимента не найдено: experiment_id='{experiment_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько экспериментов с experiment_id='{experiment_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_exp_name: {e}")
            return False, []

    def get_experiment_tickets(self, experiment_id):
        """
        Тикеты эксперимента
        """
        history = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Tickets.id,
                    Tickets.datestamp,
                    Tickets.ticket_name,
                    Tickets.status
                ).where(Tickets.experiment_id == experiment_id)
                history = session.execute(output).fetchall()
            status = True
            return status, history
        except NoResultFound:
            self.parent.db_logger.warning(f"Эксперимент не найден: id='{experiment_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_experiment_tickets: {e}")
            return False, []

    def get_memristor_experiments(self, memristor_id):
        """
        История всех экспериментов с мемристором
        """
        history = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Experiments.id,
                    Experiments.datestamp,
                    Experiments.name,
                    Experiments.status,
                    Experiments.last_resistance
                ).where(Experiments.memristor_id == memristor_id).order_by(Experiments.datestamp.desc())
                history = session.execute(output).fetchall()
            status = True
            return status, history
        except NoResultFound:
            self.parent.db_logger.warning(f"Эксперимент не найден: memristor_id='{memristor_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_memristor_experiments: {e}")
            return False, []

    def get_experiments(self, crossbar_id):
        """
        История всех экспериментов с кроссбаром
        Можно переделать для всех экспериментов в базе
        """
        history = []
        status = False
        try:
            with Session(self.engine) as session:
                output = (
                    session.query(
                        Experiments.id,
                        Experiments.datestamp,
                        Experiments.name,
                        Experiments.status,
                        Experiments.last_resistance
                    )
                    .select_from(Crossbars)
                    .join(Memristors, Memristors.crossbar_id == Crossbars.id)
                    .join(Experiments, Experiments.memristor_id == Memristors.id)
                    .filter(Crossbars.id == crossbar_id)
                    .order_by(Experiments.datestamp.desc())
                )
                history = session.execute(output).fetchall()
            status = True
            return status, history
        except NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: crossbar_id='{crossbar_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_experiments: {e}")
            return False, []

    def get_last_resistance(self, memristor_id):
        """
        Последнее сопротивление
        """
        resistance = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Memristors.last_resistance
                ).where(Memristors.id == memristor_id)
                resistance = session.scalars(output).one()
                status = True
                return status, resistance
        except NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько мемристоров с memristor_id='{memristor_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_last_resistance: {e}")
            return False, []

    def get_all_resistances(self, crossbar_id):
        """
        Последнее сопротивление
        """
        resistances = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Memristors.bl,
                    Memristors.wl,
                    Memristors.last_resistance
                ).where(Memristors.crossbar_id == crossbar_id)
                resistances = session.execute(output).fetchall()
            status = True
            return status, resistances
        except NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: crossbar_id='{crossbar_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_all_resistances: {e}")
            return False, []

    def get_img_experiment(self, experiment_id):
        """
        Получить рисунок эксперимента из базы
        """
        img = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Experiments.image
                ).where(Experiments.id == experiment_id)
                img = session.scalars(output).one()
                status = True
                return status, img
        except NoResultFound:
            self.parent.db_logger.warning(f"Рисунок не найден: experiment_id='{experiment_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько рисунков с experiment_id='{experiment_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_img_experiment: {e}")
            return False, []

    def get_tickets(self, experiment_id):
        """
        Получить тикеты одного эксперимента
        """
        ticket = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Tickets.ticket
                ).where(Tickets.experiment_id == experiment_id)
                ticket = session.execute(output).fetchall()
            status = True
            return status, ticket
        except NoResultFound:
            self.parent.db_logger.warning(f"Тикет не найден: experiment_id='{experiment_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_tickets: {e}")
            return False, []

    def get_ticket_from_id(self, ticket_id):
        """
        Получить тикет по id
        """
        ticket = []
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Tickets.result
                ).where(Tickets.id == ticket_id)
                ticket = session.scalars(output).one()
                status = True
                return status, ticket
        except NoResultFound:
            self.parent.db_logger.warning(f"Тикет не найден: ticket_id='{ticket_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько тикетов с ticket_id='{ticket_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_ticket_from_id: {e}")
            return False, []

    def get_crossbar_serial_from_id(self, crossbar_id):
        """
        Получить серийный номер кроссбара по id
        """
        serial = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Crossbars.serial
                ).where(Crossbars.id == crossbar_id)
                serial = session.scalars(output).one()
                status = True
                return status, serial
        except NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: crossbar_id='{crossbar_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько кроссбаров с crossbar_id='{crossbar_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_crossbar_serial_from_id: {e}")
            return False, []

    def get_memristor_id_from_experiment_id(self, experiment_id):
        """
        Получить id мемрезистора из эксперимента
        """
        mem_id = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Experiments.memristor_id
                ).where(Experiments.id == experiment_id)
                mem_id = session.scalars(output).one()
                status = True
                return status, mem_id
        except NoResultFound:
            self.parent.db_logger.warning(f"Эксперимент не найден: experiment_id='{experiment_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько экспериментов с experiment_id='{experiment_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_memristor_id_from_experiment_id: {e}")
            return False, []

    def get_crossbar_id_from_memristor_id(self, memristor_id):
        """
        Получить id кроссбара из мемрезистора
        """
        crb_id = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Memristors.crossbar_id
                ).where(Memristors.id == memristor_id)
                crb_id = session.scalars(output).one()
                status = True
                return status, crb_id
        except NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько мемристоров с memristor_id='{memristor_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_crossbar_id_from_memristor_id: {e}")
            return False, []

    def get_wl_from_memristor_id(self, memristor_id):
        """
        Получить WL из мемрезистора
        """
        wl = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Memristors.wl
                ).where(Memristors.id == memristor_id)
                wl = session.scalars(output).one()
                status = True
                return status, wl
        except NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько мемристоров с memristor_id='{memristor_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_wl_from_memristor_id: {e}")
            return False, []

    def get_bl_from_memristor_id(self, memristor_id):
        """
        Получить BL из мемрезистора
        """
        bl = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Memristors.bl
                ).where(Memristors.id == memristor_id)
                bl = session.scalars(output).one()
                status = True
                return status, bl
        except NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько мемристоров с memristor_id='{memristor_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_bl_from_memristor_id: {e}")
            return False, []

    def get_cb_info(self, cb_id):
        """
        Получить полную информацию о кроссбаре
        """
        info = []
        status = False
        try:
            with Session(self.engine) as session:
                # Получаем все столбцы
                all_columns = [getattr(Crossbars, col.name) 
                            for col in Crossbars.__table__.columns]
                output = select(*all_columns).where(Crossbars.id == cb_id)
                result = session.execute(output).all()
                if not result:  # Если результат пустой
                    self.parent.db_logger.warning(f"Кроссбар не найден: cb_id='{cb_id}'")
                    return False, []
                info = [tuple(row) for row in result]
            status = True
            return status, info
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_cb_info: {e}")
            return False, []
        
    def get_last_experiment(self):
        """
        Получить id последнего эксперимента
        """
        status = False
        last = ''
        try:
            with Session(self.engine) as session:
                output = select(sqla.func.max(Experiments.id))
                last = session.execute(output).scalar()
                status = True
                return status, last
        except NoResultFound:
            self.parent.db_logger.warning("Эксперимент не найден")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error("Найдено несколько экмпериментов")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_last_experiment: {e}")
            return False, []

    def get_BLOB_from_ticket_id(self, ticket_id):
        """
        Получить BLOB тикета
        """
        blob = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Tickets.ticket
                ).where(Tickets.id == ticket_id)
                blob = session.scalars(output).one()
                status = True
                return status, blob
        except NoResultFound:
            self.parent.db_logger.warning(f"Тикет не найден: ticket_id='{ticket_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько тикетов с ticket_id='{ticket_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_BLOB_from_ticket_id: {e}")
            return False, []

    def get_meta_info_from_experiment_id(self, experiment_id):
        """
        Получить метаинформацию об эксперименте по experiment_id
        """
        meta_info = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Experiments.meta_info
                ).where(Experiments.id == experiment_id)
                meta_info = session.scalars(output).one()
                status = True
                return status, meta_info
        except NoResultFound:
            self.parent.db_logger.warning(f"Эксперимент не найден: experiment_id='{experiment_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько экспериментов с experiment_id='{experiment_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_meta_info_from_experiment_id: {e}")
            return False, []

    def get_experiment_id_from_ticket_id(self, ticket_id):
        """
        Получить experiment_id по ticket_id
        """
        experiment_id = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(
                    Tickets.experiment_id
                ).where(Tickets.id == ticket_id)
                experiment_id = session.scalars(output).one()
                status = True
                return status, experiment_id
        except NoResultFound:
            self.parent.db_logger.warning(f"Тикет не найден: ticket_id='{ticket_id}'")
            return False, []
        except MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько тикетов с ticket_id='{ticket_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в ticket_id: {e}")
            return False, []
        
    def alter_memristors_table(self):
        """
        Если отсутствует поле счетчика, добавить
        """
        try:
            inspector = sqla.inspect(self.engine)
            columns = [col['name'] for col in inspector.get_columns('memristors')]

            if 'tasks' not in columns:
                # изменяем таблицу
                with self.engine.connect() as conn:
                    conn.execute(sqla.text(
                        "ALTER TABLE memristors ADD COLUMN tasks INTEGER NOT NULL DEFAULT 0"
                    ))
                    conn.commit()

                # подсчет тасков
                with Session(self.engine) as session:
                    stmt = select(
                        Memristors.id,
                        Experiments.id.label('exp_id'),
                        Tickets.id.label('ticket_id'),
                        Tickets.result
                    ).outerjoin(
                        Experiments, Experiments.memristor_id == Memristors.id
                    ).outerjoin(
                        Tickets, Tickets.experiment_id == Experiments.id
                    )
                    
                    rows = session.execute(stmt).all()
                    
                    mem_tasks = {}
                    for row in rows:
                        if row.result:
                            tasks_count = int(len(results_from_bytes(result=row.result)) / 3)
                            mem_tasks[row.id] = mem_tasks.get(row.id, 0) + tasks_count

                # запись подсчитанных тасков
                with self.engine.connect() as conn:
                    for mem_id, tasks_count in mem_tasks.items():
                        conn.execute(
                            sqla.text("UPDATE memristors SET tasks = :tasks WHERE id = :id"),
                            {"tasks": tasks_count, "id": mem_id}
                        )
                    conn.commit()
        except Exception as e:
            print("Ошибка в alter_memristors_table: ", e)
        
    def count_tasks_on_memristor_id(self, memristor_id):
        """
        Посчитать таски одного мемристора
        """
        status = False
        tasks = 0
        try:
            self.update_tasks_for_memristor(memristor_id)
            with Session(self.engine) as session:
                stmt = select(
                    Tickets.result
                ).join(
                    Experiments, Experiments.id == Tickets.experiment_id
                ).where(
                    Experiments.memristor_id == memristor_id,
                    Tickets.result.isnot(None)
                )
                
                results = session.scalars(stmt).all()
                tasks = 0
                for result in results:
                    if result:
                        tasks_count = int(len(results_from_bytes(result=result)) / 3)
                        tasks += tasks_count
                return status, tasks
        except Exception as e:
            print(f"Ошибка подсчета тасков для mem_id={memristor_id}: {e}")
            return status, tasks
        
    def update_tasks_for_memristor(self, memristor_id):
        """
        Обновить поле tasks для конкретного мемристора
        """
        with Session(self.engine) as session:
            try:
                # Подсчитываем таски
                stmt = select(
                    Tickets.result
                ).join(
                    Experiments, Experiments.id == Tickets.experiment_id
                ).where(
                    Experiments.memristor_id == memristor_id,
                    Tickets.result.isnot(None)
                )
                
                results = session.scalars(stmt).all()
                tasks = 0
                for result in results:
                    if result:
                        tasks_count = int(len(results_from_bytes(result=result)) / 3)
                        tasks += tasks_count
                
                session.execute(
                    sqla.text("UPDATE memristors SET tasks = :tasks WHERE id = :id"),
                    {"tasks": tasks, "id": memristor_id}
                )
                session.commit()
                
            except Exception as e:
                print(f"Ошибка обновления тасков для mem_id={memristor_id}: {e}")
                session.rollback()
    
    # def db_backup(self, backup_path) -> None:
    #     """
    #     Резервное копирование базы
    #     """
    #     status = False
    #     try:
    #         base = sqlite3.connect(DB_PATH)
    #         backup = sqlite3.connect(backup_path + 'backup.db')
    #         base.backup(backup)
    #         backup.close()
    #         base.close()
    #     except sqlite3.Error as er:
    #         self.parent.db_logger.critical("bd_backup",er)
    #     return status