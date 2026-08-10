import numpy as np



"""Перечисление всех доступных драйверов с их атрибутами

TEMPLATE

'family'  # Репозиторий драйвера
str: 'COM' | 'MemriCORE' | 'RRAMPiDriver' | 'RRAM_VISA_Drivers'  

'commutation'  # Может ли драйвер коммутировать ячейки 
bool: True | False  

'modes'  # Режимы, доступные в драйвере (см. manager/menu.py)
str: 'standard' | 'visa'

'compliance_type'  # Режим ограничения тока: аппаратный или программный
str: 'soft' | 'hard'

'resistance_scan'  # Как проводится сканирование сопротивлений на главном окне: одним тикетом или множеством. 
Если None, то сканирование недоступно.
Union[str, None]: 'multi-ticket' | 'single-ticket' | None

'disconnect'  # Что надо сделать в Connector.close_port()
Union[str, None]: 'com_close' | None | 'disconnect'  

'get_tech_info'  # Что надо сделать в Connector.get_tech_info() 
str: 'arduino' | 'rpi' | 'elbear' | 'tech_data'  

'impact'  # Что надо сделать в Connector.impact()
str: 'arduino' | 'rpi' | 'elbear' | 'visa'

'custom_impact'  # Что делать в Connector.custom_impact()
Union[str, None]: 'arduino' | None | 'visa'

'connect_to_ext'  # Подключение к внешним выводам на плате: Connector.connect_to_external()
Union[str, None]: 'arduino' | None | 'visa'

'connect_args'  # Аргументы, которые надо передать в Connector при подключении
Union[str, None]: 'com_port' | None | 'visa_adr'

'math_mode'  # Режим в окне математика
Union[str, None]: 'normal' | 'no_crossbar' | None

"""

# TODO в connect.py и crossbar.py встречался драйвер 'rp5_rram_c', а в Connector его нет. Надо его добавить, если такой существует.

DRIVERS = [
        ['',                       'family',	        'commutation', 'modes',    'compliance_type', 'resistance_scan', 'disconnect', 'get_tech_info', 'impact',	 'custom_impact', 'connect_to_ext', 'connect_args', 'math_mode',   'core_scan', ],
        ['memardboard_single',	   'COM',               True,	       'standard', 'soft',            'multi-ticket',    'com_close',  '100',	        'arduino',   'arduino',	      None,             'com_port',     'no_crossbar', False,       ],
        ['memardboard_crossbar',   'COM',               True,	       'standard', 'soft',            'multi-ticket',    'com_close',  '100',	        'arduino',   'arduino',	      'arduino',        'com_port',     'normal',      False,       ],
        ['elbear_nano',	           'MemriCORE',         True,	       'standard', 'soft',            'multi-ticket',    'com_close',  'elbear',	    'elbear',	 None,	          None,             'com_port',     'normal',      False,       ],
        ['elbear_multimode_WR',	   'MemriCORE',         True,	       'standard', 'soft',            'multi-ticket',    'com_close',  'elbear',	    'elbear',	 None,	          None,             'com_port',     None,          False,       ],
        ['elbear_multimode_MVM',   'MemriCORE',         True,	       'standard', 'soft',            'multi-ticket',    'com_close',  'elbear',	    'elbear',	 None,	          None,             'com_port',     None,          False,       ],
        ['rp5_python',	           'MemriCORE',         True,	       'standard', 'soft',            'multi-ticket',    None,	       'rpi',	        'rpi',	     None,	          None,             None,           'normal',      False,       ],
        ['rp5_c',	               'MemriCORE',         True,	       'standard', 'soft',            'multi-ticket',    None,	       'rpi',	        'rpi',	     None,	          None,             None,           'normal',      False,       ],
        ['rp5_fpga_python',	       'MemriCORE',         True,	       'standard', 'soft',            'multi-ticket',    None,	       'rpi',	        'rpi',	     None,	          None,             None,           'normal',      False,       ],
        ['rp5_fpga_c',	           'MemriCORE',	        True,          'standard', 'soft',            'multi-ticket',    None,	       'rpi',	        'rpi',	     None,	          None,             None,           'normal',      False,       ],
        ['rp5_rram_elbear_nano',   'RRAMPiDriver',      True,	       'standard', 'soft',            'multi-ticket',    'com_close',  'rpi', 	        'rpi',	     None,	          None,             'com_port',     'no_crossbar', False,       ],
        ['rp5_rram_python',	       'RRAMPiDriver',      True,	       'standard', 'soft',            'multi-ticket',    None,	       'rpi',	        'rpi',	     None,	          None,             None,           'no_crossbar', False,       ],
        ['pico_client',            'MemriCORE',         True,          'standard', 'soft',            'multi-ticket',    'com_close',  'pico',          'pico',      None,            None,             'com_port',     None,          True,        ],
        ['ITC_1T1R_32x8_switched', 'RRAM_VISA_Drivers', True,	       'visa',     'hard',            'single-ticket',   'disconnect', 'tech_data',	    'visa',	     'visa',	      'visa',           'visa_adr',     None,          False,       ],
        ['ITC_1T1R_probe_station', 'RRAM_VISA_Drivers', False,	       'visa',     'hard',            None,              'disconnect', 'tech_data',	    'visa',	     'visa',	      None,             'visa_adr',     None,          False,       ],
        ['ITC_probe_station',	   'RRAM_VISA_Drivers', False,	       'visa',     'hard',            None,              'disconnect', 'tech_data',	    'visa',	     'visa',	      None,             'visa_adr',     None,          False,       ],
    ]

AVAILABLE_DRIVERS = [row[0] for row in DRIVERS[1:]]

def get_driver_attr(driver: str) -> dict:
    """Get driver attributes"""    
    if driver not in AVAILABLE_DRIVERS:
        raise Exception(f'Unknown driver: {driver}')
    driver_index = np.where(driver == np.array(AVAILABLE_DRIVERS))[0][0] + 1
    attributes = {}
    for attr, value in zip(DRIVERS[0][1:], DRIVERS[driver_index][1:]):
        attributes[attr] = value
    return attributes


def get_driver_list() -> list[str]:
    """Get driver list from the table"""
    return AVAILABLE_DRIVERS
