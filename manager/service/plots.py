"""
Вспомогательные функции для рисования
plot_for_signal_graph - рисование графика на окне Сигнал
"""
from matplotlib.axes import Axes
from manager.algorithms import execute_algorithm
import numpy as np

# pylint: disable=C0103,W0212


def calculate_counts_for_ticket(parent, ticket: dict):
    """
    Посчитать количество задач для тикета или алгоритма
    """
    if ticket['mode'] == 'algorithm':  # Calculating for algorithms
        status, count = execute_algorithm(algorithm_code=ticket['code'], manager=parent)
        if status:
            return count
        else: 
            return 0
    # получаем генератор задач
    task = parent.menu[ticket['mode']], (ticket['params'],
                                        ticket['terminate'],
                                        parent.blank_type)
    count = 0
    for _ in task[0](*task[1]):
        count += 1
    return count


def plot_for_signal_graph(manager, ticket: dict, plot_type: str, ax: Axes, plot_limits: dict, lang_pack: dict) -> tuple[int, bool]:
    """Plot the graph on the Signal window and return task count"""
    if manager.driver_attr['modes'] == 'standard':
        return plot_standard(manager, ticket, plot_type, ax, plot_limits, lang_pack)
    elif manager.driver_attr['modes'] == 'visa':
        plotter = VisaPlotter(manager, ticket, plot_type, ax, plot_limits, lang_pack)
        return plotter.plot()
    else:
        ax.text(0.1, 0.1, 'Unknown driver mode :(')
        return 0, False


def plot_standard(manager, ticket, plot_type: str, ax: Axes, plot_limits: dict, lang_pack: dict) -> tuple[int, bool]:
    """Plot for standard menu"""
    # получаем генератор задач
    task_gen = manager.menu[ticket['mode']](ticket['params'], ticket['terminate'], manager.blank_type)
    READ_VOLTAGE = manager.vol_read
    READ_TIME = int(manager.ap_config['board']['read_time'])
    BLANK_TIME = int(manager.ap_config['board']['blank_time'])
    result_stem = [] # отсчеты сигнала
    result_plot_v = [0]
    result_plot_t = [0]
    plot_limit_hit = False 
    count = 0
    # генерируем отсчеты сигнала и заполняем
    for task in task_gen:
        count += 1
        if count > plot_limits[plot_type]:
            plot_limit_hit = True
        if not plot_limit_hit:  # Stop appending to the plot list if the limit is hit
            vol = task[0]['vol']
            t = int(task[0]['pulse_width'] * 1e6)  # us
            sign = task[0]['sign']
            if sign:
                vol = -vol
            if plot_type == 'stem':
                if t > 0:
                    result_stem.append(vol)
                result_stem.append(READ_VOLTAGE)
            else:
                # Plot signal
                # Blank point
                result_plot_t.append(result_plot_t[-1] + BLANK_TIME)
                result_plot_v.append(0)
                # Voltage rise
                result_plot_t.append(result_plot_t[-1])
                result_plot_v.append(vol)
                # Voltage pulse
                result_plot_t.append(result_plot_t[-1] + t)
                result_plot_v.append(vol)
                # Voltage descend
                result_plot_t.append(result_plot_t[-1])
                result_plot_v.append(0)
                # Blank point
                result_plot_t.append(result_plot_t[-1] + BLANK_TIME)
                result_plot_v.append(0)
                # Read voltage rise
                result_plot_t.append(result_plot_t[-1])
                result_plot_v.append(READ_VOLTAGE)
                # Read voltage pulse
                result_plot_t.append(result_plot_t[-1] + READ_TIME)
                result_plot_v.append(READ_VOLTAGE)
                # Read voltage descend
                result_plot_t.append(result_plot_t[-1])
                result_plot_v.append(0)
    if plot_type == 'plot':  # Adding blank point
        result_plot_t.append(result_plot_t[-1] + BLANK_TIME)
        result_plot_v.append(0)
    if plot_type == 'stem':
        ax.stem(result_stem, basefmt='')
        ax.set_xlabel(lang_pack.get("plot_pulse_count"))
    else:
        ax.plot(result_plot_t, result_plot_v)
        ax.set_xlabel(lang_pack.get("plot_time"))
    ax.set_ylabel(lang_pack.get("plot_voltage"))
    ax.grid(ls='--', color='grey')
    return count, plot_limit_hit


