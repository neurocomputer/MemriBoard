"""
Интерфейс с кроссбаром
"""

# pylint: disable=E0611,I1101,W0611

import sys
import PyQt5
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore

from gui.windows.crossbar import Window
from doom_api import doom_drawer

def main() -> None:
    """
    Отображение главного окна
    """
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Window()
    doom_drawer(window)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
