"""Ticket generator that supports algorithms"""
from typing import Generator

from manager.algorithms import algorithm_generator



user_alg = """def user_algorithm():
    measure_resistance()
    print('LAST_RES:', last_resistance())
    if last_resistance() > 50:
        send_ticket(100)
    else:
        send_ticket(200)
"""


def ticket_generator(ticket_list: list, initial_resistance: float = 0) -> Generator[list, None, None]:
    """Ticket generator that supports algorithms.

    Args:
        ticket_list (list): Ticket list (`MainWindow.exp_list`).
        initial_resistance (float, optional): Initial resistance (from the database). Defaults to 0.

    Yields:
        Generator[list, None, None]: Ticket generator.
    """
    # for ticket in ticket_list:
    #     if ticket[0] == 'algorithm':
    #         yield from algorithm_generator(user_alg)
    #     else:
    #         yield ticket
    yield from algorithm_generator(user_alg, initial_resistance=initial_resistance)  # ticket_name, ticket, count, Algorithm
    