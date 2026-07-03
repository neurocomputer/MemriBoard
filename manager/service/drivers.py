import numpy as np



"""Перечисление всех доступных драйверов с их атрибутами

TEMPLATE

'family'  # Репозиторий драйвера
str: 'COM' | 'MemriCORE' | 'RRAMPiDriver' | 'RRAM_VISA_Drivers'  

'commutation'  # Может ли драйвер коммутировать ячейки 
bool: True | False  

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
        ['',                       'family',	        'commutation', 'disconnect', 'get_tech_info', 'impact',	 'custom_impact', 'connect_to_ext', 'connect_args', 'math_mode',   ],
        ['memardboard_single',	   'COM',               True,	       'com_close',	 '100',	          'arduino', 'arduino',	      None,             'com_port',     'no_crossbar', ],
        ['memardboard_crossbar',   'COM',               True,	       'com_close',	 '100',	          'arduino', 'arduino',	      'arduino',        'com_port',     'normal',      ],
        ['elbear_nano',	           'MemriCORE',         True,	       'com_close',	 'elbear',	      'elbear',	 None,	          None,             'com_port',     'normal',      ],
        ['elbear_multimode_WR',	   'MemriCORE',         True,	       'com_close',	 'elbear',	      'elbear',	 None,	          None,             'com_port',     None,          ],
        ['elbear_multimode_MVM',   'MemriCORE',         True,	       'com_close',	 'elbear',	      'elbear',	 None,	          None,             'com_port',     None,          ],
        ['rp5_python',	           'MemriCORE',         True,	       None,	     'rpi',	          'rpi',	 None,	          None,             None,           'normal',      ],
        ['rp5_c',	               'MemriCORE',         True,	       None,	     'rpi',	          'rpi',	 None,	          None,             None,           'normal',      ],
        ['rp5_fpga_python',	       'MemriCORE',         True,	       None,	     'rpi',	          'rpi',	 None,	          None,             None,           'normal',      ],
        ['rp5_fpga_c',	           'MemriCORE',	        True,          None,	     'rpi',	          'rpi',	 None,	          None,             None,           'normal',      ],
        ['rp5_rram_elbear_nano',   'RRAMPiDriver',      True,	       'com_close',	 'rpi', 	      'rpi',	 None,	          None,             'com_port',     'no_crossbar', ],
        ['rp5_rram_python',	       'RRAMPiDriver',      True,	       None,	     'rpi',	          'rpi',	 None,	          None,             None,           'no_crossbar', ],
        ['ITC_1T1R_32x8_switched', 'RRAM_VISA_Drivers', True,	       'disconnect', 'tech_data',	  'visa',	 'visa',	      'visa',           'visa_adr',     None,          ],
        ['ITC_1T1R_probe_station', 'RRAM_VISA_Drivers', False,	       'disconnect', 'tech_data',	  'visa',	 'visa',	      None,             'visa_adr',     None,          ],
        ['ITC_probe_station',	   'RRAM_VISA_Drivers', False,	       'disconnect', 'tech_data',	  'visa',	 'visa',	      None,             'visa_adr',     None,          ],
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
