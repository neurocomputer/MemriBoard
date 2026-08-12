"""
Класс QLineEdit, поддерживающей префиксы СИ
"""
# Похожее решение: https://github.com/Ulm-IQO/qudi/blob/master/qtwidgets/scientific_spinbox.py

from PyQt5.QtWidgets import QLineEdit
import numpy as np
from typing import Union
from PyQt5.QtCore import pyqtSignal


prefixes = {  # Fallback
        'y': 1e-24,
        'z': 1e-21,
        'a': 1e-18,
        'f': 1e-15,
        'p': 1e-12,
        'n': 1e-9,
        'u': 1e-6,
        'm': 1e-3,
        '': 1,
        'k': 1e3,
        'M': 1e6,
        'G': 1e9,
        'T': 1e12,
        'P': 1e15,
        'E': 1e18,
        'Z': 1e21,
        'Y': 1e24
    }



class ScientificQLineEdit(QLineEdit):
    """
    Line Edit that supports SI prefixes.
    
    Attributes:
        unit (str): Physical unit.
        value (float | None): Value stored in the line edit. 
            If it's not a valid float, the value is None.
    """
    bad_value = pyqtSignal(str)
    unit = ''
    value = None
    def __init__(self, *args, **kwargs) -> None:
        """Custom QLineEdit class with SI prefixes
        """
        super().__init__(*args, **kwargs)
        self.change_prefix_dict(prefixes)  # Default prefix list
        self.editingFinished.connect(self.update_value)
        
        
    def change_prefix_dict(self, prefix_dict: dict) -> None:
        """Change the prefix dict (on changing language).

        Args:
            prefix_dict (dict): New prefix list.
        """
        self.prefixes = prefix_dict
        self.prefix_list = list(self.prefixes.keys())
        
        
    def _convert_value_to_text(self) -> str:
        """Convert self.value to text.

        Returns:
            result_text (str): result text for display.
        """
        if self.value is None:
            return '###'
        if self.value == 0:
            return f'0 {self.unit}'
        prefix = self.prefix_list[int(np.floor(np.log10(np.abs(self.value)) / 3)) + 8]
        number = f'{self.value / self.prefixes[prefix]:3.3f}'.rstrip('0').rstrip('.')
        return f'{number} {prefix}{self.unit}'


    def update_value(self):
        """Update value in the QLineEdit. Should be called after the editing is finished.
        """
        eng_fallback = False
        text = self.text().strip().replace(',', '.').rstrip(self.unit)  # Replace , with . for decimal separator
        try:  # If it converts to float, then just leave it
            self.value = float(text)
        except Exception: 
            prefix = text.strip('-.0123456789').strip()  # Get SI prefix
            if prefix not in self.prefixes:
                if prefix in prefixes:  # Fallback to english prefixes
                    eng_fallback = True
                else:
                    self.value = None
                    self.bad_value.emit(self.text())
                    return
            try:
                number = float(text.rstrip(prefix).strip())  # Get number without the prefix
            except Exception:
                self.value = None
                self.bad_value.emit(self.text())
                return
            if eng_fallback:
                order = -int(np.log10(prefixes[prefix]))
                self.value = round(number * prefixes[prefix], order+7)  # Fixing rounding error for small values
            else:
                order = -int(np.log10(self.prefixes[prefix]))
                self.value = round(number * self.prefixes[prefix], order+7)  # Fixing rounding error for small values
        self.setText(self._convert_value_to_text())


    def set_unit(self, unit: str) -> None:
        """
        Set the QLineEdit unit (V, A, s)
        
        Args:
            unit (str): SI unit to set.
        """
        self.unit = unit
        self.setText(self._convert_value_to_text())
        
        
    def get_value(self) -> Union[float, None]:
        """Get current value as a float.

        Returns:
            value (Union[float, None]): Current value in the QLineEdit.
        """
        return self.value
    
    
    def set_value(self, value: float) -> None:
        """Set the value in the QLineEdit and update displayed text.

        Args:
            value (float): value to set.
        """
        self.value = value
        self.setText(self._convert_value_to_text())
        