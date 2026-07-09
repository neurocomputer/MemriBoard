"""Algorithm class that contains methods used in user algorithms"""
from typing import Union
import os
import json

from manager.service.global_settings import TICKET_PATH


GENERATOR_FUNCTIONS = [  # Functions that generate tickets
    'measure_resistance',
    'send_ticket'
]

VALUE_FUNCTIONS = [  # Function that return or set values (do not yield a ticket)
    'last_resistance',
    'set_last_resistance'
]


example_ticket = ('iv-curve', {'name': 'iv-curve', 'mode': 'std', 'params': {'v_dir_strt_inc': 0, 'v_dir_stop_inc': 1392, 'v_dir_step_inc': 41, 't_dir_msec_inc': 0, 't_dir_usec_inc': 100, 'dir_inc_countr': 1, 'v_dir_strt_dec': 1392, 'v_dir_stop_dec': 0, 'v_dir_step_dec': 41, 't_dir_msec_dec': 0, 't_dir_usec_dec': 100, 'dir_dec_countr': 1, 'v_rev_strt_inc': 0, 'v_rev_stop_inc': 1392, 'v_rev_step_inc': 41, 't_rev_msec_inc': 0, 't_rev_usec_inc': 100, 'rev_inc_countr': 1, 'v_rev_strt_dec': 1392, 'v_rev_stop_dec': 0, 'v_rev_step_dec': 41, 't_rev_msec_dec': 0, 't_rev_usec_dec': 100, 'rev_dec_countr': 1, 'count': 1, 'reverse': 0, 'id': 0, 'wl': 0, 'bl': 0}, 'terminate': {'type': 'pass', 'value': 0}}, 140)
class Algorithm:
    """Algorithm class that contains methods used in user algorithms"""
    def __init__(self, parent=None, initial_resistance: float = 0, validate: bool = False):
        """Algorithm class that implements algorithm functions; Attributes can be modified from the ApplyExp.

        Args:
            parent (gui.windows.apply.ApplyExp | None): Parent object.
            initial_resistance (float, optional): Initial resistance (self.last_res). Defaults to 0.
            validate (bool, optional): If True, the methods are used for code validation.
        """
        self.parent = parent  # ApplyExp
        self.validate = validate
        self.last_res: float = initial_resistance
        self.need_db_resistance: bool = False
        
        
    def last_resistance(self) -> float:
        """Get last measured resistance.

        Returns:
            resistance (float): Last measured resistance.
        """
        return self.last_res
    
    
    def set_last_resistance(self, resistance: float) -> None:
        """Set last measured resistance

        Args:
            resistance (float): resistance value.
        """
        self.last_res = resistance
        
        
    def send_ticket(self, ticket_name: str, folder_path: Union[str, None] = None) -> None:
        """Send a ticket from a file (by default, from `MemriBoard/tickets`).

        Args:
            ticket_name (str): Ticket name.
            folder_path (str | None, optional): Full path to a folder containing ticket. 
                If left `None`, default ticket folder is used (`MemriBoard/tickets`). Defaults to None.

        Returns:
            None: This function generates a ticket when the algorithm is running, 
                it **should not be used in an expression**.
        """
        if self.validate:  # Variable validation
            if not isinstance(ticket_name, str):
                raise RuntimeError(f"Wrong type for 'ticket_name' variable: '{type(ticket_name)}'. Expected type is 'str'")
            if not (isinstance(folder_path, str) or folder_path is None):
                raise RuntimeError(f"Wrong type for 'folder_path' variable: '{type(folder_path)}'. Expected type is 'str' or 'None'") 
        if folder_path is None:
            full_path = os.path.join(TICKET_PATH, self._add_json_to_path(ticket_name))
        else:
            full_path = os.path.join(folder_path, self._add_json_to_path(ticket_name))
        if self.validate:  # Ticket validation
            if not os.path.exists(full_path):
                raise RuntimeError(f"Ticket does not exist! Path: '{full_path}'")
            try:
                with open(full_path, 'r') as file:
                    json.load(file)
            except Exception as e:
                raise RuntimeError(f'Could not open the ticket: {type(e).__name__}: {e}')
        # Generating ticket
        return example_ticket
        # ticket = example_ticket[1]
        # ticket['params']['v_dir_stop_inc'] = voltage
        # return (example_ticket[0], ticket, example_ticket[2], self)
        # print('Executing!', ticket_name)
    
    
    def measure_resistance(self) -> None:
        """Measure the resistance"""
        return example_ticket
    
    
    def _add_json_to_path(self, path: str) -> str:
        """Add `.json` to ticket path.

        Args:
            path (str): Ticket path.

        Returns:
            str: Ticket path with .json at the end.
        """
        if path.lower().endswith('.json'):
            return path
        return path + '.json'
        