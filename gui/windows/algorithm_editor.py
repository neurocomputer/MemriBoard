"""Algorithm editor"""
import os
import inspect

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QPlainTextEdit
from PyQt5.QtGui import QFontDatabase, QFontMetricsF, QTextCursor

from manager.algorithms import PythonHighlighter, Algorithm
from manager.algorithms.algorithm import VALUE_FUNCTIONS, GENERATOR_FUNCTIONS, MULTI_GENERATOR_FUNCTIONS


# TODO remove
user_alg = """def algorithm():
    measure_resistance()
    print('LAST_RES:', last_resistance())
    if last_resistance() > 10000:
        send_experiment('Experiment_SET')
    else:
        send_experiment('Experiment_RESET')
"""


class AlgorithmEditor(QDialog):
    """Algorithm editor"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.ui = uic.loadUi(os.path.join(os.getcwd(), 'gui', 'uies', 'algorithm_editor.ui'), self)
        # Setting widgets
        self.setup_code_editor()
        self.setup_function_lists()
        
        
    def setup_code_editor(self) -> None:
        """Set the code editor parameters"""
        self.code_editor: QPlainTextEdit
        # Font
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.code_editor.setFont(font)
        # Highlighting
        highlight = PythonHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(lambda: highlight.highlightBlock(None))
        # Tabulation
        space_width = QFontMetricsF(self.code_editor.font()).horizontalAdvance(' ')
        self.code_editor.setTabStopDistance(space_width * 4)  # 4 spaces
        # Displaying algorithm
        self.code_editor.setPlainText(user_alg)
        self.code_editor.setFocus()
        self.code_editor.moveCursor(QTextCursor.End)
        
    
    def setup_function_lists(self) -> None:
        """Set up bult-in function lists"""
        alg = Algorithm()
        utility_list = []
        exp_list = []
        for name, method in inspect.getmembers(alg, inspect.ismethod):
            if name in VALUE_FUNCTIONS:
                sig = inspect.signature(method)
                utility_list.append(name + str(sig))
            if name in GENERATOR_FUNCTIONS or name in MULTI_GENERATOR_FUNCTIONS:
                sig = inspect.signature(method)
                exp_list.append(name + str(sig))
        self.listWidget_utility_funcs.addItems(utility_list)
        self.listWidget_exp_funcs.addItems(exp_list)
        
        
    def closeEvent(self, event):
        event.accept()
        self.parent.close()
        
        
# TODO: custom QPlainEditText for tabulation
        
# TODO: dark theme?
# palette = self.code_editor.palette()
# palette.setColor(QPalette.ColorRole.Base, QColor('#282c34'))
# palette.setColor(QPalette.ColorRole.Text, QColor('#ffffff'))
# self.code_editor.setPalette(palette)
        