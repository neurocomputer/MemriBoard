"""
Вспомогательные функции для рисования
plot_for_signal_graph - рисование графика на окне Сигнал
"""
from matplotlib.axes import Axes
from manager.algorithms import execute_algorithm

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


def plot_for_signal_graph(manager, ticket: dict, plot_type: str, ax: Axes, plot_limits: dict) -> tuple[int, bool]:
    """Plot the graph on the Signal window and return task count"""
    if manager.driver_attr['modes'] == 'standard':
        return plot_standard(manager, ticket, plot_type, ax, plot_limits)
    elif manager.driver_attr['modes'] == 'vis':
        return plot_visa(manager, ticket, plot_type, ax, plot_limits)
    else:
        ax.text(0.1, 0.1, 'Unknown driver mode :(')
        return 0, False


def plot_standard(manager, ticket, plot_type: str, ax: Axes, plot_limits: dict):
    """Plot for standard menu"""
    ax.clear()
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
        ax.stem(result_stem)
    else:
        ax.plot(result_plot_t, result_plot_v)
    ax.grid(ls='--', color='grey')
    return count, plot_limit_hit


def plot_visa(manager, ticket, plot_type: str, ax: Axes, plot_limits: dict):
    """Plot for visa menu"""
    # получаем генератор задач
    task_gen = manager.menu[ticket['mode']](ticket['params'], ticket['terminate'], manager.blank_type)
    for task in task_gen:  # TODO remove, reimplement
        print(task) 