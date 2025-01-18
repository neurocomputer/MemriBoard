"""
Application
"""

# pylint: disable=W0401,W0614,R0902,C0321

import logging
from configparser import ConfigParser
from logging import Logger
from manager.menu import menu
from manager.model.db import DBOperate
from manager.service.global_settings import LOG_PATH, SETTINGS_PATH
from manager.service.prepare import prepare

class Application():
    """
    Application
    """

    ap_log_path: str # путь к логу
    ap_config_path: str # путь к конфигу
    ap_config: ConfigParser # конфиг
    ap_logger: Logger # логгер
    dac_bit: int # разрядность ЦАП
    vol_ref_dac: float # опорное напряжение ЦАП
    res_load: int # нагрузочный резистор
    vol_read: float # напряжение чтения
    adc_bit: int # разрядность АЦП
    vol_ref_adc: float # опорное напряжение АЦП
    res_switches: float # сопротивление переключателей
    gain: int # усиление
    menu: dict # меню режимов
    blank_type: str # тип бланка
    _port: str # com порт
    row_num: int # кол-во строк
    col_num: int # кол-во столбцов
    db: DBOperate
    status_db_connect: bool

    def __init__(self) -> None:
        # это выполняется везде где есть наследование от Application и super().__init__()
        prepare()
        self.ap_log_path = LOG_PATH
        self.ap_config_path = SETTINGS_PATH
        self.ap_config = ConfigParser() # создаём объекта парсера
        self.ap_logger = logging.getLogger(__name__)
        self.read_settings() # читаем настройки
        logging.basicConfig(level=logging.INFO, # настраиваем логгер
                            filename=self.ap_log_path,
                            filemode=self.ap_config["logging"]["filemode"],
                            format="%(asctime)s %(levelname)s %(message)s")
        self.ap_logger.setLevel(logging.WARNING)
        self.menu = menu
        self.db = DBOperate()
        status_db_connect = self.db.db_connect()
        if not status_db_connect:
            assert 0 # нет подключения к БД
        self.db.db_disconnect()

    def read_settings(self) -> None:
        """
        Прочитать настройки платы
        """
        self.ap_config.read(self.ap_config_path, encoding="utf-8")  # читаем конфиг
        self._port = self.ap_config['connector']['com_port']
        self.blank_type = self.ap_config['connector']['c_type']
        # для отдельных настроек создаем алиасы
        self.dac_bit = int(self.ap_config['board']['dac_bit'])
        self.vol_ref_dac = float(self.ap_config['board']['vol_ref_dac'])
        self.res_load = int(self.ap_config['board']['res_load'])
        self.vol_read = float(self.ap_config['board']['vol_read'])
        self.adc_bit = int(self.ap_config['board']['adc_bit'])
        self.vol_ref_adc = float(self.ap_config['board']['vol_ref_adc'])
        self.res_switches = float(self.ap_config['board']['res_switches'])
        self.gain = float(self.ap_config['board']['gain'])
        self.soft_cc = float(self.ap_config['board']['soft_cc'])

    def save_settings(self, **kwargs):
        """
        Сохранить настройки
        """
        if "adc_bit" in kwargs:
            self.ap_config['board']['adc_bit'] = kwargs["adc_bit"]
        if "gain" in kwargs:
            self.ap_config['board']['gain'] = kwargs["gain"]
        if "soft_cc" in kwargs:
            self.ap_config['board']['soft_cc'] = kwargs["soft_cc"]
        if "last_crossbar_serial" in kwargs:
            self.ap_config['gui']['last_crossbar_serial'] = kwargs["last_crossbar_serial"]
        if "com_port" in kwargs:
            self.ap_config['connector']['com_port'] = kwargs["com_port"]
        if "c_type" in kwargs:
            self.ap_config['connector']['c_type'] = kwargs["c_type"]
        # запись в файл
        with open(self.ap_config_path, 'w', encoding='utf-8') as configfile:
            self.ap_config.write(configfile)
        self.read_settings()
