"""Ticket generator that supports algorithms"""
from logging import Logger

from manager.algorithms import algorithm_generator, Algorithm
from manager.model.db import DBOperate

            
            
class TicketGenerator:
    """Ticket generator that supports algorithms. Also handles adding ticket to the database"""
    def __init__(self, parent, ticket_list: list, algorithm: Algorithm, db: DBOperate, experiment_id: int, ap_logger: Logger) -> None:
        """Ticket generator that supports algorithms.

        Args:
            parent (ApplyExp): ApplyExp object.
            ticket_list (list): Ticket list (`MainWindow.exp_list`).
            algorithm (Algorithm): Algorithm instance for the ticket sequence.
            db (manager.model.DBOperate): Database for adding ticket entries.
            experiment_id (int): Experiment id for adding ticket to the database.
            ap_logger (logging.Logger): Logger for writing exceptions.

        Yields:
            Generator[list, None, None]: Ticket generator.
        """
        self.parent = parent
        self.ticket_list = ticket_list
        self.algorithm = algorithm
        self.db = db
        self.experiment_id = experiment_id
        self.ap_logger = ap_logger
        self.ticket_id = None
        
        
    def __iter__(self):
        """Ticket iteration"""
        for ticket in self.ticket_list:
            self.add_ticket_to_database(ticket[1])
            if ticket[1]['mode'] == 'algorithm':  # Algorithm: generate multiple tickets
                self.algorithm.reset_executed_tickets()
                yield from algorithm_generator(ticket[1]['code'], algorithm=self.algorithm)
                self.add_executed_tickets_to_db()  # TODO: finish
            else:
                yield ticket[1]
                
                
    def add_ticket_to_database(self, ticket: dict) -> None:
        """Add a ticket to the database

        Args:
            ticket (dict): Ticket.
        """
        status, self.ticket_id = self.db.add_ticket(ticket, self.experiment_id)
        if not status:
            self.ap_logger.critical(self.parent.lang_pack.get('err_ticket_add_to_db'))
            
            
    def get_ticket_id(self) -> int:
        """Get current ticket id in the database.

        Returns:
            int: ticket id.
        """
        if self.ticket_id is None:
            raise RuntimeError('Ticket id was asked before it was changed from None')
        return self.ticket_id
    
    
    def add_executed_tickets_to_db(self) -> None:
        """Add a list of tickets executed during the algorithm to the database
        
        Args:
            executed_tickets (list): List of executed tickets.
        """
        #tickets = self.algorithm.get_executed_tickets()
        # TODO add to database
    