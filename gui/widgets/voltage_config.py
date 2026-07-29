"""Widget which configures the voltage/time on the signal window"""
import os

from PyQt5.QtWidgets import QWidget
from PyQt5 import uic



class VoltageConfig(QWidget):
    """Widget which configures the voltage/time on the signal window"""
    def __init__(self, parent):
        super().__init__(parent)
        # gui_path = os.path.join(os.getcwd(), 'gui', 'uies', 'voltage_config_widget.ui')
        gui_path = os.path.join(os.getcwd(), 'gui', 'uies', 'voltage_config_2.ui')
        self.ui = uic.loadUi(gui_path, self)
