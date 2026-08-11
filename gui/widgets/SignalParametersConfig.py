"""Widget which configures the voltage/time on the signal window"""
import os
from functools import partial

from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QGroupBox, 
    QCheckBox, 
    QSpinBox, 
    QFrame, 
    QComboBox
)
from PyQt5 import uic

from gui.widgets.ScientificQLineEdit import ScientificQLineEdit



class SignalParameters(QWidget):
    """Widget which configures the voltage/time on the signal window"""         
    def __init__(self, parent, signal_mode: str = 'volt_sweep'):
        super().__init__(parent)
        self.parent = parent
        # Init UI
        gui_path = os.path.join(os.getcwd(), 'gui', 'uies', 'signal_parameters.ui')
        self.ui = uic.loadUi(gui_path, self)
        # Variables
        self.signal_mode = signal_mode
        self.used_scientific_widgets = []
        self.direction_items = {0: 'dir', 1: 'rev'}
        self.direction_indexes = {val: key for key, val in self.direction_items.items()}
        
        # Linting widget types for convenience
        self.groupBox_sweep_params: QGroupBox
        # Labels
        self.label_dir: QLabel
        self.label_rev: QLabel
        self.label_start: QLabel
        self.label_stop: QLabel
        self.label_step: QLabel
        self.label_read_vol: QLabel
        self.label_read_direction: QLabel
        self.label_pulse_width: QLabel
        self.label_amount: QLabel
        self.label_double: QLabel
        self.label_sweep_val: QLabel
        self.label_time: QLabel
        self.label_compliance_val: QLabel
        self.label_compliance: QLabel
        self.label_pulse_period: QLabel
        self.label_sweep_params: QLabel
        # ScientificQLineEdits
        self.start_dir: ScientificQLineEdit
        self.stop_dir: ScientificQLineEdit
        self.step_dir: ScientificQLineEdit
        self.start_rev: ScientificQLineEdit
        self.stop_rev: ScientificQLineEdit
        self.step_rev: ScientificQLineEdit
        self.read_voltage: ScientificQLineEdit
        self.pulse_width_dir: ScientificQLineEdit
        self.pulse_width_rev: ScientificQLineEdit
        self.pulse_period_dir: ScientificQLineEdit
        self.pulse_period_rev: ScientificQLineEdit
        self.compliance_dir: ScientificQLineEdit
        self.compliance_rev: ScientificQLineEdit
        # Other
        self.amount_dir: QSpinBox
        self.amount_rev: QSpinBox
        self.double_dir: QCheckBox
        self.double_rev: QCheckBox
        self.read_direction: QComboBox
        self.read_voltage_group: QGroupBox
        
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
        self.label_step.setText(lang_pack.get("step"))
        self.label_stop.setText(self.lang_pack.get("stop"))
        self.label_read_vol.setText(lang_pack.get("read_vol"))
        self.label_read_direction.setText(lang_pack.get("read_direction"))
        self.label_pulse_period.setText(lang_pack.get("pulse_period"))
        self.label_amount.setText(lang_pack.get("amount"))
        self.label_double.setText(lang_pack.get("double"))
        self.label_time.setText(lang_pack.get("time"))
        # Compliance tooltip
        comp_type = self.parent.parent.man.driver_attr['compliance_type']
        self.label_compliance.setText(lang_pack.get("compliance") + self.lang_pack.get(comp_type))
        self.label_compliance.setToolTip(lang_pack.get(f"{comp_type}_tooltip"))
        self.label_compliance_val.setToolTip(lang_pack.get(f"{comp_type}_tooltip"))
        # Read directions
        self.read_direction.clear()
        for item in self.direction_items.values():
            self.read_direction.addItem(lang_pack.get(item))
        self.read_direction.setCurrentIndex(1)  # TODO Check if it works
        # self.read_
        # ScientificQLineEdits
        self.start_dir.set_unit(lang_pack.get("volt"))
        self.stop_dir.set_unit(lang_pack.get("volt"))
        self.step_dir.set_unit(lang_pack.get("volt"))
        self.start_rev.set_unit(lang_pack.get("volt"))
        self.stop_rev.set_unit(lang_pack.get("volt"))
        self.step_rev.set_unit(lang_pack.get("volt"))
        self.read_voltage.set_unit(lang_pack.get("volt"))
        self.compliance_dir.set_unit(lang_pack.get("amperes"))
        self.compliance_rev.set_unit(lang_pack.get("amperes"))
        self.pulse_width_dir.set_unit(lang_pack.get("second"))
        self.pulse_width_rev.set_unit(lang_pack.get("second"))
        self.pulse_period_dir.set_unit(lang_pack.get("second"))
        self.pulse_period_rev.set_unit(lang_pack.get("second"))
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
            self.read_voltage,
            self.compliance_dir,
            self.compliance_rev,
            self.pulse_width_dir,
            self.pulse_width_rev,
            self.pulse_period_dir,
            self.pulse_period_rev
        ]
        # Widget groups: label + 2 ScientificLineEdits
        self.start_group = WidgetGroup(self, self.label_start, self.start_dir, self.start_rev)
        self.stop_group = WidgetGroup(self, self.label_stop, self.stop_dir, self.stop_rev)
        self.step_group = WidgetGroup(self, self.label_step, self.step_dir, self.step_rev)
        self.compliance_group = WidgetGroup(self, self.label_compliance, self.compliance_dir, self.compliance_rev)
        self.pulse_width_group = WidgetGroup(self, self.label_pulse_width, self.pulse_width_dir, self.pulse_width_rev)
        self.pulse_period_group = WidgetGroup(self, self.label_pulse_period, self.pulse_period_dir, self.pulse_period_rev)
        self.amount_group = WidgetGroup(self, self.label_amount, self.amount_dir, self.amount_rev)
        self.double_group = WidgetGroup(self, self.label_double, self.double_dir, self.double_rev)
        # Horizontal lines
        self.lines_h_0 = HorizontalLines(self.line_0_0, self.line_0_1, self.line_0_2, self.line_0_3)
        self.lines_h_1 = HorizontalLines(self.line_1_0, self.line_1_1, self.line_1_2, self.line_1_3)
        self.lines_h_2 = HorizontalLines(self.line_2_0, self.line_2_1, self.line_2_2, self.line_2_3)
        self.lines_h_3 = HorizontalLines(self.line_3_0, self.line_3_1, self.line_3_2, self.line_3_3)
        self.lines_h_4 = HorizontalLines(self.line_4_0, self.line_4_1, self.line_4_2, self.line_4_3)
        
        
    def set_horizontal_lines_visible(self, visible_flags: list[bool]) -> None:
            """Change visibility of the horizontal lines"""
            for line_group, flag in zip([self.lines_h_0, self.lines_h_1, self.lines_h_2, self.lines_h_3, self.lines_h_4], visible_flags):
                line_group.setVisible(flag)
                    
                    
    def set_vertical_lines_visible(self, visible_flags: list[bool]) -> None:
        """Change visibility of the vertical lines"""
        for line, flag in zip([self.line_v_0, self.line_v_1, self.line_v_2], visible_flags):
            line.setVisible(flag)
            
            
    def set_mode(self, mode: str) -> None:
        """Change ui based on signal mode"""
        self.mode = mode
        self.ui_fields = self.parent.parent.man.menu.ui_fields(mode).split(', ')
        self.base_mode = self.ui_fields[0]
        if self.base_mode == 'volt_sweep':
            self.show_sweep()
        elif self.base_mode == 'endurance':
            self.show_endurance()
        elif self.base_mode == 'retention':
            self.show_retention()
        else:
            raise RuntimeError(f'Unknown signal mode: {self.base_mode}')
        
        
    def show_sweep(self) -> None:
        """Show sweep ui"""
        self.used_scientific_widgets = []
        # Top widgets
        self.label_dir.show()
        self.label_rev.show()
        # Group widgets
        self.start_group.show()
        self.stop_group.show()
        self.step_group.show()
        self.compliance_group.show()
        self.pulse_width_group.show()
        self.pulse_period_group.hide()
        self.amount_group.show()
        self.double_group.show()
        self.read_voltage_group.setVisible('+amp_read' in self.ui_fields)
        # Left widgets
        self.label_sweep_val.show()
        self.label_compliance_val.show()
        self.label_time.show()
        self.label_sweep_params.show()
        # Gray lines
        self.set_horizontal_lines_visible([True, True, True, True, '+amp_read' in self.ui_fields])
        self.set_vertical_lines_visible([True, True, True])
        # Labels
        self.label_sweep_val.setText(self.lang_pack.get("voltage"))
        self.label_compliance_val.setText(self.lang_pack.get("current"))
        self.label_start.setText(self.lang_pack.get("start"))
        self.label_sweep_params.setText(self.lang_pack.get("sweep"))
        if 'pw_to_int' in self.ui_fields:
            self.label_pulse_width.setText(self.lang_pack.get("interval"))
        else:
            self.label_pulse_width.setText(self.lang_pack.get("pulse_width"))
        
        
    def show_endurance(self) -> None:
        """Show endurance ui (reduced)"""
        self.used_scientific_widgets = []
        # Top widgets
        self.label_dir.show()
        self.label_rev.show()
        # Group widgets
        self.start_group.show()
        self.stop_group.hide()
        self.step_group.hide()
        self.compliance_group.show()
        self.pulse_width_group.show()
        self.pulse_period_group.setVisible('+period' in self.ui_fields)
        self.amount_group.show()
        self.double_group.hide()
        self.read_voltage_group.setVisible('+amp_read' in self.ui_fields)
        # Left widgets
        self.label_sweep_val.show()
        self.label_compliance_val.show()
        self.label_time.show()
        self.label_sweep_params.show()
        # Gray lines
        self.set_horizontal_lines_visible([True, True, True, True, '+amp_read' in self.ui_fields])
        self.set_vertical_lines_visible([True, True, True])
        # Labels
        self.label_start.setText(self.lang_pack.get("amplitude"))
        self.label_sweep_val.setText(self.lang_pack.get("voltage"))
        self.label_compliance_val.setText(self.lang_pack.get("current"))
        self.label_sweep_params.setText(self.lang_pack.get("pulse"))
        self.label_pulse_width.setText(self.lang_pack.get("pulse_width"))
                
        
    def show_retention(self) -> None:
        """Show retention ui (reduced)"""
        self.used_scientific_widgets = []
        # Checking whether to show one column (dir) or hide the whole table
        show_table_flag = '+pw' in self.ui_fields or '+period' in self.ui_fields or '+comp' in self.ui_fields
        # Top widgets
        self.label_dir.hide()
        self.label_rev.hide()
        # Group widgets
        self.start_group.hide()
        self.stop_group.hide()
        self.step_group.hide()
        self.compliance_group.setVisible_dir('+comp' in self.ui_fields)
        self.pulse_width_group.setVisible_dir('+pw' in self.ui_fields)
        self.pulse_period_group.setVisible_dir('+period' in self.ui_fields)
        self.amount_group.hide()
        self.double_group.hide()
        self.read_voltage_group.setVisible('+amp_read' in self.ui_fields)
        if not show_table_flag:  # Hiding everything except label_sweep_val
            # Left widgets
            self.label_sweep_val.show()
            self.label_compliance_val.hide()
            self.label_time.hide()
            self.label_sweep_params.hide()
            # Gray lines
            self.set_horizontal_lines_visible([False, False, False, False, False])
            self.set_vertical_lines_visible([False, False, False])
            # Labels
            self.label_sweep_val.setText(self.lang_pack.get("voltage_in_settings"))
        else:  # Showing table with one column
            show_time_flag = '+pw' in self.ui_fields or '+period' in self.ui_fields
            # Left widgets
            self.label_sweep_val.hide()
            self.label_compliance_val.setVisible('+comp' in self.ui_fields)
            self.label_time.setVisible(show_time_flag)
            self.label_sweep_params.hide()
            # Gray lines
            if show_time_flag and '+comp' in self.ui_fields:  # Both time and compliance are present, separate them by a line
                self.lines_h_2.show_specific([0, 1, 2])
            else:
                self.lines_h_2.hide()
            for line_gr in [self.lines_h_0, self.lines_h_1, self.lines_h_3, self.lines_h_4]:
                line_gr.hide()
            self.set_vertical_lines_visible([True, True, False])
            # Labels
            self.label_compliance_val.setText(self.lang_pack.get("current"))
            self.label_pulse_width.setText(self.lang_pack.get("pulse_width"))
            
            
    def fill_params_to_ticket(self, ticket: dict) -> tuple[bool, dict]:
        """Fill in params in the ticket dict"""
        # Checking if all scientific widgets are fine
        for widget in self.used_scientific_widgets:
            if widget.get_value() is None:
                return False, ticket
        ticket['params'] = {}  # Clearing parameters
        # Filling in based on the mode
        if self.base_mode == 'volt_sweep':
            ticket = self.fill_params_sweep(ticket)
        elif self.base_mode == 'endurance':
            ticket = self.fill_params_endurance(ticket)
        elif self.base_mode == 'retention':
            ticket = self.fill_params_retention(ticket)
        else:
            print(f'Filling params: unknown mode {self.base_mode}')
            return False, ticket
        return True, ticket
    
    
    def fill_params_sweep(self, ticket: dict) -> dict:
        """Fill in params for a sweep based mode"""
        # Sweep
        ticket['params']['start_dir'] = self.start_dir.get_value()
        ticket['params']['stop_dir'] = self.stop_dir.get_value()
        ticket['params']['step_dir'] = self.step_dir.get_value()
        ticket['params']['start_rev'] = self.start_rev.get_value()
        ticket['params']['stop_rev'] = self.stop_rev.get_value()
        ticket['params']['step_rev'] = self.step_rev.get_value()
        # Compliance
        ticket['params']['compliance_dir'] = self.compliance_dir.get_value()
        ticket['params']['compliance_rev'] = self.compliance_rev.get_value()
        # Time
        if 'pw_to_int' in self.ui_fields:  # Replace pulse width with interval
            ticket['params']['interval_dir'] = self.pulse_width_dir.get_value()
            ticket['params']['interval_rev'] = self.pulse_width_rev.get_value()
        else:
            ticket['params']['pulse_width_dir'] = self.pulse_width_dir.get_value()
            ticket['params']['pulse_width_rev'] = self.pulse_width_rev.get_value()
        # Sweep params
        ticket['params']['amount_dir'] = self.amount_dir.value()
        ticket['params']['amount_rev'] = self.amount_rev.value()
        ticket['params']['double_dir'] = self.double_dir.isChecked()
        ticket['params']['double_rev'] = self.double_rev.isChecked()
        # Read
        if '+amp_read' in self.ui_fields:
            ticket['params']['read_voltage'] = self.read_voltage.get_value()
            ticket['params']['read_direction'] = self.direction_items[self.read_direction.currentIndex()]
        return ticket
        
        
    def fill_params_endurance(self, ticket: dict) -> dict:
        """Fill in params for an endurance based mode"""
        # Pulse
        ticket['params']['amplitude_dir'] = self.start_dir.get_value()
        ticket['params']['amplitude_rev'] = self.start_rev.get_value()
        # Compliance
        ticket['params']['compliance_dir'] = self.compliance_dir.get_value()
        ticket['params']['compliance_rev'] = self.compliance_rev.get_value()
        # Time
        ticket['params']['pulse_width_dir'] = self.pulse_width_dir.get_value()
        ticket['params']['pulse_width_rev'] = self.pulse_width_rev.get_value()
        if '+period' in self.ui_fields:  # Add period
            ticket['params']['pulse_period_dir'] = self.pulse_period_dir.get_value()
            ticket['params']['pulse_period_rev'] = self.pulse_period_rev.get_value()
        # Amount params
        ticket['params']['amount_dir'] = self.amount_dir.value()
        ticket['params']['amount_rev'] = self.amount_rev.value()
        # Read
        if '+amp_read' in self.ui_fields:  # Add read voltage
            ticket['params']['read_voltage'] = self.read_voltage.get_value()
            ticket['params']['read_direction'] = self.direction_items[self.read_direction.currentIndex()]
        return ticket
    
            
    def fill_params_retention(self, ticket: dict) -> dict:
        """Fill in params for a retention based mode"""
        # Compliance
        if '+comp' in self.ui_fields:
            ticket['params']['compliance'] = self.compliance_dir.get_value()
        # Time
        if '+pw' in self.ui_fields:
            ticket['params']['pulse_width'] = self.pulse_width_dir.get_value()
        if '+period' in self.ui_fields:
            ticket['params']['pulse_period'] = self.pulse_period_dir.get_value()
        # Read 
        if '+amp_read' in self.ui_fields:
            ticket['params']['read_voltage'] = self.read_voltage.get_value()
            ticket['params']['read_direction'] = self.direction_items[self.read_direction.currentIndex()]
        return ticket
    
    
    def load_ticket_to_ui(self, ticket: dict) -> None:
        """Load ticket to the ui. The .set_mode() is expected to be called before this method"""
        # Filling in based on the mode
        if self.base_mode == 'volt_sweep':
            self.load_ticket_sweep(ticket)
        elif self.base_mode == 'endurance':
            self.load_ticket_endurance(ticket)
        elif self.base_mode == 'retention':
            self.load_ticket_retention(ticket)
        else:
            raise RuntimeError(f'Loading ticket to ui: unknown mode {self.base_mode}')
        
    
    def load_ticket_sweep(self, ticket: dict) -> None:
        """Load a sweep based ticket to the UI"""
        # Sweep
        self.start_dir.set_value(ticket['params']['start_dir'])
        self.stop_dir.set_value(ticket['params']['stop_dir'])
        self.step_dir.set_value(ticket['params']['step_dir'])
        self.start_rev.set_value(ticket['params']['start_rev'])
        self.stop_rev.set_value(ticket['params']['stop_rev'])
        self.step_rev.set_value(ticket['params']['step_rev'])
        # Compliance
        self.compliance_dir.set_value(ticket['params']['compliance_dir'])
        self.compliance_rev.set_value(ticket['params']['compliance_rev'])
        # Time
        if 'pw_to_int' in self.ui_fields:  # Replace pulse width with interval
            self.pulse_width_dir.set_value(ticket['params']['interval_dir'])
            self.pulse_width_rev.set_value(ticket['params']['interval_rev'])
        else:
            self.pulse_width_dir.set_value(ticket['params']['pulse_width_dir'])
            self.pulse_width_rev.set_value(ticket['params']['pulse_width_rev'])
        # Sweep params
        self.amount_dir.setValue(ticket['params']['amount_dir'])
        self.amount_rev.setValue(ticket['params']['amount_rev'])
        self.double_dir.setChecked(ticket['params']['double_dir'])
        self.double_rev.setChecked(ticket['params']['double_rev'])
        # Read
        if '+amp_read' in self.ui_fields:  # Add read voltage
            self.read_voltage.set_value(ticket['params']['read_voltage'])
            self.read_direction.setCurrentIndex(self.direction_indexes[ticket['params']['read_direction']])
        
        
    def load_ticket_endurance(self, ticket: dict) -> None:
        """Load an endurance based ticket to the UI"""
        # Pulse
        self.start_dir.set_value(ticket['params']['amplitude_dir'])
        self.start_rev.set_value(ticket['params']['amplitude_rev'])
        # Compliance
        self.compliance_dir.set_value(ticket['params']['compliance_dir'])
        self.compliance_rev.set_value(ticket['params']['compliance_rev'])
        # Time
        self.pulse_width_dir.set_value(ticket['params']['pulse_width_dir'])
        self.pulse_width_rev.set_value(ticket['params']['pulse_width_rev'])
        if '+period' in self.ui_fields:  # Add period
            self.pulse_period_dir.set_value(ticket['params']['pulse_period_dir'])
            self.pulse_period_rev.set_value(ticket['params']['pulse_period_rev'])
        # Amount params
        self.amount_dir.setValue(ticket['params']['amount_dir'])
        self.amount_rev.setValue(ticket['params']['amount_rev'])
        # Read
        if '+amp_read' in self.ui_fields:  # Add read voltage
            self.read_voltage.set_value(ticket['params']['read_voltage'])
            self.read_direction.setCurrentIndex(self.direction_indexes[ticket['params']['read_direction']])
        
            
    def load_ticket_retention(self, ticket: dict) -> None:
        """Load a retention based ticket to the UI"""
        # Compliance
        if '+comp' in self.ui_fields:
            self.compliance_dir.set_value(ticket['params']['compliance'])
        # Time
        if '+pw' in self.ui_fields:
            self.pulse_width_dir.set_value(ticket['params']['pulse_width'])
        if '+period' in self.ui_fields:
            self.pulse_period_dir.set_value(ticket['params']['pulse_period'])
        # Read 
        if '+amp_read' in self.ui_fields:
            self.read_voltage.set_value(ticket['params']['read_voltage'])
            self.read_direction.setCurrentIndex(self.direction_indexes[ticket['params']['read_direction']])      
 
        
        
