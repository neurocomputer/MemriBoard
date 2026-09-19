"""Slideshow with images"""
import os
from typing import Union

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QPixmap

from manager.service.global_settings import ICON_PATH
from gui.themes import color_icon
from gui.widgets.AspectRatioLabel import AspectRatioLabel



class SlideShow(QWidget):
    """SlideShow Widget"""
    
    current_slide: int = 0
    timer_enabled: bool = True  # Automatic slide changing
    
    def __init__(self, 
        parent=None, 
        slide_str: str = 'Slide:', 
        folder_path: Union[str, None] = None, 
        time_msec: int = 5000,
        timer_enabled: bool = True
    ) -> None:
        """SlideShow Widget"""
        super().__init__(parent)
        self.parent = parent
        # Init UI
        gui_path = os.path.join(os.getcwd(), 'gui', 'uies', 'slide_show.ui')
        self.ui = uic.loadUi(gui_path, self)
        self.set_icons(timer_enabled)
        self.label_slide.setText(slide_str) 
        # Widget linting
        self.btn_next: QPushButton
        self.btn_prev: QPushButton
        self.btn_pause: QPushButton
        self.comboBox_slide: QComboBox
        self.label_slide: QLabel
        self.label_img: AspectRatioLabel
        # Default slide show settings
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_slide)
        self.set_folder(folder_path)
        self.enable_timer(timer_enabled, time_msec)
        # Binding
        self.btn_pause.clicked.connect(self.handle_pause_btn)
        self.btn_next.clicked.connect(self.next_slide)
        self.btn_prev.clicked.connect(self.previous_slide)
        self.comboBox_slide.currentIndexChanged.connect(self.handle_combobox_change)
        
        
    def set_icons(self, timer_enabled: bool):
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
        if timer_enabled:
            self.btn_pause.setIcon(self.icon_pause)
        else:
            self.btn_pause.setIcon(self.icon_start)
        for button in [self.btn_prev, self.btn_next, self.btn_pause]:
            button.setIconSize(icon_size)
        
        
    def set_folder(self, folder_path: Union[str, None]) -> None:
        """Set folder where images are contained"""
        if folder_path is None:
            self.slide_paths = []
            self.current_slide = 0
            return
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f'No directory {folder_path}')
        self.slide_paths = []
        for slide in sorted(os.listdir(folder_path)):
            if slide.lower().endswith(('.png', 'jpg')):
                self.slide_paths.append(os.path.join(folder_path, slide))
        if len(self.slide_paths) == 0:
            raise FileNotFoundError(f'No .png or .jpg slide file in directory {folder_path}')
        self.current_slide = 0
        self.comboBox_slide.clear()
        self.comboBox_slide.addItems(map(str, range(1, len(self.slide_paths)+1)))
        self.comboBox_slide.setCurrentIndex(self.current_slide)
        self.update_current_image()
        
        
    def update_current_image(self) -> None:
        """Update current slide image"""
        self.pixmap = QPixmap(self.slide_paths[self.current_slide])
        self.label_img.setPixmap(self.pixmap)
        
        
    def next_slide(self) -> None:
        """Go to next slide"""
        if self.current_slide + 1 == len(self.slide_paths):
            self.current_slide = 0
        else:
            self.current_slide += 1
        self.comboBox_slide.setCurrentIndex(self.current_slide)
        self.update_current_image()
        
        
    def previous_slide(self) -> None:
        """Go to previous slide"""
        if self.current_slide == 0:
            self.current_slide = len(self.slide_paths) - 1
        else:
            self.current_slide -= 1
        self.comboBox_slide.setCurrentIndex(self.current_slide)
        self.update_current_image()
        
        
    def handle_pause_btn(self) -> None:
        """Handle pause button: start or stop the timer"""
        self.timer_enabled = not self.timer_enabled
        self.enable_timer(self.timer_enabled, self.time_msec)
        if self.timer_enabled:
            self.btn_pause.setIcon(self.icon_pause)
        else:
            self.btn_pause.setIcon(self.icon_start)
            
            
    def handle_combobox_change(self) -> None:
        """Handle slide change via combobox"""
        self.current_slide = self.comboBox_slide.currentIndex()
        self.update_current_image()
        
        
    def enable_timer(self, enable: bool, time_msec: int = 5000) -> None:
        """Enable or disable automatic slide show"""
        self.timer_enabled = enable
        self.time_msec = time_msec
        if enable:
            self.timer.start(int(time_msec))
        else:
            self.timer.stop()
    