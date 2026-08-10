"""
Snapshot window
"""

import numpy as np
from typing import Union
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import (MultipleLocator, MaxNLocator)
from matplotlib.colors import LogNorm
from PyQt5.QtWidgets import (
    QWidget, 
    QFileDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QCheckBox
)
from PyQt5.QtCore import Qt
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
     
    def __init__(self, parent=None, data: Union[list, None] = None, mode: str = 'resistances') -> None:
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
        self.change_language(update_widgets=False)
        self.init_ui()
        self.plot_matrix(mode=mode)
        
        
    def change_language(self, update_widgets: bool = True):
        """
        Change GUI language
        """
        ok, self.lang_pack = self.parent.read_language_json("snapshot")
        if ok:
            self.setWindowTitle(self.lang_pack['window_title'])
            if update_widgets:
                self.export_btn.setText(self.lang_pack.get('export'))
                self.checkbox_log.setText(self.lang_pack.get('log_scale'))
                self.plot_matrix()
        
        
    def init_ui(self) -> None:
        """Place widgets on the window"""
        layout = QVBoxLayout()
        bottom_layout = QHBoxLayout()
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.canvas)
        self.export_btn = QPushButton(self, text=self.lang_pack.get('export'))
        self.export_btn.clicked.connect(self.save_matrix)
        self.checkbox_log = QCheckBox(parent=self, text=self.lang_pack.get('log_scale'))
        self.checkbox_log.stateChanged.connect(self.on_checkbox_state_change)
        bottom_layout.addWidget(self.toolbar)
        bottom_layout.addWidget(self.checkbox_log)
        bottom_layout.addWidget(self.export_btn)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
        
        
    def plot_matrix(self, mode: str = 'resistances', log_scale: bool = True) -> None:
        """Plot matrix on the figure

        Args:
            mode (str, optional): 'resistances' (plotting all resistances),
                'binary' (binary data from rram window) or 'weights' (for plotting weights 
                on the Math window). Defaults to 'resistances'.
            log_scale (bool, optional): If True, the matrix is displayed in logarithmic scale. Defaults to True.
        """
        self.fig.clear()
        ax = self.fig.add_subplot()
        if self.data is None:
            return
        if mode == 'resistances':
            if log_scale:
                image = ax.matshow(np.array(self.data)/1000, interpolation=None, norm=LogNorm())  # kOhm
            else:
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
            self.checkbox_log.setVisible(True)
            cbar.set_label(self.lang_pack['res_kOhm'])
            cbar.ax.yaxis.set_major_locator(MaxNLocator(10, integer=True))
            if log_scale:
                cbar.ax.set_yscale('log')
                self.checkbox_log.setChecked(True)
            else:
                self.checkbox_log.setChecked(False)
        elif mode =='weights':
            self.checkbox_log.setVisible(False)
            cbar.set_label(self.lang_pack['weight'])
            cbar.ax.yaxis.set_major_locator(MaxNLocator(10, integer=True))
        else:
            self.checkbox_log.setVisible(False)
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
        except ModuleNotFoundError as e:
            show_warning_messagebox(parent=self, message=self.lang_pack['module_not_found'] + str(e))
        except Exception as e:
            show_warning_messagebox(parent=self, message=e)
            
            
    def on_checkbox_state_change(self, state) -> None:
        """Checkbox log_scale is clicked"""
        if state == Qt.Checked:
            self.plot_matrix(mode='resistances', log_scale=True)
        else:
            self.plot_matrix(mode='resistances', log_scale=False)
        
        
    def safe_close(self) -> None:
        """Closing the window"""
        plt.close(self.fig)
        self.parent.snapshot_dialog = None
        self.close()
        
        
    def closeEvent(self, event) -> None:
        self.safe_close()
