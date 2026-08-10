"""
Меню режимов
"""
from manager.modes import get_tst, get_std, SMUGen
from collections.abc import Generator


# Basic modes used in example tickets
BASE_MODES = ['volt_sweep', 'endurance', 'retention', 'pot-dep']


class Menu:
    """
    Меню связывает сущности board_type, ticket['mode'] и manager.modes
    """
    def __init__(self, parent):
        """
        Меню связывает сущности board_type, ticket['mode'] и manager.modes
        """
        self.parent = parent  # Manager
        
        # Setting the signal modes
        
        # Standard generators for arduino/raspberry boards
        if self.parent.driver_attr['modes'] == 'standard':
            # Modes and their aliases
            self._modes = {
                'volt_sweep': 'Voltage sweep',
                'endurance': 'Endurance',
                'retention': 'Retention',
                'pot-dep': 'Potentiation-Depression'
            }
            # Generator functions for each mode
            self._mode_functions = {
                'volt_sweep': lambda params, terminate, blank_type: get_std('volt_sweep', params, terminate, blank_type),
                'endurance': lambda params, terminate, blank_type: get_std('endurance', params, terminate, blank_type),
                'retention': lambda params, terminate, blank_type: get_std('retention', params, terminate, blank_type),
                'pot-dep': lambda params, terminate, blank_type: get_std('endurance', params, terminate, blank_type)  # Same as endurance
            }
            # UI fields necessary to configure this mode in Signal window (gui/widgets/SignalParametersConfig.py)
            self._ui_fields = {
                'volt_sweep': 'volt_sweep',  # Standard volt_sweep: sweep voltage, 
                'endurance': 'volt_endurance',  # Standard endurance: amplitude, compliance, pulse_width, amounts, double
                'retention': 'retention',  # Standard retention: no fields
                'pot-dep': 'volt_endurance'  # Same as endurance
            }
            # Setting crossbar scan generator (This group of drivers uses multi-ticket generation) for crossbar window
            self.crossbar_scan_gen = None  # Multi-ticket
            
        # Generators for VISA-instruments
        elif self.parent.driver_attr['modes'] == 'visa':
            # Modes and their aliases
            self._modes = {
                'prog_sync': 'Programming (sync)',
                'smu_iv_dc': 'IV DC (async)',
                'smu_pulsed_retention': 'Pulsed retention (async)',
                'smu_endurance': 'Endurance (async)',
                'smu_pot_dep': 'Potentiation-Depression (async)',
            }
            # Generator functions for each mode
            self._smu_gen = SMUGen(logger=self.parent.ap_logger)
            self._mode_functions = {
                'prog_sync': self._smu_gen.smu_std,
                'smu_iv_dc': self._smu_gen.smu_iv_dc,
                'smu_pulsed_retention': self._smu_gen.smu_pulsed_retention,
                'smu_endurance': self._smu_gen.smu_endurance,
                'smu_pot_dep': self._smu_gen.smu_pot_dep,
            }
            # UI fields necessary to configure this mode in Signal window (gui/widgets/SignalParametersConfig.py)
            self._ui_fields = {
                'prog_sync': 'volt_sweep, +amp_read',  # Standard volt_sweep
                'smu_iv_dc': 'volt_sweep, pw_to_int',  # Replace pulse width with trigger interval
                'smu_pulsed_retention': 'endurance, -amp, +amp_read, +period, -amount',  # Standard endurance + remove amplitude, add read amplitude, add period, remove amount
                'smu_endurance': 'endurance, +period, +amp_read',  # Add period, add read amplitude
                'smu_pot_dep': 'endurance, +period'  # Add period
            }
            # Setting crossbar scan generator (This group of drivers uses single ticket scanning) for crossbar window
            self.crossbar_scan_gen = self._smu_gen.crossbar_scan  # Single-ticket
            
        else:
            raise RuntimeError(f"Manager/Menu initialization: Unknown 'modes' field in driver attr: {self.parent.driver_attr['modes']}")
        
        
    def __getitem__(self, key: str) -> Generator[list, None, None]:
        """Get the menu item"""
        if key == 'tst':
            return get_tst
        if key in self._mode_functions:
            return self._mode_functions[key]
        raise KeyError(key)
    
    
    def mode_to_alias(self) -> dict:
        """Get the dict which translates from mode to alias"""
        return self._modes        
    
    
    def alias_to_mode(self) -> dict:
        """Get the dict which translates from alias to mode"""
        return {val: key for key, val in self._modes.items()}
    
    
    def ui_fields(self, mode: str) -> str:
        """Get the ui fields needed for a specific mode"""
        return self._ui_fields[mode]
    
    
    def check_mode_compatibility(self, mode: str) -> bool:
        """Check if the mode is compatible with driver in use"""
        return mode in self._modes
