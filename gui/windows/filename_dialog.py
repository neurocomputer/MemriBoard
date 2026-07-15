"""
Filename dialog for choosing new file names or replacing existing files.
"""
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal



class FileNameDialog(QDialog):
    """Filename dialog for choosing new file names or replacing existing files"""
    
    signal = pyqtSignal(tuple)
    
    def __init__(self, initial_filename: str, lang_pack: dict, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.lang_pack = lang_pack
        self.initial_filename = initial_filename
        self.ui = uic.loadUi(os.path.join(os.getcwd(), 'gui', 'uies', 'filename_dialog.ui'), self)
        self.setModal(True)
        self.change_language()
        self.edit.setText(initial_filename)
        # Buttons
        self.btn_save.clicked.connect(self.on_save_btn)
        self.btn_skip.clicked.connect(self.on_skip_btn)
        
    
    def change_language(self):
        """Change interface language"""
        self.setWindowTitle(self.lang_pack.get('window_title'))
        self.label.setText(self.lang_pack.get('label_text_1') + self.initial_filename + self.lang_pack.get('label_text_2'))
        self.label_filename.setText(self.lang_pack.get('filename'))
        self.btn_save.setText(self.lang_pack.get('save'))
        self.btn_skip.setText(self.lang_pack.get('skip'))
        
        
    def on_save_btn(self):
        """Save the file"""
        if self.edit.text() == self.initial_filename:
            self.signal.emit()
        
        
    def on_skip_btn(self):
        """Skip the file"""