class VisaPlotter:
    """Plotting routine for visa modes"""
    def __init__(self, manager, ticket, plot_type: str, ax: Axes, plot_limits: dict, lang_pack: dict):
        """Plotting routine for visa modes"""
        self.manager = manager
        self.ticket = ticket
        self.plot_type = plot_type
        self.ax = ax
        self.plot_limits = plot_limits
        self.lang_pack = lang_pack
        
        
    def plot(self) -> tuple[int, bool]:
        """Plot the graph for visa menu"""
        # Axis values
        self.ax.grid(ls='--', color='grey')
        if self.ticket['mode'] in ['smu_cc-cv', 'smu_cv-cc', 'smu_iv_current']:  # Plotting both voltage and current
            self.cur_list = []
            self.ax.set_ylabel(self.lang_pack.get('plot_voltage'), color='tab:blue')
            self.ax.tick_params(axis='y', labelcolor='tab:blue')
            self.ax2 = self.ax.twinx()
            self.ax2.set_ylabel(self.lang_pack.get('plot_current'), color='tab:red')
            self.ax2.tick_params(axis='y', labelcolor='tab:red')
        else:  # Plotting voltage only
            self.cur_list = None
            self.ax.set_ylabel(self.lang_pack.get('plot_voltage'))
        self.vol_list = []
        if self.plot_type == 'plot':
            self.vol_time_list = []
            self.cur_time_list = []
        self.plot_mode = None  # Plot mode variable, changes on config task
        self.plot_val = None  # Value currently plotting: vol or cur
        self.time = 0  # Current time value for iteration
        self.vlines = []  # Vertical line positions (configurations)
        blank_time = 500e-6  # 500 us
        self.plot_limit_hit = False 
        self.sense_counter = 0
        count = 0
        
        # Generating arrays
        task_gen = self.manager.menu[self.ticket['mode']](self.ticket['params'], self.ticket['terminate'], self.manager.blank_type)
        for task, _ in task_gen:  # Task is dict
            count += 1
            if count > self.plot_limits[self.plot_type]:
                self.plot_limit_hit = True
            if not self.plot_limit_hit:  # Stop appending to the plot list if the limit is hit
                # Config task
                if task['mode_flag'].startswith('config'):
                    if self.plot_mode is not None:  # Adding configuration vertical line
                        if self.plot_type == 'stem':
                            self.vlines.append(len(self.vol_list))
                        else:
                            self.time += blank_time
                            self.vlines.append(self.time*1e6)  # us
                            self.time += blank_time
                    if task['mode_flag'] in ['config_iv_dc', 'config_iv_current_dc']:
                        self.plot_mode = 'dc_sweep'
                        self.time_interval = task['time_interval']
                        self.sense_counter = task['n_points'] * 2 if task['double'] else task['n_points']
                        if task['mode_flag'] == 'config_iv_dc':
                            self.plot_val = 'vol'
                            if self.plot_type == 'plot':
                                self.vol_list.append(0)
                                self.vol_time_list.append(self.time)
                        elif task['mode_flag'] == 'config_iv_current_dc':
                            self.plot_val = 'cur'
                            if self.plot_type == 'plot':
                                self.cur_list.append(0)
                                self.cur_time_list.append(self.time)
                    elif task['mode_flag'] in ['config_pulsed_retention', 'config_pot_dep']:
                        self.plot_mode = 'pulse'
                        self.pulse_width = task['pulse_width']
                        self.time_interval = task['pulse_period'] - task['pulse_width']
                        self.sense_counter = task['count']
                        self.plot_val = 'vol'
                        if self.plot_type == 'plot':
                            self.vol_list.append(0)
                            self.vol_time_list.append(self.time)
                    elif task['mode_flag'] == 'config_std':
                        self.plot_mode = 'pulse+read'
                        self.pulse_width = task['pulse_width']
                        self.time_interval = blank_time
                        self.read_voltage = -task['read_voltage'] if task['read_direction'] else task['read_voltage']
                        self.sense_counter = len(task['volt_array'])
                        self.plot_val = 'vol'
                        if self.plot_type == 'plot':
                            self.vol_list.append(0)
                            self.vol_time_list.append(self.time)
                    elif task['mode_flag'] == 'config_endurance':
                        self.plot_mode = 'pulse+read'
                        self.pulse_width = task['pulse_width']
                        self.time_interval = task['pulse_period'] - task['pulse_width']
                        self.read_voltage = -task['read_voltage'] if task['read_direction'] else task['read_voltage']
                        self.sense_counter = task['count'] * 2
                        self.plot_val = 'vol'
                        if self.plot_type == 'plot':
                            self.vol_list.append(0)
                            self.vol_time_list.append(self.time)
                    continue
                
                elif task['mode_flag'] == 'sense':
                    self.sense_counter -= 1
                    # Plotting for different modes
                    if self.plot_mode == 'dc_sweep':
                        self.add_dc_point(task)
                    elif self.plot_mode == 'pulse':
                        self.add_pulse_point(task, read=False)
                    elif self.plot_mode == 'pulse+read':
                        self.add_pulse_point(task, read=True)
        
        # Plotting           
        if self.plot_type == 'stem':
            self.ax.stem(self.vol_list, linefmt='tab:blue', basefmt='')
            if self.cur_list is not None:
                self.ax2.stem(np.array(self.cur_list) * 1000, linefmt='tab:red', basefmt='')  # mA
            self.ax.set_xlabel(self.lang_pack.get("plot_pulse_count"))
        else:
            self.ax.plot(np.array(self.vol_time_list)*1e6, self.vol_list, color='tab:blue')
            if self.cur_list is not None:
                self.ax2.plot(np.array(self.cur_time_list)*1e6, np.array(self.cur_list)*1e3, color='tab:red')  # mA
            self.ax.set_xlabel(self.lang_pack.get("plot_time"))
        
        # Align axes
        if self.cur_list is not None:
            lim1 = max(abs(x) for x in self.ax.get_ylim())
            lim2 = max(abs(x) for x in self.ax2.get_ylim())
            self.ax.set_ylim(-lim1, lim1)
            self.ax2.set_ylim(-lim2, lim2)
            
        # Vertical lines
        for x in self.vlines:
            self.ax.axvline(x, color='k', ls='--')  # us
        if len(self.vlines) > 0:
            # Placing configuration text
            if self.plot_type == 'plot':
                x = self.vlines[0] + blank_time * 1e6 / 5
            else:
                x = self.vlines[0] + 1
            self.ax.text(x=x, y=0.01, s=self.lang_pack.get("instrument_config"), 
                         transform=self.ax.get_xaxis_transform(), rotation=90)
            
        return count, self.plot_limit_hit
    
    
    def add_dc_point(self, task: dict) -> None:
        """Add a point for dc mode"""
        if self.plot_val == 'vol':  # Plotting voltage
            if self.plot_type == 'stem':
                self.vol_list.append(sign_vol(task))
                if self.cur_list is not None:
                    self.cur_list.append(np.nan)
            else:
                # Rise
                self.vol_list.append(sign_vol(task))
                self.vol_time_list.append(self.time)
                # Flat
                self.vol_list.append(sign_vol(task))
                self.time += self.time_interval
                self.vol_time_list.append(self.time)
                # Add 0 on last sense
                if self.sense_counter == 0:
                    self.vol_list.append(0)
                    self.vol_time_list.append(self.time)
        elif self.plot_val == 'cur':
            if self.plot_type == 'stem':
                self.cur_list.append(sign_vol(task))
                self.vol_list.append(np.nan)
            else:
                # Rise
                self.cur_list.append(sign_vol(task))
                self.cur_time_list.append(self.time)
                # Flat
                self.cur_list.append(sign_vol(task))
                self.time += self.time_interval
                self.cur_time_list.append(self.time)
                # Add 0 on last sense
                if self.sense_counter == 0:
                    self.cur_list.append(0)
                    self.cur_time_list.append(self.time)
                    
                    
    def add_pulse_point(self, task: dict, read: bool = False) -> None:
        """Add a point for pulse mode (no read pulse)"""
        if self.plot_type == 'stem':
            # Voltage pulse
            self.vol_list.append(sign_vol(task))
            if self.cur_list is not None:
                self.cur_list.append(np.nan)
            # Read pulse
            if read:
                self.vol_list.append(self.read_voltage)
                if self.cur_list is not None:
                    self.cur_list.append(np.nan)
        else:
            # Rise
            self.vol_list.append(sign_vol(task))
            self.vol_time_list.append(self.time)
            # Pulse
            self.vol_list.append(sign_vol(task))
            self.time += self.pulse_width
            self.vol_time_list.append(self.time)
            # Descend
            self.vol_list.append(0)
            self.vol_time_list.append(self.time)
            # Read pulse
            if read:
                # Pulse interval
                self.vol_list.append(0)
                self.time += self.time_interval
                self.vol_time_list.append(self.time)     
                # Rise
                self.vol_list.append(self.read_voltage)
                self.vol_time_list.append(self.time)
                # Pulse
                self.vol_list.append(self.read_voltage)
                self.time += self.pulse_width
                self.vol_time_list.append(self.time)
                # Descend
                self.vol_list.append(0)
                self.vol_time_list.append(self.time)
            # Pulse interval
            if self.sense_counter != 0:
                self.vol_list.append(0)
                self.time += self.time_interval
                self.vol_time_list.append(self.time)            
        
        
def sign_vol(task: dict) -> float:
    """Add sign to voltage"""
    if task['sign']:
        return -task['vol']
    return task['vol']