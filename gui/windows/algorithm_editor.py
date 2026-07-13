"""Algorithm editor"""
import os

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog



class AlgorithmEditor(QDialog):
    """Algorithm editor"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.ui = uic.loadUi(os.path.join(os.getcwd(), 'gui', 'uies', 'algorithm_editor.ui'), self)
        
        
    def closeEvent(self, event):
        event.accept()
        self.parent.close()