# ----- HELPER CLASSES -----

class WidgetGroup:
    """Widget group: label + dir/rev parameter widget"""
    def __init__(self, parent: SignalParameters, label: QLabel, dir_widget: QWidget, rev_widget: QWidget) -> None:
        self.parent = parent
        self.label = label
        self.dir_widget = dir_widget
        self.rev_widget = rev_widget
        
    def show(self) -> None:
        """Show widget group"""
        self.label.show()
        self.dir_widget.show()
        self.rev_widget.show()
        if isinstance(self.dir_widget, ScientificQLineEdit):
            self.parent.used_scientific_widgets.append(self.dir_widget)
            self.parent.used_scientific_widgets.append(self.rev_widget)
            
    def show_dir(self) -> None:
        """Show label and dir widget only, hide rev widget"""
        self.label.show()
        self.dir_widget.show()
        self.rev_widget.hide()
        if isinstance(self.dir_widget, ScientificQLineEdit):
            self.parent.used_scientific_widgets.append(self.dir_widget)
        
    def hide(self) -> None:
        """Hide widget group"""
        self.label.hide()
        self.dir_widget.hide()
        self.rev_widget.hide()
            
    def setVisible(self, visible_flag: bool) -> None:
        """Change visibility by a flag"""
        if visible_flag:
            self.show()
        else:
            self.hide()
            
    def setVisible_dir(self, visible_flag: bool) -> None:
        """Set visible dir widget only"""
        if visible_flag:
            self.show_dir()
        else:
            self.hide()
            
            
class HorizontalLines:
    """Widget group for a row of horizontal lines"""
    def __init__(self, line_1: QFrame, line_2: QFrame, line_3: QFrame, line_4: QFrame) -> None:
        self.lines = [line_1, line_2, line_3, line_4]
        
    def show(self) -> None:
        """Show widget group"""
        for line in self.lines:
            line.show()
            
    def show_specific(self, indexes: list[int]) -> None:
        """Show specific lines by their indexes"""
        for i, line in enumerate(self.lines):
            line.setVisible(i in indexes)
    
    def hide(self) -> None:
        """Hide widget group"""
        for line in self.lines:
            line.hide()
            
    def setVisible(self, visible_flag: bool) -> None:
        """Change visibility by a flag"""
        if visible_flag:
            self.show()
        else:
            self.hide()
# --------------------------