"""Slideshow with images"""
import os
from typing import Union

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import QSize

from manager.service.global_settings import ICON_PATH
from gui.themes import color_icon



class SlideShow(QWidget):
    """SlideShow Widget"""
    def __init__(self, parent=None, slide_str: str = 'Slide:', folder_path: Union[str, None] = None):
        """SlideShow Widget"""
        super().__init__(parent)
        self.parent = parent
        self.setFolder(folder_path)
        # Init UI
        gui_path = os.path.join(os.getcwd(), 'gui', 'uies', 'slide_show.ui')
        self.ui = uic.loadUi(gui_path, self)
        self.set_icons()
        # Widget linting
        self.btn_next: QPushButton
        self.btn_prev: QPushButton
        self.btn_pause: QPushButton
        self.comboBox_slide: QComboBox
        self.label_slide: QLabel
        self.label_img: QLabel
        
        
    def set_icons(self):
        """
        Set icons used in the GUI
        """
        icon_size = QSize(16, 16)
        icon_prev = color_icon(
            svg_path=os.path.join(ICON_PATH, 'arrow-left-line.svg'), 
            theme=self.parent.parent.theme, 
            size=icon_size
        )
        icon_next = color_icon(
            svg_path=os.path.join(ICON_PATH, 'arrow-right-line.svg'), 
            theme=self.parent.parent.theme, 
            size=icon_size
        )
        self.icon_start = color_icon(
            svg_path=os.path.join(ICON_PATH, 'play-line.svg'), 
            theme=self.parent.parent.theme, 
            size=icon_size
        )
        self.icon_pause = color_icon(
            svg_path=os.path.join(ICON_PATH, 'pause-line.svg'), 
            theme=self.parent.parent.theme, 
            size=icon_size
        )
        self.btn_prev.setIcon(icon_prev)
        self.btn_next.setIcon(icon_next)
        self.btn_pause.setIcon(self.icon_pause)
        for button in [self.btn_prev, self.btn_next, self.btn_pause]:
            button.setIconSize(icon_size)
        
        
    def setFolder(self, folder_path: str) -> None:
        """Set folder where images are contained"""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f'No directory {folder_path}')
    