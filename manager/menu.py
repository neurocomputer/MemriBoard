"""
Меню режимов
"""
import os
import json
from collections.abc import Generator

from manager.service.global_settings import TICKET_PATH
from manager.modes import get_tst, get_std, SMUGen


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
                'smu_iv_dc': 'Voltage Sweep (DC, async)',
                'smu_pulsed_retention': 'Pulsed retention (async)',
                'smu_endurance': 'Endurance (async)',
                'smu_pot_dep': 'Potentiation-Depression (async)',
                'smu_cc-cv': 'CC | CV (DC, async)',
                'smu_cv-cc': 'CV | CC (DC, async)',
                'smu_iv_current': 'Current Sweep (DC, async)'
            }
            # Generator functions for each mode
            self._smu_gen = SMUGen(parent=self, logger=self.parent.ap_logger)
            self._mode_functions = {
                'prog_sync': self._smu_gen.smu_prog_sync,
                'smu_iv_dc': self._smu_gen.smu_iv_dc,
                'smu_pulsed_retention': self._smu_gen.smu_pulsed_retention,
                'smu_endurance': self._smu_gen.smu_endurance,
                'smu_pot_dep': self._smu_gen.smu_pot_dep,
                'smu_cc-cv': self._smu_gen.smu_cc_cv,
                'smu_cv-cc': self._smu_gen.smu_cv_cc,
                'smu_iv_current': self._smu_gen.smu_iv_current
            }
            # UI fields necessary to configure this mode in Signal window (gui/widgets/SignalParametersConfig.py)
            self._ui_fields = {
                'prog_sync': 'volt_sweep, +amp_read, +batch_pulses',  # Standard volt_sweep + read voltage
                'smu_iv_dc': 'volt_sweep, pw_to_int',  # Replace pulse width with trigger interval
                'smu_pulsed_retention': 'retention, +amp_read, +pw, +period, +comp, +batch_pulses',  # Standard retention (nothing) + read voltage + pulse width + pulse period + compliance
                'smu_endurance': 'endurance, +period, +amp_read, +batch_cycles_4',  # Add period, add read amplitude, batch_size: 1 cycle is 4 pulses
                'smu_pot_dep': 'endurance, +period, +batch_pulses',  # Add period
                'smu_cc-cv': 'volt_sweep, dir_to_curr',  # Dir sweep value is current
                'smu_cv-cc': 'volt_sweep, rev_to_curr',  # Rev sweep value is current
                'smu_iv_current': 'volt_sweep, dir_to_curr, rev_to_curr'  # Both dir and rev sweeps are for current
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
    
    
    def get_measure_ticket(self) -> dict:
        """Get measure ticket from the settings.ini"""
        name = self.parent.ap_config['gui']['measure_ticket']
        fname = os.path.join(TICKET_PATH, name)
        with open(fname, encoding='utf-8') as file:
            ticket = json.load(file)
        return ticket
