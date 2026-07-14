"""Algorithm editor"""
import os
import inspect

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QPlainTextEdit
from PyQt5.QtGui import QFontDatabase, QFontMetricsF, QTextCursor

from gui.widgets.QCodeEditor import QCodeEditor
from gui.widgets.syntax_highlighter import PythonHighlighter
from manager.algorithms import Algorithm, check_algorithm_code, ticket_generator
from manager.algorithms.algorithm import VALUE_FUNCTIONS, GENERATOR_FUNCTIONS, MULTI_GENERATOR_FUNCTIONS


# TODO remove
user_alg = """import numpy as np

def a1():
    print(np.arange(1, 100))

def algorithm():
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
        self.change_language()
        # Setting widgets
        self.setup_code_editor()
        self.setup_function_lists()
        self.setup_check_result()
        # Binding buttons
        self.btn_check.clicked.connect(self.on_check_btn)
        self.btn_help.clicked.connect(self.on_help_btn)
        self.btn_save.clicked.connect(self.on_save_btn)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_show_funcs.clicked.connect(self.on_show_funcs_btn)
        
        
    def change_language(self):
        """
        Change interface language
        """
        # ok, self.lang_pack = self.parent.read_language_json("cell_info")
        #TODO: change
        import json
        lang = 'eng'
        if lang == 'rus':
            path = os.path.join(os.getcwd(), 'manager', 'service', 'languages', 'russian.json')
        else:
            path = os.path.join(os.getcwd(), 'manager', 'service', 'languages', 'english.json')
        with open(path, 'r', encoding='utf-8') as f:
            localization_data = json.load(f)
            self.lang_pack = localization_data['algorithm_editor']
        ok = True
        if ok:
            self.setWindowTitle(self.lang_pack.get('window_title'))
            self.label_alg_name.setText(self.lang_pack.get("alg_name"))
            self.groupBox_code_editor.setTitle(self.lang_pack.get('algorithm'))
            self.groupBox_check_result.setTitle(self.lang_pack.get('check_result'))
            self.groupBox_funcs.setTitle(self.lang_pack.get('builtin_funcs'))
            self.btn_check.setText(self.lang_pack.get('check'))
            self.btn_help.setText(self.lang_pack.get('help'))
            self.btn_save.setText(self.lang_pack.get('save'))
            self.btn_cancel.setText(self.lang_pack.get('cancel'))
            self.btn_show_funcs.setText(self.lang_pack.get('show_builtins'))
            self.plainTextEdit_check.setPlainText(self.lang_pack.get('default_check_out'))
        
        
    def setup_code_editor(self) -> None:
        """Set the code editor parameters"""
        self.code_editor = QCodeEditor()
        self.groupBox_code_editor.layout().addWidget(self.code_editor)
        self.set_font_and_highlight(self.code_editor)
        # Tabulation
        space_width = QFontMetricsF(self.code_editor.font()).horizontalAdvance(' ')
        self.code_editor.setTabStopDistance(space_width * 4)  # 4 spaces
        # Displaying algorithm
        self.code_editor.setPlainText(user_alg)
        self.code_editor.setFocus()
        self.code_editor.moveCursor(QTextCursor.End)
        
    
    def setup_function_lists(self) -> None:
        """Set up built-in function lists"""
        alg = Algorithm()
        utility_list = []
        exp_list = []
        for name, method in inspect.getmembers(alg, inspect.ismethod):
            if name in VALUE_FUNCTIONS:
                sig = inspect.signature(method)
                utility_list.append(name + self.format_signature(str(sig)))
            if name in GENERATOR_FUNCTIONS or name in MULTI_GENERATOR_FUNCTIONS:
                sig = inspect.signature(method)
                exp_list.append(name + self.format_signature(str(sig)))
        self.set_font_and_highlight(self.textEdit_functions)
        text = self.lang_pack.get('util_funcs') + '\n\n    ' + '\n\n    '.join(utility_list) + \
            '\n\n' + self.lang_pack.get('ticket_funcs') + '\n\n    ' + '\n\n    '.join(exp_list)
        self.textEdit_functions.setReadOnly(True)
        self.textEdit_functions.setPlainText(text)
        self.groupBox_funcs.setVisible(False)
        
        
    def format_signature(self, signature: str) -> str:
        """Format signature of a built-in function"""
        if signature.startswith('()'):
            return signature
        spl = signature[1:].split(')')
        return '(\n        ' + ',\n       '.join(spl[0].split(',')) + '\n    )' + spl[1]
    
    
    def setup_check_result(self) -> None:
        """Setup check result plainTextEdit"""
        self.set_font_and_highlight(self.plainTextEdit_check)
        self.plainTextEdit_check.setReadOnly(True)
    
    
    def set_font_and_highlight(self, plainTextEdit: QPlainTextEdit) -> None:
        """Apply font and highlight to the plainTextEdit"""
        # Font
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        plainTextEdit.setFont(font)
        # Highlighting
        highlight = PythonHighlighter(plainTextEdit.document())
        plainTextEdit.textChanged.connect(lambda: highlight.highlightBlock(None))
        
        
    def on_show_funcs_btn(self) -> None:
        """Show or hide built-in functions"""
        self.groupBox_funcs.setVisible(self.btn_show_funcs.isChecked())
        
        
    def on_check_btn(self) -> None:
        """Check the algorithm code"""
        status, result = check_algorithm_code(self.code_editor.toPlainText())
        if status:
            self.plainTextEdit_check.setPlainText(self.lang_pack.get('alg_compiles') + result)
        else:
            self.plainTextEdit_check.setPlainText(self.lang_pack.get('alg_could_not_compile') + result)
        # TODO remove
        alg = Algorithm()
        for ticket in ticket_generator(self.code_editor.toPlainText(), alg):
            print(ticket)
        
        
    def on_help_btn(self) -> None:
        pass
    
    
    def on_save_btn(self) -> None:
        pass
        
        
    def closeEvent(self, event):
        event.accept()
        self.parent.close()
        
        
# TODO: custom QPlainEditText for tabulation
        
# TODO: dark theme?
# palette = self.code_editor.palette()
# palette.setColor(QPalette.ColorRole.Base, QColor('#282c34'))
# palette.setColor(QPalette.ColorRole.Text, QColor('#ffffff'))
# self.code_editor.setPalette(palette)
        