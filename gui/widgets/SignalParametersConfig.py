"""Widget which configures the voltage/time on the signal window"""
import os
from functools import partial

from PyQt5.QtWidgets import QWidget, QLabel, QGroupBox, QCheckBox, QSpinBox
from PyQt5 import uic

from gui.widgets.ScientificQLineEdit import ScientificQLineEdit



class SignalParameters(QWidget):
    """Widget which configures the voltage/time on the signal window"""
    def __init__(self, parent, signal_mode: str = 'sweep'):
        super().__init__(parent)
        self.parent = parent
        # Init UI
        gui_path = os.path.join(os.getcwd(), 'gui', 'uies', 'signal_parameters.ui')
        self.ui = uic.loadUi(gui_path, self)
        # Variables
        self.signal_mode = signal_mode
        
        # Linting widget types for convenience
        self.groupBox_sweep_params: QGroupBox
        # Labels
        self.label_dir: QLabel
        self.label_rev: QLabel
        self.label_start: QLabel
        self.label_stop: QLabel
        self.label_step: QLabel
        self.label_pulse_width: QLabel
        self.label_amount: QLabel
        self.label_double: QLabel
        self.label_sweep_val: QLabel
        self.label_time: QLabel
        self.label_sweep_params: QLabel
        # ScientificQLineEdits
        self.start_dir: ScientificQLineEdit
        self.stop_dir: ScientificQLineEdit
        self.step_dir: ScientificQLineEdit
        self.start_rev: ScientificQLineEdit
        self.stop_rev: ScientificQLineEdit
        self.step_rev: ScientificQLineEdit
        self.pulse_width_dir: ScientificQLineEdit
        self.pulse_width_rev: ScientificQLineEdit
        self.scientific_widgets = [  # List for convenience
            self.start_dir,
            self.stop_dir,
            self.step_dir,
            self.start_rev,
            self.stop_rev,
            self.step_rev,
            self.pulse_width_dir,
            self.pulse_width_rev
        ]
        # Other
        self.amount_dir: QSpinBox
        self.amount_rev: QSpinBox
        self.double_dir: QCheckBox
        self.double_rev: QCheckBox
        
        # Scientific widget warnings
        for widget in self.scientific_widgets:
            widget.bad_value.connect(partial(self.parent.warn_scientific_widget, widget))
        
    
    def change_language(self, lang_pack: dict, scientific_lang_pack: dict) -> None:
        """Change the widget language"""
        self.groupBox_sweep_params.setTitle(lang_pack.get("sweep_params"))
        # Labels
        self.label_dir.setText(lang_pack.get("dir"))
        self.label_rev.setText(lang_pack.get("rev"))
        self.label_start.setText(lang_pack.get("start"))
        self.label_stop.setText(lang_pack.get("stop"))
        self.label_step.setText(lang_pack.get("step"))
        self.label_pulse_width.setText(lang_pack.get("pulse_width"))
        self.label_amount.setText(lang_pack.get("amount"))
        self.label_double.setText(lang_pack.get("double"))
        self.label_sweep_val.setText(lang_pack.get("voltage"))
        self.label_time.setText(lang_pack.get("time"))
        self.label_sweep_params.setText(lang_pack.get("sweep"))
        # ScientificQLineEdits
        self.start_dir.set_unit(lang_pack.get("volt"))
        self.stop_dir.set_unit(lang_pack.get("volt"))
        self.step_dir.set_unit(lang_pack.get("volt"))
        self.start_rev.set_unit(lang_pack.get("volt"))
        self.stop_rev.set_unit(lang_pack.get("volt"))
        self.step_rev.set_unit(lang_pack.get("volt"))
        self.pulse_width_dir.set_unit(lang_pack.get("second"))
        self.pulse_width_rev.set_unit(lang_pack.get("second"))
        for widget in self.scientific_widgets:
            widget.change_prefix_dict(scientific_lang_pack)        
