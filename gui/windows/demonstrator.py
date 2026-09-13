"""Demonstrator window"""
import os
import numpy as np
import pyqtgraph as pg
from pyqt_slideshow import SlideShow  # pip install pyqt-slideshow | TODO add to requirements.txt

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QComboBox, QPushButton, QCheckBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont



class DemonstratorWindow(QWidget):
    """Demonstrator window"""

    lang_pack: dict
    
    def __init__(self, parent = None) -> None:
        """Demonstrator"""
        super().__init__()
        self.parent = parent  # Crossbar window
        # Loading ui
        self.ui = uic.loadUi(os.path.join(os.getcwd(), 'gui', 'uies', 'demonstrator.ui'), self)
        # Window settings
        self.setWindowModality(Qt.ApplicationModal)  # Make it modal
        self.setWindowFlags(Qt.Window)
        # Standard variables
        self.slideshow_dir = os.path.join(os.getcwd(), 'gui', 'demonstration', 'slide_show')
        self.plot_data_path = os.path.join(os.getcwd(), 'gui', 'demonstration', '1000_IV.npz')
        self.x_values = ['counts', 'voltage']  # Values available for x axis on the plot
        self.x_units = ['', 'volt']  # Units corresponding to values
        self.y_values = ['resistance', 'current']  # Values available for y axis on the plot
        self.y_units = ['ohm', 'ampere']  # Units corresponding to values
        self.x_value = 'voltage'  # Standard x axis
        self.y_value = 'current'  # Standard y axis
        self.auto_slideshow = True  # Automatically change slides
        self.pause_slideshow_texts = {True: 'pause_slideshow', False: 'cont_slideshow'}
        self.plotting = True  # Plot is running
        self.pause_plot_texts = {True: 'pause', False: 'continue'}
        self.graph_window = int(self.parent.man.ap_config['demonstration']['graph_window'])  # Amount of points on the graph
        self.log_y = False  # Logarithmic scale on Y axis
        # Initializing widgets
        self.change_language()
        self.init_slideshow()
        self.plot_widget = pg.PlotWidget(parent=self.frame_demo)
        self.frame_demo.layout().addWidget(self.plot_widget)
        self.init_plot()
        # Binding
        self.cbox_xaxis.currentIndexChanged.connect(self.change_plot_values)
        self.cbox_yaxis.currentIndexChanged.connect(self.change_plot_values)
        self.checkBox_log.stateChanged.connect(self.change_plot_values)
        self.btn_pause_slideshow.clicked.connect(self.pause_slideshow)
        self.btn_pause.clicked.connect(self.pause_plot)
        # Annotating widget types
        self.frame_slideshow: QFrame  # Left frame with slide
        self.frame_demo: QFrame  # Right frame with demo and static image
        self.plot_widget: pg.PlotWidget  # Widget with IV plot
        self.btn_pause: QPushButton  # Pause button for the graph
        self.cbox_xaxis: QComboBox  # Combobox for X axis unit
        self.cbox_yaxis: QComboBox  # Combobox for Y axis unit
        self.label_xaxis: QLabel  # Label for X axis unit
        self.label_yaxis: QLabel  # Label for Y axis unit
        self.btn_pause_slideshow: QPushButton  # Pause slideshow button
        self.layout_slideshow: QVBoxLayout  # Layout which holds the slide show widget
        self.checkBox_log: QCheckBox
        # Centering splitter
        QTimer.singleShot(0, self.center_splitter)
        
        
    def change_language(self) -> None:
        """Change the language"""
        ok, self.lang_pack = self.parent.read_language_json("demonstrator_window")
        if ok:
            self.setWindowTitle(self.lang_pack.get('title'))
            self.label_xaxis.setText(self.lang_pack.get('x_axis'))
            self.label_yaxis.setText(self.lang_pack.get('y_axis'))
            self.cbox_xaxis.clear()
            self.cbox_xaxis.addItems([self.lang_pack.get(val) for val in self.x_values])
            self.cbox_yaxis.clear()
            self.cbox_yaxis.addItems([self.lang_pack.get(val) for val in self.y_values])
            self.checkBox_log.setText(self.lang_pack.get('logarithmic_scale'))
            self.btn_pause.setText(self.lang_pack.get(self.pause_plot_texts[self.plotting]))
            self.btn_pause_slideshow.setText(self.lang_pack.get(self.pause_slideshow_texts[self.auto_slideshow]))
            # Default combobox values
            self.cbox_xaxis.setCurrentText(self.lang_pack.get(self.x_value))
            self.cbox_yaxis.setCurrentText(self.lang_pack.get(self.y_value))
        
        
    def init_slideshow(self) -> None:
        """Initialize the slideshow"""
        self.slide_list = os.listdir(self.slideshow_dir)
        self.slideshow = SlideShow()
        self.slideshow.setFilenames([os.path.join(self.slideshow_dir, slide) for slide in self.slide_list])
        self.slideshow.setInterval(int(self.parent.man.ap_config['demonstration']['slide_show_time_msec']))
        # Layout
        self.layout_slideshow.addWidget(self.slideshow)
        self.slideshow.show()
        
        
    def pause_slideshow(self) -> None:
        """Pause or unpause slideshow"""
        self.auto_slideshow = not self.auto_slideshow
        self.btn_pause_slideshow.setText(self.lang_pack.get(self.pause_slideshow_texts[self.auto_slideshow]))
        self.slideshow.setTimerEnabled(self.auto_slideshow)
        
        
    def init_plot(self) -> None:
        """Initialize the plot widget"""
        self.plot_widget.clear()
        self.plot_widget.setBackground('w')
        self.plot_widget.getPlotItem().showGrid(x=True, y=True)
        # Plot values
        self.x_data = []
        self.y_data = []
        self.plot_count = 0
        self.change_plot_values()
        # Plotting
        self.plot_line = self.plot_widget.plot(self.x_data, self.y_data, pen=pg.mkPen(width=3, color=(0, 43, 255)))
        self.plot_line.setSymbolBrush(color=(0, 43, 255))
        # Font
        font = QFont()
        font.setPointSize(12)
        for axis_key in ['top', 'bottom', 'left', 'right']:
            ax = self.plot_widget.getAxis(axis_key)
            ax.setTickFont(font)
        # Preparing arrays
        data = np.load(self.plot_data_path)
        self.vol = data['vol']
        self.res = data['res']
        # Timer
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.plot_point)
        if self.plotting:
            self.plot_timer.start(int(self.parent.man.ap_config['demonstration']['graph_time_msec']))
        
        
    def change_plot_values(self) -> None:
        """Change values of the plot"""
        # Getting plot values
        x_index = self.cbox_xaxis.currentIndex()
        self.x_value = self.x_values[x_index]
        y_index = self.cbox_yaxis.currentIndex()
        self.y_value = self.y_values[y_index]
        # Log Y
        self.log_y = self.checkBox_log.isChecked()
        self.plot_widget.setLogMode(y=self.log_y)
        # Changing plot labels
        self.plot_widget.setLabel('bottom', self.lang_pack.get(self.x_value), units=self.lang_pack.get(self.x_units[x_index]), 
                                  **{'color': '#8c8c8c', 'font-size': '14pt'})   
        self.plot_widget.setLabel('left', self.lang_pack.get(self.y_value), units=self.lang_pack.get(self.y_units[y_index]), 
                                  **{'color': '#8c8c8c', 'font-size': '14pt'})  # TODO translate prefixes to Russian
        # X processing
        if self.x_value == 'counts':
            self.x_process = lambda vol, count: count
        elif self.x_value == 'voltage':
            self.x_process = lambda vol, count: vol
        # Y processing
        if self.y_value == 'resistance':
            self.y_process = lambda vol, res: res
        elif self.y_value == 'current':
            if self.log_y:
                self.y_process = lambda vol, res: abs(vol / res)
            else:
                self.y_process = lambda vol, res: vol / res
        # Replot current data
        if self.plot_count > 0:
            start_count = max(0, self.plot_count - self.graph_window + 1)
            self.x_data = []
            self.y_data = []
            for i in range(start_count, self.plot_count + 1):
                self.x_data.append(self.x_process(self.vol[i], i))
                self.y_data.append(self.y_process(self.vol[i], self.res[i]))
        
        
    def plot_point(self) -> None:
        """Plot next point on the graph"""
        if self.plot_count == len(self.res):  # The array has ended
            self.init_plot()
            return
        # Appending to list
        self.x_data.append(self.x_process(self.vol[self.plot_count], self.plot_count))
        self.y_data.append(self.y_process(self.vol[self.plot_count], self.res[self.plot_count]))
        if len(self.x_data) > self.graph_window:  # Removing first element
            del self.x_data[0]
            del self.y_data[0]
        self.plot_line.setData(self.x_data, self.y_data)
        self.plot_count += 1
        
        
    def pause_plot(self) -> None:
        """Pause or start the graph"""
        self.plotting = not self.plotting
        self.btn_pause.setText(self.lang_pack.get(self.pause_plot_texts[self.plotting]))
        if self.plotting:
            self.plot_timer.start(int(self.parent.man.ap_config['demonstration']['graph_time_msec']))
        else:
            self.plot_timer.stop()
        
        
    def center_splitter(self) -> None:
        """
        Center the QSplitter widget
        """
        sizes = self.splitter.sizes()
        s1 = int(sum(sizes) / 2)
        s2 = sum(sizes) - s1
        self.splitter.setSizes([s1, s2])
        
        
    def closeEvent(self, event):
        self.parent.demonstrator_dialog = None
        self.plot_timer.stop()
        self.slideshow.setTimerEnabled(False)
        event.accept()
        