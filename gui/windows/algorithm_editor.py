"""Algorithm editor"""
import os
import inspect
import json
from typing import Union

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QPlainTextEdit, QFileDialog, QShortcut
from PyQt5.QtGui import QFontDatabase, QFontMetricsF, QTextCursor, QKeySequence

from gui.widgets.QCodeEditor import QCodeEditor
from gui.widgets.syntax_highlighter import PythonHighlighter
from gui.src import show_warning_messagebox, show_choose_window
from manager.service.global_settings import ALGORITHM_PATH, TICKET_PATH
from manager.algorithms import Algorithm, check_algorithm_code, execute_algorithm
from manager.algorithms.algorithm import VALUE_FUNCTIONS, GENERATOR_FUNCTIONS, MULTI_GENERATOR_FUNCTIONS



BASE_ALGORITHM = """def algorithm():
"""



class AlgorithmEditor(QDialog):
    """Algorithm editor"""
    
    lang_pack: dict
    safe_to_close: bool
    
    def __init__(self, parent=None, ticket: Union[dict, None] = None):
        super().__init__(parent)
        self.parent = parent
        self.ui = uic.loadUi(os.path.join(os.getcwd(), 'gui', 'uies', 'algorithm_editor.ui'), self)
        self.setModal(True)
        self.change_language()
        self.ticket_at_start = ticket  # Ticket on opening the window
        if ticket is None:
            self.mode = 'create'
            self.btn_save.setVisible(False)  # Hiding the save button, only saving to file
        else:
            self.mode = 'edit'
        self.safe_to_close = False
        # Setting widgets
        self.setup_code_editor(ticket)
        self.setup_function_lists()
        self.setup_check_result()
        # Binding buttons
        self.btn_check.clicked.connect(self.check_algorithm)
        self.btn_help.clicked.connect(self.on_help_btn)
        self.btn_save.clicked.connect(self.on_save_btn)
        self.btn_save_to_file.clicked.connect(self.on_save_to_file_btn)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_show_funcs.clicked.connect(self.on_show_funcs_btn)
        self.btn_ticket_export.clicked.connect(self.on_ticket_import_btn)
        # Shortcuts
        QShortcut(QKeySequence('F1'), self).activated.connect(self.on_help_btn)
        
        
    def change_language(self):
        """
        Change interface language
        """
        ok, self.lang_pack = self.parent.parent.read_language_json("algorithm_editor")
        if ok:
            self.setWindowTitle(self.lang_pack.get('window_title'))
            self.label_alg_name.setText(self.lang_pack.get("alg_name"))
            self.groupBox_code_editor.setTitle(self.lang_pack.get('algorithm'))
            self.groupBox_check_result.setTitle(self.lang_pack.get('check_result'))
            self.groupBox_funcs.setTitle(self.lang_pack.get('builtin_funcs'))
            self.btn_check.setText(self.lang_pack.get('check'))
            self.btn_help.setText(self.lang_pack.get('help'))
            self.btn_save.setText(self.lang_pack.get('save'))
            self.btn_save_to_file.setText(self.lang_pack.get('save_to_file'))
            self.btn_cancel.setText(self.lang_pack.get('cancel'))
            self.btn_show_funcs.setText(self.lang_pack.get('show_builtins'))
            self.btn_ticket_export.setText(self.lang_pack.get('ticket_export'))
            self.plainTextEdit_check.setPlainText(self.lang_pack.get('default_check_out'))
            self.btn_ticket_export.setToolTip(self.lang_pack.get('ticket_export_tooltip'))
            self.btn_check.setToolTip(self.lang_pack.get('check_tooltip'))
            self.btn_save.setToolTip(self.lang_pack.get('save_tooltip'))
            self.btn_save_to_file.setToolTip(self.lang_pack.get('save_to_file_tooltip'))
        
        
    def setup_code_editor(self, ticket: Union[str, None]) -> None:
        """Set the code editor parameters"""
        self.code_editor = QCodeEditor()
        self.groupBox_code_editor.layout().addWidget(self.code_editor)
        self.set_font_and_highlight(self.code_editor)
        # Tabulation
        space_width = QFontMetricsF(self.code_editor.font()).horizontalAdvance(' ')
        self.code_editor.setTabStopDistance(space_width * 4)  # 4 spaces
        # Parsing initial algorithm ticket
        if ticket is None:
            self.code_editor.setPlainText(BASE_ALGORITHM)
        else:
            try:
                self.code_editor.setPlainText(ticket['code'])
                self.lineEdit_alg_name.setText(ticket['name'])
            except Exception as e:
                show_warning_messagebox(self, self.lang_pack.get('could_not_read') + f'{type(e).__name__}: {e}')
                self.code_editor.setPlainText(BASE_ALGORITHM)
        # Displaying algorithm
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
            
            
    def check_algorithm(self) -> tuple[bool, dict]:
        """Check the algorithm and get tickets used in it.

        Returns:
            status, used_tickets: (tuple[bool, dict]): Status and used tickets.
        """
        status, result, used_tickets = check_algorithm_code(self.code_editor.toPlainText(), get_used_tickets=True)
        if not status:
            self.plainTextEdit_check.setPlainText(self.lang_pack.get('alg_could_not_compile') + result)
            return status, used_tickets
        status, exec_result = execute_algorithm(self.code_editor.toPlainText(), manager=self.parent.parent.man)
        if status:
            self.plainTextEdit_check.setPlainText(self.lang_pack.get('alg_compiles') + result)
        else:
            self.plainTextEdit_check.setPlainText(self.lang_pack.get('alg_could_not_compile') + exec_result)
        return status, used_tickets
        
        
    def on_help_btn(self) -> None:
        """Show help window with algorithm manual"""
        self.parent.parent.show_help(parent=self, section='algorithms')
    
    
    def on_ticket_import_btn(self) -> None:
        """Import tickets used in the code to ticket folder"""
        status, used_tickets = self.check_algorithm()
        if not status:
            # If algorithm does not compile, try to export from base algorithm ticket
            if self.ticket_at_start is None:  # No ticket at start, nothing to export from
                show_warning_messagebox(self, self.lang_pack.get('bad_code_on_ticket_import'))
                return
            used_tickets = self.ticket_at_start['tickets']  # Exporting from algorithm ticket
        if len(used_tickets) == 0:  # No tickets in the algorithm
            show_warning_messagebox(self, self.lang_pack.get('no_tickets_to_export'))
            return
        folder = QFileDialog.getExistingDirectory(self, 
                                                  caption=self.lang_pack.get('choose_folder'),
                                                  directory=TICKET_PATH)
        if folder == '':
            return
        for name, ticket in used_tickets.items():
            path = os.path.join(folder, name + '.json')
            if os.path.exists(path):
                # Ask if user wants to rewrite the ticket
                if not show_choose_window(self, self.lang_pack.get('ticket_name') + "'" + name + "'" + self.lang_pack.get('already_exists')):
                    continue
            with open(path, 'w', encoding='utf-8') as file:
                json.dump(ticket, file, ensure_ascii=False, indent=4)
        self.parent.refresh_list()
    
    
    def get_ticket_for_saving(self) -> dict:
        """Get algorithm ticket before saving"""
        status, used_tickets = self.check_algorithm()
        if not status:
            show_warning_messagebox(self, self.lang_pack.get('bad_code_on_save'))
            return None
        name = self.lineEdit_alg_name.text().strip()
        if name == '':
            show_warning_messagebox(self, self.lang_pack.get('no_alg_name'))
            return None
        alg_ticket = {
            'name': name,
            'mode': 'algorithm',
            'params': {},
            'code': self.code_editor.toPlainText(),
            'tickets': used_tickets,
            'executed_tickets': []
        }
        return alg_ticket
    
    
    def on_save_btn(self) -> None:
        """Save algorithm to experiment plan"""
        alg_ticket = self.get_ticket_for_saving()
        self.parent.apply_edit_to_exp_list(alg_ticket)
        self.safe_to_close = True
        self.close()
            
            
    def on_save_to_file_btn(self) -> None:
        """Save algorithm to experiment plan and file"""
        alg_ticket = self.get_ticket_for_saving()
        if alg_ticket is None: 
            return
        if self.mode == 'edit':
            self.parent.apply_edit_to_exp_list(alg_ticket)
        if alg_ticket['name'] in self.parent.parent.protected_algorithms:
            show_warning_messagebox(self, self.lang_pack.get("alg_protected"))
            return
        save_path = os.path.join(ALGORITHM_PATH, alg_ticket['name'] + '.json')
        if os.path.exists(save_path):
            if not show_choose_window(self, self.lang_pack.get("an_algorithm") + "'" + alg_ticket['name'] + "'" + self.lang_pack.get('already_exists')):
                return
        try:  # Saving to file
            with open(save_path, mode='w', encoding='utf-8') as file:
                json.dump(alg_ticket, file, ensure_ascii=False, indent=4)
            self.safe_to_close = True
            self.close()
        except Exception as e:
            show_warning_messagebox(self, self.lang_pack.get('could_not_save') + f'{type(e).__name__}: {e}')
                                            
        
    def closeEvent(self, event):
        if self.safe_to_close:  # This flag is True if closing after saving the algorithm
            event.accept()
        else:
            if self.ticket_at_start is None:
                code_at_start = BASE_ALGORITHM
            else:
                code_at_start = self.ticket_at_start['code']
            # Checking if code was changed, confirming if user wants to close
            if self.code_editor.toPlainText() != code_at_start:
                if show_choose_window(self, self.lang_pack.get('choose_closing')):
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
        self.parent.refresh_alg_list()
        
# TODO: dark theme?
        