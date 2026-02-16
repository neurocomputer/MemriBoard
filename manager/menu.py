"""
Меню режимов
"""
from manager.modes import get_tst, get_std, get_visa

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
    elif board_type in ['VISA', 'VISA_test']:
        menu: dict = {
                'std': get_visa,
            }
    return menu
