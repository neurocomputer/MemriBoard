"""
Меню режимов
"""
from manager.modes import get_tst, get_std
from collections.abc import Generator


class Menu:
    """Menu with available modes"""
    def __init__(self):
        """Menu with available modes"""
        self.base_modes = {  # Modes and their aliases
            'volt_sweep': 'Voltage sweep',
            'endurance': 'Endurance',
            'retention': 'Retention',
            'pot-dep': 'Potentiation-Depression'
        }
        
        
    def __getitem__(self, key: str) -> Generator[list, None, None]:
        """Get the menu item"""
        if key == 'tst':
            return get_tst
        if key in self.base_modes:
            return lambda params, terminate, blank_type: get_std(key, params, terminate, blank_type)
        raise KeyError(key)
    
    
    def mode_to_alias(self) -> dict:
        """Get the dict which translates from mode to alias"""
        return self.base_modes        
    
    
    def alias_to_mode(self) -> dict:
        """Get the dict which translates from alias to mode"""
        return {val: key for key, val in self.base_modes.items()}
