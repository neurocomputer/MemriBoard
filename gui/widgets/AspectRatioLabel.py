"""Label that keeps the aspect ratio"""
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap



class AspectRatioLabel(QLabel):
    """Label with image that keeps the aspect ratio"""
    def __init__(self, parent=None):
        """Label with image that keeps the aspect ratio"""
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        
    def _scale_pixmap(self):
        """Scale the pixmap"""
        return self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        
    def setPixmap(self, pixmap: QPixmap):
        """Set the pixmap"""
        self._pixmap = pixmap
        return super().setPixmap(self._scale_pixmap())
        
        
    def resizeEvent(self, event):
        super().setPixmap(self._scale_pixmap())
        super().resizeEvent(event)