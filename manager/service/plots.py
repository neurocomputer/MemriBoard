"""
Вспомогательные функции для рисования
plot_input_signal - отображение графика входного сигнала
plot_input_signal_stem - отображения графика в виде столбцов
"""

from typing import Union
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes._axes import Axes
from manager.service import d2v

# pylint: disable=C0103,W0212

def calculate_counts_for_ticket(parent, ticket: dict):
    """
    Посчитать количество задач для тикета
    """
    # получаем генератор задач
    task = parent.menu[ticket['mode']], (ticket['params'],
                                        ticket['terminate'],
                                        parent.blank_type)
    count = 0
    task_list = []
    for tsk in task[0](*task[1]):
        count += 1
        task_list.append(tsk)

    return task_list, count

def plot_input_signal(parent,
                      ticket: dict,
                      plt_flag: bool = False,
                      shadow: bool = False,
                      figure: Figure = None) -> Union[int, Axes]:
    """
    Функция отображения графика входного сигнала
    Примеры использования:
    from manager.service.plots import plot_input_signal
    import matplotlib.pyplot as plt
    * рисунок генерируется внутри функции
    count = plot_input_signal(ticket, plt_flag=True)
    * рисунок передается в функцию извне
    figure = plt.figure()
    ax, count = plot_input_signal(ticket,
                                plt_flag=True,
                                shadow=True,
                                figure=figure)
    plt.show()

    Arguments:
        ticket -- тикет задачи
        plt_flag -- флаг создания графика (только создает) (default=True)
        shadow -- флаг отображения графика (отображать график) (default=False)
        figure -- график matplotlib (default=None)

    Returns:
        ax -- оси с графиком
        count -- счетчик задач
    """

    # получаем генератор задач
    task = parent.menu[ticket['mode']], (ticket['params'],
                                        ticket['terminate'],
                                        parent.blank_type)

    READ_VOLTAGE = parent.vol_read
    READ_TIME = int(parent.ap_config['board']['read_time'])
    BLANK_TIME = int(parent.ap_config['board']['blank_time'])
    result = [] # отсчеты сигнала
    count = 0
    # генерируем отсчеты сигнала и заполняем
    for tsk in task[0](*task[1]):
        count += 1
        vol = d2v(parent.dac_bit, parent.vol_ref_dac, tsk[0]['vol'])
        t = tsk[0]['t_ms'] * 1000 + tsk[0]['t_us']
        sign = tsk[0]['sign']
        if sign:
            vol = -vol
        for _ in range(BLANK_TIME):
            result.append(0)
        for _ in range(t):
            result.append(vol)
        for _ in range(BLANK_TIME):
            result.append(0)
        for _ in range(READ_TIME):
            result.append(READ_VOLTAGE)
    for _ in range(BLANK_TIME):
        result.append(0)
    # строим график
    if plt_flag:
        if figure is None:
            figure = plt.figure()
        else:
            figure.clear()
        ax = figure.add_subplot(111)
        ax.plot(result)
        ax.set_ylabel('Напряжение, В')
        ax.set_xlabel('Время, мкс')
        ax.grid(True, linestyle='--')
        if not shadow:
            plt.show()
        else:
            return ax, count
    return count

def plot_input_signal_stem(parent,
                           ticket: dict,
                           plt_flag: bool = False,
                           shadow: bool = False,
                           figure: Figure = None) -> Union[int, Axes]:
    """
    Функция отображения графика входного сигнала в виде столбцов stem

    Arguments:
        ticket -- тикет задачи
        plt_flag -- флаг создания графика (только создает) (default=True)
        shadow -- флаг отображения графика (отображать график) (default=False)
        figure -- график matplotlib (default=None)

    Returns:
        ax -- оси с графиком
        count -- счетчик задач
    """
    # получаем генератор задач
    task = parent.menu[ticket['mode']], (ticket['params'],
                                        ticket['terminate'],
                                        parent.blank_type)

    READ_VOLTAGE = parent.vol_read
    result = [] # отсчеты сигнала
    count = 0
    # генерируем отсчеты сигнала и заполняем
    for tsk in task[0](*task[1]):
        count += 1
        vol = d2v(parent.dac_bit, parent.vol_ref_dac, tsk[0]['vol'])
        t = tsk[0]['t_ms'] * 1000 + tsk[0]['t_us']
        sign = tsk[0]['sign']
        if sign:
            vol = -vol
        result.append(vol)
        result.append(READ_VOLTAGE)
    # строим график
    if plt_flag:
        if figure is None:
            figure = plt.figure()
        else:
            figure.clear()
        ax = figure.add_subplot(111)
        if result:
            ax.stem(result)
        else:
            ax.plot(result)
        ax.set_ylabel('Напряжение, В')
        ax.set_xlabel('Импульс')
        ax.grid(True, linestyle='--')
        if not shadow:
            plt.show()
        else:
            return ax, count
    return count

def plot_with_save(parent,
                   ticket: dict,
                   mode: str,
                   save_path: str = "") -> int:
    plt.clf()
    # получаем генератор задач
    task = parent.menu[ticket['mode']], (ticket['params'],
                                        ticket['terminate'],
                                        parent.blank_type)

    READ_VOLTAGE = parent.vol_read
    READ_TIME = int(parent.ap_config['board']['read_time'])
    BLANK_TIME = int(parent.ap_config['board']['blank_time'])
    result_stem = [] # отсчеты сигнала
    result_plot = []
    count = 0
    # генерируем отсчеты сигнала и заполняем
    for tsk in task[0](*task[1]):
        count += 1
        vol = d2v(parent.dac_bit, parent.vol_ref_dac, tsk[0]['vol'])
        t = tsk[0]['t_ms'] * 1000 + tsk[0]['t_us']
        sign = tsk[0]['sign']
        if sign:
            vol = -vol
        if mode == 'stem':
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
    if mode == 'plot':
        for _ in range(BLANK_TIME):
            result_plot.append(0)
    if mode == 'stem':
        if result_stem:
            plt.stem(result_stem)
            plt.xlabel('Импульс')
        else:
            plt.plot(result_stem)
            plt.xlabel('Время, мкс')
    else:
        plt.plot(result_plot)
        plt.xlabel('Время, мкс')
    plt.ylabel('Напряжение, В')
    plt.grid(True, linestyle='--')
    plt.tight_layout()
    if save_path:
        plt.savefig(fname=save_path, dpi=100)
    return count
