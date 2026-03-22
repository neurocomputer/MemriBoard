"""
Меню режимов
"""
from manager.modes import (
    get_tst, 
    get_std, 
    get_smu_iv_dc, 
    get_smu_std, 
    get_smu_pulsed_retention
)

def get_menu(board_type):
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
    elif board_type in ['ITC_1T1R_32x8_switched', 'ITC_1T1R_32x8_probe_station']:
        menu: dict = {
                'std': get_smu_std,
                'smu_iv_dc': get_smu_iv_dc,
                'smu_pulsed_retention': get_smu_pulsed_retention,
            }
    return menu
