"""Class the implements Connector.impact() for visa drivers"""
from logging import Logger
from typing import Union

from manager.service import r2a

try:
    from RRAM_VISA_Drivers import ITC_probe_station, ITC_1T1R_probe_station, ITC_1T1R_32x8_switched
    drivers_available = True
except ModuleNotFoundError:
    drivers_available = False



class VisaImpact:
    """Class the implements Connector.impact() for visa drivers"""
    
    interface: Union[ITC_probe_station, ITC_1T1R_probe_station, ITC_1T1R_32x8_switched]
    logger: Logger
    config: dict
    driver_attr: dict
    board_type: str
    
    def __init__(
        self,
        parent,
        interface: Union[ITC_probe_station, ITC_1T1R_probe_station, ITC_1T1R_32x8_switched],
        logger: Logger,
        config: dict,
        driver_attr: dict,
        board_type: str
    ):
        """Class the implements Connector.impact() for visa drivers"""
        if not drivers_available:
            raise ModuleNotFoundError('Visa drivers are not available! Install them to the MemriBoard folder.')
        # TODO: remove what's not needed
        self.parent = parent  # board.py/Connector
        self.interface = interface
        self.logger = logger
        self.config = config
        self.driver_attr = driver_attr
        self.board_type = board_type
        # Available task modes
        self.task_modes = {
            'connect_cell': self.connect_cell,
            'standby': self.standby,
            'panic': self.panic,
            'need_stop': self.send_need_stop,
            'sense': self.sense,
            'config_std': self.config_std,
            'config_iv_dc': lambda task: self.config_iv_dc(task, sweep_val='voltage'),
            'config_iv_current_dc': lambda task: self.config_iv_dc(task, sweep_val='current'),
            'config_pulsed_retention': self.config_pulsed_retention,
            'config_endurance': self.config_endurance,
            'config_pot_dep': self.config_pot_dep,
        }
        
        
    def __call__(self, task: dict) -> tuple:
        """Calling impact"""
        res = self.task_modes[task['mode']](task)
        self.interface.logger.info(f'Impact: res = {res}')
        return res
    
    
    def log(self, flag: bool, response: str, add_error_info: str) -> None:
        """Log a message as error or info based on the flag"""
        if flag:
            self.logger.info(str(response))
        else:
            self.logger.critical(add_error_info + str(response))
        
        
    def connect_cell(self, task: dict) -> tuple:
        """Connect cell of the crossbar"""
        flag, response = self.interface.connect_cell(wl=task['wl'], bl=task['bl'])
        self.log(flag, response)
        return int(flag)
    
    
    def standby(self, task: dict) -> tuple:
        """Set insrtuments to standby mode"""
        flag, response = self.interface.standby()
        self.log(flag, response)
        return int(flag)
    
    
    def panic(self, task: dict) -> tuple:
        """Stop the ongoing experiment"""
        self.logger.info('Panic started for VISA-instruments')
        flag, response = self.interface.panic()
        if flag:
            self.logger.info('Panic resolved')
        else:
            self.logger.critical(f'Panic was not resolved!: {response}')
        return int(flag)
    
    
    def send_need_stop(self, task) -> tuple:
        """Send need stop flag to the driver if it's stuck"""
        self.interface.stop_experiment()
        self.logger.info('Need stop sent to the driver')
        return 1
    
    
    def sense(self, task: dict) -> tuple:
        """Get measurement data"""
        sense_data = self.interface.sense(vol=task.get('vol'))
        if isinstance(sense_data, str):
            self.logger.critical(f'Sense error: {sense_data}')
            return 0
        adc = r2a(  # TODO remove when output format changed
            gain = float(self.config['board']['gain']),
            res_load = float(self.config['board']['res_load']),
            vol_read = float(self.config['board']['vol_read']),
            adc_bit = int(self.config['board']['adc_bit']),
            vol_ref_adc = float(self.config['board']['vol_ref_adc']),
            res_switches = float(self.config['board']['res_switches']),
            res = sense_data[0]
        )
        return (sense_data[0], task['id'], adc, *sense_data[1:])
    
    
    def config_std(self, task: dict) -> tuple:
        """Configure std mode"""
        flag, response = self.interface.config_std(  # TODO reimplement driver
            volt_array = task['volt_array'],
            compliance = task['compliance'],
            pulse_width = task['pulse_width'],
            read_voltage = task['read_voltage'],
            read_direction = task['read_direction'],
            sign = task['sign'],
        )
        self.log(flag, response, 'Configuring STD error: ')
        return int(flag)
    
    
    def config_iv_dc(self, task: dict, sweep_val: str) -> tuple:
        """Configure iv_dc mode"""
        if sweep_val == 'voltage':
            flag, response = self.interface.config_iv_dc(  # TODO reimplement driver
                v_start = task['start'],
                v_stop = task['stop'],
                n_points = task['n_points'],
                current_compliance = task['compliance'],
                trigger_interval = task['time_interval'],
                double = task['double'],
                sign = task['sign']
            )
        else:
            flag, response = self.interface.config_current_sweep(  # TODO reimplement driver
                i_start = task['start'],
                i_stop = task['stop'],
                n_points = task['n_points'],
                voltage_compliance = task['compliance'],
                trigger_interval = task['time_interval'],
                double = task['double'],
                sign = task['sign']
            )
        self.log(flag, response, 'Configuring IV DC error: ')
        return int(flag)
    
    
    def config_pulsed_retention(self, task: dict) -> tuple:
        """Configure pulsed retention mode"""
        flag, response = self.interface.config_pulsed_retention(
            pulse_width = task['pulse_width'], 
            trigger_interval = task['pulse_period'],
            compliance = task['compliance'],
            count = task['count'],
            read_voltage = task['read_voltage'],
            sign = task['sign']
        )
        self.log(flag, response, 'Configuring Pulsed Retention error: ')
        return int(flag)
    
    
    def config_endurance(self, task: dict) -> tuple:
        """Configure endurance mode"""
        flag, response = self.interface.config_endurance(
            v_dir = task['amplitude_dir'],
            v_rev = task['amplitude_rev'],
            dir_cc = task['compliance_dir'],
            rev_cc = task['compliance_rev'],
            pulse_width = task['pulse_width'], 
            trigger_interval = task['pulse_period'],
            read_voltage = task['read_voltage'],
            read_direction = task['read_direction'],
            reverse = task['reverse'],
            count = task['count'],
        )
        self.log(flag, response, 'Configuring Endurance error: ')
        return int(flag)
    
    
    def config_pot_dep(self, task: dict) -> tuple:
        """Configure potentiation-depression mode"""
        flag, response = self.interface.config_pot_dep(
            voltage = task['volage'],
            compliance = task['compliance'],
            pulse_width = task['pulse_width'], 
            trigger_interval = task['pulse_period'],
            count = task['count'],
            sign = task['sign']
        )
        self.log(flag, response, 'Configuring pot-dep error: ')
        return int(flag)
        