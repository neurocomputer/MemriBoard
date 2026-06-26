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
from PyQt5.QtWidgets import QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton
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
    lang_pack: dict
     
    def __init__(self, parent=None, data: list = None, mode: str = 'resistances') -> None:
        """Snapshot window

        Args:
            parent (optional): Parent class. Defaults to None.
            data (list, optional): Data to plot (2D list). If data is None, 
                doesn't plot anything. Defaults to None.
            mode (str, optional): Snapshot mode: 'resistances' (plotting all resistances),
                'binary' (binary data from rram window) or 'weights' (for plotting weights 
                on the Math window). Defaults to 'resistances'.
        """
        super().__init__()
        self.parent = parent
        self.data = data
        
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.change_language()
        self.plot_matrix(mode=mode)
        self.init_ui()
        
        
    def change_language(self):
        """
        Change GUI language
        """
        ok, self.lang_pack = self.parent.read_language_json("snapshot")
        if ok:
            if hasattr(self, 'toolbar'):
                self.export_btn.setText(self.lang_pack.get('export'))
            self.setWindowTitle(self.lang_pack['window_title'])
            self.plot_matrix()
        
        
    def init_ui(self) -> None:
        """Place widgets on the window"""
        layout = QVBoxLayout()
        bottom_layout = QHBoxLayout()
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.canvas)
        self.export_btn = QPushButton(self, text=self.lang_pack.get('export'))
        self.export_btn.clicked.connect(self.save_matrix)
        bottom_layout.addWidget(self.toolbar)
        bottom_layout.addWidget(self.export_btn)
        layout.addLayout(bottom_layout)
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
            cbar.set_label(self.lang_pack['res_kOhm'])
            cbar.ax.yaxis.set_major_locator(MaxNLocator(10, integer=True))
        elif mode =='weights':
            cbar.set_label(self.lang_pack['weight'])
            cbar.ax.yaxis.set_major_locator(MaxNLocator(10, integer=True))
        else:
            cbar.ax.yaxis.set_major_locator(MaxNLocator(2, integer=True))
        self.canvas.draw_idle()
        
        
    def save_matrix(self) -> None:
        """Handles pressing export button"""
        save_funcs = {
            f'{self.lang_pack["txt"]} (*.txt)': save_matrix_txt,
            f'{self.lang_pack["csv"]} (*.csv)': save_matrix_csv,
            f'{self.lang_pack["xls"]} (*.xls)': save_matrix_xlsx,
            f'{self.lang_pack["xls"]} (*.xlsx)': save_matrix_xlsx,
            f'{self.lang_pack["json"]} (*.json)': save_matrix_json
        }
        filename, extension = QFileDialog.getSaveFileName(self, 
            filter=';;'.join(save_funcs))
        if filename == '':
            return
        if extension not in save_funcs:
            show_warning_messagebox(parent=self, message=self.lang_pack['ext_not_supported'])
            return
        try:
            ext = extension.split('*')[1].split(')')[0]
            if not filename.endswith(ext):
                filename += ext
            save_funcs[extension](filename, self.data)
        except PermissionError:
            show_warning_messagebox(parent=self, message=self.lang_pack['file_busy'])
        except Exception as e:
            show_warning_messagebox(parent=self, message=e)
        
        
    def safe_close(self) -> None:
        """Closing the window"""
        plt.close(self.fig)
        self.parent.snapshot_dialog = None
        self.close()
        
        
    def closeEvent(self, event) -> None:
        self.safe_close()
