"""Ticket generator that supports algorithms"""
from typing import Generator

from manager.algorithms import algorithm_generator, Algorithm



user_alg = """def user_algorithm():
    measure_resistance()
    print('LAST_RES:', last_resistance())
    if last_resistance() > 50:
        send_ticket('iv-curve')
    else:
        send_ticket('measure')
"""


def ticket_generator(ticket_list: list, algorithm: Algorithm) -> Generator[list, None, None]:
    """Ticket generator that supports algorithms.

    Args:
        ticket_list (list): Ticket list (`MainWindow.exp_list`).
        algorithm (Algorithm): Algorithm instance for the ticket sequence.

    Yields:
        Generator[list, None, None]: Ticket generator.
    """
    # for ticket in ticket_list:
    #     if ticket[0] == 'algorithm':
    #         yield from algorithm_generator(user_alg)
    #     else:
    #         yield ticket
    yield from algorithm_generator(user_alg, algorithm=algorithm)  # ticket_name, ticket, count, Algorithm
    