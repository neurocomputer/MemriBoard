"""
Меню режимов
"""
from manager.modes import (
    get_tst, 
    get_std, 
    get_smu_iv_dc, 
    get_smu_std, 
    get_smu_pulsed_retention,
    get_smu_endurance,
    get_smu_pot_dep,
    get_visa_crossbar_scan
)

def get_menu(board_type, logger=None):
    '''
    Меню связывает сущности board_type, ticket['mode'] и manager.modes
    '''
    menu: dict = {}
    if board_type in ['offline',
                      'memardboard_single',
                      'memardboard_crossbar',
                      'rp5_python',
                      'rp5_c',
                      'rp5_fpga_python',
                      'rp5_fpga_c',
                      'elbear_nano',
                      'rp5_rram_python',
                      'rp5_rram_c']:
        menu: dict = {
                'tst': get_tst,
                'std': get_std,
            }
    elif board_type in ['ITC_1T1R_32x8_switched', 'ITC_1T1R_32x8_probe_station', 'ITC_probe_station']:
        menu: dict = {  # TODO на этом этапе уже как будто лучше сделать меню целым классом, у которого есть методы и атрибут menu
                'std': lambda params, terminate, blank_type: get_smu_std(params, terminate, blank_type, logger),
                'smu_iv_dc': lambda params, terminate, blank_type: get_smu_iv_dc(params, terminate, blank_type, logger),
                'smu_pulsed_retention': lambda params, terminate, blank_type: get_smu_pulsed_retention(params, terminate, blank_type, logger),
                'smu_endurance': lambda params, terminate, blank_type: get_smu_endurance(params, terminate, blank_type, logger),
                'smu_pot_dep': lambda params, terminate, blank_type: get_smu_pot_dep(params, terminate, blank_type, logger),
            }
    return menu


def get_crossbar_scan(board_type, logger=None):
    """
    Генератор тасков для режима сканирования кроссбара.
    """
    if board_type in ['ITC_1T1R_32x8_switched', 'ITC_1T1R_32x8_probe_station', 'ITC_probe_station']:
        return lambda params, terminate, blank_type: get_visa_crossbar_scan(params, terminate, blank_type, logger)
    return None
