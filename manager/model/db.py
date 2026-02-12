"""
База данных
"""

import pickle
import datetime
import sqlite3
import sqlalchemy as sqla
from sqlalchemy import ForeignKey, LargeBinary, String, Integer, select
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
    datestamp: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_resistance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta_info: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    
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
    datestamp: Mapped[str] = mapped_column(String, nullable=False)
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
                memristor_id = session.scalars(output).one()
                status = True
                return status, memristor_id
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: wl={wl}, bl={bl}, crossbar={crossbar_id}")
            return False, 0
        except sqla.exc.MultipleResultsFound:
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
        cb_list = ''
        status = False
        try:
            with Session(self.engine) as session:
                output = select(Crossbars.serial)
                cb_list = session.scalars(output).all()
                status = True
                return status, cb_list
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в get_cb_list: {e}")

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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: cb_type='{cb_type}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Имя эксперимента не найдено: experiment_id='{experiment_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
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
                ).where(Experiments.memristor_id == memristor_id)
                history = session.execute(output).fetchall()
            status = True
            return status, history
        except sqla.exc.NoResultFound:
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
        except sqla.exc.NoResultFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Рисунок не найден: experiment_id='{experiment_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Тикет не найден: ticket_id='{ticket_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Кроссбар не найден: crossbar_id='{crossbar_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Эксперимент не найден: experiment_id='{experiment_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Мемристор не найден: memristor_id='{memristor_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning("Эксперимент не найден")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Тикет не найден: ticket_id='{ticket_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Эксперимент не найден: experiment_id='{experiment_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
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
        except sqla.exc.NoResultFound:
            self.parent.db_logger.warning(f"Тикет не найден: ticket_id='{ticket_id}'")
            return False, []
        except sqla.exc.MultipleResultsFound:
            self.parent.db_logger.error(f"Несколько тикетов с ticket_id='{ticket_id}'")
            return False, []
        except Exception as e:
            self.parent.db_logger.critical(f"Ошибка в ticket_id: {e}")
            return False, []
    
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