"""
Snapshot window
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import (MultipleLocator, MaxNLocator)
from PyQt5.QtWidgets import QWidget, QFileDialog, QVBoxLayout, QPushButton
from gui.src import (
    save_matrix_csv, 
    save_matrix_txt, 
    save_matrix_json, 
    save_matrix_xlsx, 
    show_warning_messagebox
)


class Snapshot(QWidget):
    """
    Snapshot window
    """
    
    data: list  # Массив сопротивлений
    fig: Figure
     
    def __init__(self, parent=None, data=None, mode='resistances') -> None:
        super().__init__()
        self.parent = parent
        self.data = data
        self.setWindowTitle('Снапшот')
        
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.plot_matrix(mode=mode)
        self.init_ui()
        
        
    def init_ui(self) -> None:
        """Place widgets on the window"""
        layout = QVBoxLayout()
        toolbar = CustomToolbar(self.canvas, self)
        layout.addWidget(self.canvas)
        layout.addWidget(toolbar)
        self.setLayout(layout)
        
        
    def plot_matrix(self, mode: str = 'resistances') -> None:
        """Plot matrix on the figure

        Args:
            mode (str, optional): 'resistances' (plotting all resistances),
                'binary' (binary data from rram window) or 'weights' (for plotting weights 
                on the Math window). Defaults to 'resistances'.
        """
        self.fig.clear()
        ax = self.fig.add_subplot()
        if self.data is None:
            return
        if mode == 'resistances':
            image = ax.matshow(np.array(self.data)/1000, interpolation=None)  # kOhm
        else:
            image = ax.matshow(self.data, interpolation=None)
        # Ticks
        ax.xaxis.set_major_locator(MaxNLocator(16, integer=True))
        ax.yaxis.set_major_locator(MaxNLocator(16, integer=True))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(which='both', top=True, bottom=False, left=True, right=False)
        # Colorbar
        n_rows, n_cols = len(self.data), len(self.data[0])
        cbar_ax = ax.inset_axes([n_cols+2, n_rows/6, max(n_cols//32, 1), n_rows*2/3], transform=ax.transData)
        cbar = self.fig.colorbar(image, cax=cbar_ax, orientation='vertical', shrink=0.4)
        if mode == 'resistances':
            cbar.set_label('Сопротивление, кОм')
            cbar.ax.yaxis.set_major_locator(MaxNLocator(10, integer=True))
        elif mode =='weights':
            cbar.set_label('Вес')
            cbar.ax.yaxis.set_major_locator(MaxNLocator(10, integer=True))
        else:
            cbar.ax.yaxis.set_major_locator(MaxNLocator(2, integer=True))
        self.canvas.draw_idle()
        
        
    def save_matrix(self) -> None:
        """Handles pressing export button"""
        save_funcs = {
            'Текстовый файл (*.txt)': save_matrix_txt,
            'Файл CSV (*.csv)': save_matrix_csv,
            'Таблица Excel (*.xls)': save_matrix_xlsx,
            'Таблица Excel (*.xlsx)': save_matrix_xlsx,
            'Файл JSON (*.json)': save_matrix_json
        }
        filename, extention = QFileDialog.getSaveFileName(self, 
            filter=';;'.join(save_funcs))
        if filename == '':
            return
        if extention not in save_funcs:
            show_warning_messagebox('Данный формат не поддерживается.')
            return
        try:
            save_funcs[extention](filename, self.data)
        except PermissionError:
            show_warning_messagebox('Файл занят другой программой.')
        except Exception as e:
            show_warning_messagebox(e)
        
        
    def closeEvent(self, event) -> None:
        """Closing the window"""
        plt.close(self.fig)
        self.parent.snapshot_dialog = None
        
        
    
class CustomToolbar(NavigationToolbar):
    """
    Custom Navigation Toolbar for matplotlib
    """    
    def __init__(self, canvas, parent=None) -> None:
        super(CustomToolbar, self).__init__(canvas, parent)
        
        self.export_btn = QPushButton(self, text='Экспорт данных')
        self.export_btn.setGeometry(290, 5, 150, 30)  # TODO: set geometry not by pixels
        self.export_btn.clicked.connect(parent.save_matrix)        