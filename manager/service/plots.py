"""
Вспомогательные функции для рисования
plot_for_signal_graph - рисование графика на окне Сигнал
"""
from matplotlib.axes import Axes
from manager.algorithms import execute_algorithm

# pylint: disable=C0103,W0212
# TODO dark theme for plots?


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
    ax.clear()
    # получаем генератор задач
    task_gen = manager.menu[ticket['mode']](ticket['params'], ticket['terminate'], manager.blank_type)
    READ_VOLTAGE = manager.vol_read
    READ_TIME = int(manager.ap_config['board']['read_time'])
    BLANK_TIME = int(manager.ap_config['board']['blank_time'])
    result_stem = [] # отсчеты сигнала
    result_plot = []
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
                for _ in range(BLANK_TIME):
                    result_plot.append(0)
                for _ in range(t):
                    result_plot.append(vol)
                for _ in range(BLANK_TIME):
                    result_plot.append(0)
                for _ in range(READ_TIME):
                    result_plot.append(READ_VOLTAGE)
    if plot_type == 'plot':
        for _ in range(BLANK_TIME):
            result_plot.append(0)
    if plot_type == 'stem':
        ax.stem(result_stem)
    else:
        ax.plot(result_plot)
    ax.grid(ls='--', color='grey')
    return count, plot_limit_hit
