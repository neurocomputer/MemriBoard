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
        # Other
        self.amount_dir: QSpinBox
        self.amount_rev: QSpinBox
        self.double_dir: QCheckBox
        self.double_rev: QCheckBox
        
        self.create_item_groups()
        # Scientific widget warnings
        for widget in self.scientific_widgets:
            widget.bad_value.connect(partial(self.parent.warn_scientific_widget, widget))
        
    
    def change_language(self, lang_pack: dict, scientific_lang_pack: dict) -> None:
        """Change the widget language"""
        self.lang_pack = lang_pack
        self.groupBox_sweep_params.setTitle(lang_pack.get("sweep_params"))
        # Labels
        self.label_dir.setText(lang_pack.get("dir"))
        self.label_rev.setText(lang_pack.get("rev"))
        self.label_stop.setText(lang_pack.get("stop"))
        self.label_step.setText(lang_pack.get("step"))
        self.label_pulse_width.setText(lang_pack.get("pulse_width"))
        self.label_amount.setText(lang_pack.get("amount"))
        self.label_double.setText(lang_pack.get("double"))
        self.label_time.setText(lang_pack.get("time"))
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
            
            
    def create_item_groups(self) -> None:
        """Create item group lists for convenience"""
        self.scientific_widgets = [  # ScientificQLineEdits
            self.start_dir,
            self.stop_dir,
            self.step_dir,
            self.start_rev,
            self.stop_rev,
            self.step_rev,
            self.pulse_width_dir,
            self.pulse_width_rev
        ]
        self.start_group = [  # Start LineEdits and label
            self.label_start,
            self.start_dir,
            self.start_rev
        ]
        self.stop_group = [  # Stop LineEdits and label
            self.label_stop,
            self.stop_dir,
            self.stop_rev
        ]
        self.step_group = [  # Step LineEdits and label
            self.label_step,
            self.step_dir,
            self.step_rev
        ]
        self.pulse_width_group = [  # Pulse width LineEdits and label
            self.label_pulse_width,
            self.pulse_width_dir,
            self.pulse_width_rev
        ]
        self.amount_group = [  # Amount SpinBoxes and label
            self.label_amount,
            self.amount_dir,
            self.amount_rev
        ]
        self.double_group = [  # Double CheckBoxes and label
            self.label_double,
            self.double_dir,
            self.double_rev
        ]
        # First horizontal line row
        self.lines_h_0 = [self.line_0_0, self.line_0_1, self.line_0_2, self.line_0_3]
        # Second horizontal line row
        self.lines_h_1 = [self.line_1_0, self.line_1_1, self.line_1_2, self.line_1_3]
        # Third horizontal line row
        self.lines_h_2 = [self.line_2_0, self.line_2_1, self.line_2_2, self.line_2_3]
            
            
    def set_mode(self, mode: str) -> None:
        """Change ui based on signal mode"""
        # TODO reimplement in VISA_instruments
        self.mode = mode
        if mode == 'volt_sweep':
            self.show_sweep()
        elif mode == 'endurance':
            self.show_endurance()
        elif mode == 'retention':
            self.show_retention()
        elif mode == 'pot-dep':
            self.show_endurance()  # Same ui as for endurance
        else:
            raise RuntimeError(f'Unknown signal mode: {mode}')
        
        
    def show_sweep(self) -> None:
        """Show sweep ui"""
        for widget in [  # Showing all widgets
            self.label_dir,
            self.label_rev,
            *self.start_group,
            *self.stop_group,
            *self.step_group,
            *self.pulse_width_group,
            *self.amount_group,
            *self.double_group,
            self.label_sweep_val,
            self.label_time,
            self.label_sweep_params,
        ]:
            widget.show()
        # Gray lines
        self.set_horizontal_lines_visible([True, True, True, True])
        self.set_vertical_lines_visible([True, True, True])
        # Labels
        self.label_sweep_val.setText(self.lang_pack.get("voltage"))
        self.label_start.setText(self.lang_pack.get("start"))
        self.label_sweep_params.setText(self.lang_pack.get("sweep"))
        # Scientific widgets used in the mode
        self.used_scientific_widgets = self.scientific_widgets  # TODO change in VISA-instruments
        
        
    def show_endurance(self) -> None:
        """Show endurance ui (reduced)"""
        for widget in [  # Showing widgets
            self.label_dir,
            self.label_rev,
            *self.start_group,
            *self.pulse_width_group,
            *self.amount_group,
            self.label_sweep_val,
            self.label_time,
            self.label_sweep_params
        ]:
            widget.show()
        for widget in [  # Hiding widgets
            *self.stop_group,
            *self.step_group,
            *self.double_group
        ]:
            widget.hide()
        # Gray lines
        self.set_horizontal_lines_visible([True, True, True, True])
        self.set_vertical_lines_visible([True, True, True])
        # Labels
        self.label_sweep_val.setText(self.lang_pack.get("voltage"))
        self.label_start.setText(self.lang_pack.get("amplitude"))
        self.label_sweep_params.setText(self.lang_pack.get("pulse"))
        # Scientific widgets used in the mode
        self.used_scientific_widgets = [
            *self.start_group[1:],
            *self.pulse_width_group[1:]
        ]
        
        
    def show_retention(self) -> None:
        """Show retention ui (reduced)"""
        for widget in [  # Hiding widgets
            self.label_dir,
            self.label_rev,
            *self.start_group,
            *self.stop_group,
            *self.step_group,
            *self.pulse_width_group,
            *self.amount_group,
            *self.double_group,
            self.label_time,
            self.label_sweep_params
        ]:
            widget.hide()
        # Gray lines
        self.set_horizontal_lines_visible([False, False, False, False])
        self.set_vertical_lines_visible([False, False, False])
        # Labels
        self.label_sweep_val.show()
        self.label_sweep_val.setText(self.lang_pack.get("voltage_in_settings"))
        # Scientific widgets used in the mode
        self.used_scientific_widgets = []
        
        
    def set_horizontal_lines_visible(self, visible_flags: list[bool]) -> None:
        """Change visibility of the horizontal lines"""
        for line_group, flag in zip([self.lines_h_0, self.lines_h_1, self.lines_h_2], visible_flags):
            for line in line_group:
                line.setVisible(flag)
                
                
    def set_vertical_lines_visible(self, visible_flags: list[bool]) -> None:
        """Change visibility of the vertical lines"""
        for line, flag in zip([self.line_v_0, self.line_v_1, self.line_v_2], visible_flags):
            line.setVisible(flag)
            
            
    def fill_params_to_ticket(self, ticket: dict) -> dict:
        """Fill in params in the ticket dict"""
        # Checking if all scientific widgets are fine
        for widget in self.used_scientific_widgets:
            if widget.get_value() is None:
                raise ValueError
        ticket['params'] = {}  # Clearing parameters
        # Filling in based on the mode
        if self.mode == 'volt_sweep':
            # Sweep
            ticket['params']['start_dir'] = self.start_dir.get_value()
            ticket['params']['stop_dir'] = self.stop_dir.get_value()
            ticket['params']['step_dir'] = self.step_dir.get_value()
            ticket['params']['start_rev'] = self.start_rev.get_value()
            ticket['params']['stop_rev'] = self.stop_rev.get_value()
            ticket['params']['step_rev'] = self.step_rev.get_value()
            # Time
            ticket['params']['pulse_width_dir'] = self.pulse_width_dir.get_value()
            ticket['params']['pulse_width_rev'] = self.pulse_width_rev.get_value()
            # Sweep params
            ticket['params']['amount_dir'] = self.amount_dir.value()
            ticket['params']['amount_rev'] = self.amount_rev.value()
            ticket['params']['double_dir'] = self.double_dir.isChecked()
            ticket['params']['double_rev'] = self.double_rev.isChecked()
        elif self.mode in ['endurance', 'pot-dep']:
            # Pulse
            ticket['params']['amplitude_dir'] = self.start_dir.get_value()
            ticket['params']['amplitude_rev'] = self.start_rev.get_value()
            # Time
            ticket['params']['pulse_width_dir'] = self.pulse_width_dir.get_value()
            ticket['params']['pulse_width_rev'] = self.pulse_width_rev.get_value()
            # Amount params
            ticket['params']['amount_dir'] = self.amount_dir.value()
            ticket['params']['amount_rev'] = self.amount_rev.value()
        elif self.mode == 'retention':
            pass  # No parameters for this mode
        else:
            raise RuntimeError(f'Filling params: unknown mode {self.mode}')
        return ticket
    
    def load_ticket_to_ui(self, ticket: dict) -> None:
        """Load ticket to the ui. The .set_mode() is expected to be called before this method"""
        # Filling in based on the mode
        if self.mode == 'volt_sweep':
            # Sweep
            self.start_dir.set_value(ticket['params']['start_dir'])
            self.stop_dir.set_value(ticket['params']['stop_dir'])
            self.step_dir.set_value(ticket['params']['step_dir'])
            self.start_rev.set_value(ticket['params']['start_rev'])
            self.stop_rev.set_value(ticket['params']['stop_rev'])
            self.step_rev.set_value(ticket['params']['step_rev'])
            # Time
            self.pulse_width_dir.set_value(ticket['params']['pulse_width_dir'])
            self.pulse_width_rev.set_value(ticket['params']['pulse_width_rev'])
            # Sweep params
            self.amount_dir.setValue(ticket['params']['amount_dir'])
            self.amount_rev.setValue(ticket['params']['amount_rev'])
            self.double_dir.setChecked(ticket['params']['double_dir'])
            self.double_rev.setChecked(ticket['params']['double_rev'])
        elif self.mode in ['endurance', 'pot-dep']:
            # Pulse
            self.start_dir.set_value(ticket['params']['amplitude_dir'])
            self.start_rev.set_value(ticket['params']['amplitude_rev'])
            # Time
            self.pulse_width_dir.set_value(ticket['params']['pulse_width_dir'])
            self.pulse_width_rev.set_value(ticket['params']['pulse_width_rev'])
            # Amount params
            self.amount_dir.setValue(ticket['params']['amount_dir'])
            self.amount_rev.setValue(ticket['params']['amount_rev'])        
        elif self.mode == 'retention':
            pass  # No parameters for this mode
        else:
            raise RuntimeError(f'Filling params: unknown mode {self.mode}')
        
