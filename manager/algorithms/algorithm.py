"""Algorithm class that contains methods used in user algorithms"""
from typing import Union
import os
import json
import traceback
from copy import deepcopy

from manager.service.global_settings import TICKET_PATH


GENERATOR_FUNCTIONS = [  # Functions that generate a single ticket
    'measure_resistance',
    'send_ticket',
    'send_ticket_dict'
]

MULTI_GENERATOR_FUNCTIONS = [  # Functions that generate multiple tickets
    'send_experiment',
    'send_experiment_dict'
]

VALUE_FUNCTIONS = [  # Function that return or set values (do not yield a ticket)
    'last_resistance',
    'set_last_resistance',
    'get_ticket_dict'
]



class Algorithm:
    """Algorithm class that contains methods used in user algorithms"""
    def __init__(
        self, parent=None, 
        initial_resistance: float = 0, 
        measure_ticket_name: Union[str, None] = None,
        validate: bool = False
    ):
        """Algorithm class that implements algorithm functions; Attributes can be modified from the ApplyExp.

        Args:
            parent (gui.windows.apply.ApplyExp | None): Parent object.
            initial_resistance (float, optional): Initial resistance (self.last_res). Defaults to 0.
            measure_ticket_name (str | None, optional): Name of the measure ticket (in `MemriBoard/tickets`), 
                used in `.measure_resistance()` method. If None, defaults to `tickets/measure.json`.
            validate (bool, optional): If True, the methods are used for code validation.
        """
        self.parent = parent  # ApplyExp
        self.last_res: float = initial_resistance
        if measure_ticket_name is None:
            self.measure_ticket_name = 'measure.json'
        else:
            self.measure_ticket_name = measure_ticket_name
        self.validate = validate
        self.executed_tickets = []  # Tickets executed during a single algorithm
        
        
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
                    ticket = json.load(file)
                self._validate_ticket(ticket)
            except Exception as e:
                raise RuntimeError(f'Could not open the ticket: {type(e).__name__}: {e}')
        # Generating ticket
        with open(full_path, 'r') as file:
            ticket = json.load(file)
        self.executed_tickets.append(deepcopy(ticket))
        return ticket
    
    
    def send_ticket_dict(self, ticket: dict) -> None:
        """Send a ticket as a dict.

        Args:
            ticket (dict): Ticket to send.
            
        Returns:
            None: This function generates a ticket when the algorithm is running, 
                it **should not be used in an expression**.
        """
        if self.validate:
            if not isinstance(ticket, dict):
                raise RuntimeError(f"Wrong type for 'ticket' variable: '{type(ticket)}'. Expected type is 'dict'")            
            self._validate_ticket(ticket)
        self.executed_tickets.append(deepcopy(ticket))
        return ticket
    
    
    def measure_resistance(self) -> None:
        """Measure the resistance (send measure ticket).
        
        Returns:
            None: This function generates a ticket when the algorithm is running, 
                it **should not be used in an expression**.
        """
        return self.send_ticket(ticket_name=self.measure_ticket_name)
    
    
    def send_experiment(self, experiment_name: str, folder_path: Union[str, None] = None) -> None:
        """Send an experiment from a file (by default, from `MemriBoard/tickets`).

        Args:
            experiment_name (str): Experiment name.
            folder_path (str | None, optional): Full path to a folder containing the experiment. 
                If left `None`, default ticket folder is used (`MemriBoard/tickets`). Defaults to None.

        Returns:
            None: This function generates tickets when the algorithm is running, 
                it **should not be used in an expression**.
        """
        if self.validate:  # Variable validation
            if not isinstance(experiment_name, str):
                raise RuntimeError(f"Wrong type for 'experiment_name' variable: '{type(experiment_name)}'. Expected type is 'str'")
            if not (isinstance(folder_path, str) or folder_path is None):
                raise RuntimeError(f"Wrong type for 'folder_path' variable: '{type(folder_path)}'. Expected type is 'str' or 'None'") 
        if folder_path is None:
            full_path = os.path.join(TICKET_PATH, self._add_json_to_path(experiment_name))
        else:
            full_path = os.path.join(folder_path, self._add_json_to_path(experiment_name))
        if self.validate:  # Ticket validation
            if not os.path.exists(full_path):
                raise RuntimeError(f"Experiment does not exist! Path: '{full_path}'")
            try:
                with open(full_path, 'r') as file:
                    experiment = json.load(file)
                    for i, ticket in experiment.items():
                        self._validate_ticket(ticket)
                    return experiment_name, experiment
            except Exception as e:
                raise RuntimeError(f'Could not open the ticket number {i}: {type(e).__name__}: {e}')
        # Generating tickets
        with open(full_path, 'r') as file:
            experiment = json.load(file)
        self.executed_tickets.append(deepcopy(experiment))
        return [ticket for ticket in experiment.values()]
    
    
    def send_experiment_dict(self, experiment: dict) -> None:
        """Send an experiment as a dict in format {'number': ticket}.

        Args:
            experiment (dict): Experiment to send.

        Returns:
            None: This function generates tickets when the algorithm is running, 
                it **should not be used in an expression**.
        """
        if self.validate:
            if not isinstance(experiment, dict):
                raise RuntimeError(f"Wrong type for 'experiment' variable: '{type(experiment)}'. Expected type is 'dict'")
            for i, ticket in experiment.items():
                if not isinstance(ticket, dict):
                    raise RuntimeError(f"Wrong type for ticket number {i}: '{type(ticket)}'. Expected type is 'dict'")  # noqa: TRY004
                self._validate_ticket(ticket)
            return 'dict_experiment', experiment
        self.executed_tickets.append(deepcopy(experiment))
        return [ticket for ticket in experiment.values()]
    
    
    def get_ticket_dict(self, filename: str, folder_path: Union[str, None] = None) -> dict:
        """Get ticket or experiment dict in the algorithm code.

        Args:
            filename (str): Filename of the ticket or experiment json.
            folder_path (str | None, optional): Full path to a folder containing the ticket or experiment. 
                If left `None`, default ticket folder is used (`MemriBoard/tickets`). Defaults to None.

        Returns:
            dict: Ticket or experiment.
        """
        if self.validate:  # Variable validation
            if not isinstance(filename, str):
                raise RuntimeError(f"Wrong type for 'filename' variable: '{type(filename)}'. Expected type is 'str'")
            if not (isinstance(folder_path, str) or folder_path is None):
                raise RuntimeError(f"Wrong type for 'folder_path' variable: '{type(folder_path)}'. Expected type is 'str' or 'None'") 
        if folder_path is None:
            full_path = os.path.join(TICKET_PATH, self._add_json_to_path(filename))
        else:
            full_path = os.path.join(folder_path, self._add_json_to_path(filename))
        if self.validate:  # Ticket validation
            if not os.path.exists(full_path):
                raise RuntimeError(f"File does not exist! Path: '{full_path}'")
            try:
                with open(full_path, 'r') as file:
                    ticket = json.load(file)
            except Exception as e:
                raise RuntimeError(f'Could not open the .json file: {type(e).__name__}: {e}')
            return filename, ticket
        # Returning the ticket
        with open(full_path, 'r') as file:
            ticket = json.load(file)
        return ticket
    
        
    def _validate_ticket(self, ticket: dict) -> None:
        """Validate a ticket. If something is wrong, an exception is risen.

        Args:
            ticket (dict): Ticket to validate.
        """
        if 'mode' not in ticket:
            raise RuntimeError("Ticket should have 'mode' key!")
        if 'params' not in ticket:
            raise RuntimeError("Ticket should have 'params' key!")
        if 'terminate' not in ticket:
            raise RuntimeError("Ticket should have 'terminate' key!")
        if self.parent is not None:
            # Trying to yield tasks
            # TODO: rewrite for VISA merge
            try:
                for _ in self.parent.parent.parent.man.menu[ticket['mode']](ticket['params'], ticket['terminate'], self.parent.parent.parent.man.blank_type):
                    pass
            except Exception:
                raise RuntimeError('Could not yield tasks from ticket! Error occurred:\n', traceback.format_exc())
    
    
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
    
    
    def reset_executed_tickets(self) -> None:
        """Reset list of tickets executed during algorithm"""
        self.executed_tickets = []
        
        
    def get_executed_tickets(self) -> list[dict]:
        """Get a list of executed tickets"""
        return self.executed_tickets
        