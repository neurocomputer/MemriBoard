"""Ticket generator for algorithms"""
import ast
import traceback
import inspect
from typing import Union
from collections.abc import Generator

from manager.algorithms import Algorithm
from manager.main import Manager
from manager.algorithms.algorithm import GENERATOR_FUNCTIONS, MULTI_GENERATOR_FUNCTIONS, VALUE_FUNCTIONS



def check_algorithm_code(algorithm_code: str, get_used_tickets: bool = False) -> tuple[bool, str]:
    """Check if algorithm code can be compiled.

    Args:
        algorithm_code (str): Algorithm code.
        get_used_tickets (bool): If True, validator creates a dict with tickets used in the experiment.

    Returns:
        status, result, tickets (tuple[bool, str, dict | None]]): Status: if True, algorithm compiles fine.
            result: Transformed generator or errors if occurred. tickets: tickets used in the experiment.
    """
    try:
        tree = ast.parse(algorithm_code)
    except Exception:
        return False, traceback.format_exc(), None
    # Adding parents
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent
    try:      
        # Validating code
        validator = CodeValidator(get_used_tickets=get_used_tickets)
        validator.visit(tree)
        if not validator.found_algorithm:
            return False, 'The code should define the algorithm() function!', None
        if len(validator.errors) > 0:
            return False, '\n'.join(validator.errors), None
        # Transforming generator statements
        new_tree = GeneratorTransformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        # Getting tickets used in the experiment
        if get_used_tickets:
            used_tickets = validator.used_tickets
        else:
            used_tickets = None
        return True, ast.unparse(new_tree), used_tickets
    except Exception:
        return False, traceback.format_exc(), None


def algorithm_generator(algorithm_code: str, algorithm: Algorithm) -> Generator[list, None, None]:
    """Ticket generator for algorithms.

    Args:
        algorithm_code (str): Algorithm code.
        algorithm (Algorithm): Algorithm instance for the ticket sequence.

    Yields:
        Generator[list, None, None]: Ticket generator.
    """
    status, result, _ = check_algorithm_code(algorithm_code)
    if not status:
        raise RuntimeError(f'Could not create a generator from code! Algorithm:\n{algorithm_code}\n{result}')
    tree = ast.parse(result)
    # Creating namespace based on Algorithm methods
    namespace = {}
    for name, method in inspect.getmembers(algorithm, inspect.ismethod):
        if name in GENERATOR_FUNCTIONS or name in VALUE_FUNCTIONS or name in MULTI_GENERATOR_FUNCTIONS:
            namespace[name] = method
    # Creating generator
    compiled = compile(tree, '<algorithm>', 'exec')
    exec(compiled, namespace)
    yield from namespace['algorithm']()
    
    
def execute_algorithm(algorithm_code: str, manager: Manager) -> tuple[bool, Union[int, str]]:
    """Execute an algorithm to check if it can be compiled and get its count.

    Args:
        algorithm_code (str): Algorithm code.

    Returns:
        status, result (tuple[bool, int|str): If status is True, the algorithm executed correctly;
            result is the algorithm task count. If status is False, there was an error, result is 
            the error message.
    """
    try:
        tree = ast.parse(algorithm_code)
        new_tree = GeneratorTransformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        # Creating namespace based on Algorithm methods
        alg = Algorithm()
        namespace = {}
        for name, method in inspect.getmembers(alg, inspect.ismethod):
            if name in GENERATOR_FUNCTIONS or name in VALUE_FUNCTIONS or name in MULTI_GENERATOR_FUNCTIONS:
                namespace[name] = method
        # Creating generator
        compiled = compile(new_tree, '<algorithm>', 'exec')
        exec(compiled, namespace)
        count = 0
        for ticket in namespace['algorithm']():
            task_gen = manager.menu[ticket['mode']]
            for _ in task_gen(ticket['params'], ticket['terminate'], manager.blank_type):
                count += 1
        return True, count
    except Exception:
        return False, traceback.format_exc()

class CodeValidator(ast.NodeVisitor):
    """Validator for the algorithm"""
    def __init__(self, get_used_tickets: bool = False):
        """Code validator.

        Args:
            get_used_tickets (bool, optional): If True, validator gets tickets used in the 
                experiment. Defaults to False.
        """
        self.errors = []
        self.found_algorithm = False
        self.get_used_tickets = get_used_tickets
        self.used_tickets = {}
    
    def error(self, node: ast.Expr, message:str):
        """Add an error to error queue.

        Args:
            node (ast.Expr): Node where an error occurred.
            message (str): Message to user
        """
        self.errors.append(f'Line {node.lineno}: {message}')
        
    # Forbidden code
    def visit_AsyncFunctionDef(self, node):
        self.error(node, 'Async is forbidden')
        
    def visit_Await(self, node):
        self.error(node, 'Async is forbidden')
        
    def visit_AsyncFor(self, node):
        self.error(node, 'Async is forbidden')
        
    def visit_AsyncWith(self, node):
        self.error(node, 'Async is forbidden')
        
    def visit_Call(self, node):
        """Semantic check for generator function calls"""
        self.generic_visit(node)
        if isinstance(node.func, ast.Name):
            if node.func.id in GENERATOR_FUNCTIONS or node.func.id in MULTI_GENERATOR_FUNCTIONS:
                # Checking if the generator is expected to return values
                if isinstance(node.parent, (ast.Assign, ast.Call, ast.If, ast.BinOp)):
                    self.error(node, f'{node.func.id}() does not return a value')  
                if not isinstance(node.parent, ast.Expr):
                    self.error(node, f'{node.func.id} cannot be transformed to a generator in this expression')
                # Checking if the function can be executed
                try:
                    alg = Algorithm(parent=None, validate=True)
                    method = getattr(alg, node.func.id)
                    args, kwargs = [], {}
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            return
                        args.append(arg.value)
                    for keyword in node.keywords:
                        if isinstance(keyword.value, ast.Name):
                            return
                        kwargs[keyword.arg] = keyword.value.value
                    result = method(*args, **kwargs)  # Trying to execute
                    if self.get_used_tickets:
                        if node.func.id in GENERATOR_FUNCTIONS:
                            # result is a ticket
                            if result['mode'] == 'algorithm':  # Checking if ticket is not an algorithm
                                self.error(node, 'An algorithm can not call another algorithm!')
                            self.used_tickets[result['name']] = result
                        if node.func.id in MULTI_GENERATOR_FUNCTIONS:
                            name, experiment = result
                            for i, ticket in experiment.items():  # Checking if ticket is not an algorithm
                                if ticket['mode'] == 'algorithm':
                                    self.error(node, f'Ticket {i} is an algorithm, an algorithm can not call another algorithm!')
                            if name == 'dict_experiment':
                                if 'dict_experiment' in self.used_tickets:  # Experiment sent from dict, it has no name
                                    flag = True
                                    i = 0
                                    while flag:
                                        i += 1
                                        if f'dict_experiment_{i}' not in self.used_tickets:
                                            flag = False
                                    self.used_tickets[f'dict_experiment{i}'] = experiment
                                else:
                                    self.used_tickets['dict_experiment'] = experiment
                            else:  # Save experiment by its name
                                self.used_tickets[name] = experiment
                except RuntimeError as e:
                    self.error(node, e)
                except Exception:
                    self.error(node, traceback.format_exc())
            elif node.func.id == 'get_ticket_dict':
                try:
                    alg = Algorithm(parent=None, validate=True)
                    method = getattr(alg, node.func.id)
                    args, kwargs = [], {}
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            return
                        args.append(arg.value)
                    for keyword in node.keywords:
                        if isinstance(keyword.value, ast.Name):
                            return
                        kwargs[keyword.arg] = keyword.value.value
                    name, ticket = method(*args, **kwargs)  # Trying to execute
                    if self.get_used_tickets:
                        if 'mode' in ticket:
                            if ticket['mode'] == 'algorithm':  # Checking if ticket is not an algorithm
                                self.error(node, 'An algorithm can not call another algorithm!')
                        else:  # Its an experiment
                            for i, tick in ticket.items():
                                if tick['mode'] == 'algorithm':
                                    self.error(node, f'Ticket {i}: An algorithm can not call another algorithm!')
                        self.used_tickets[name] = ticket
                except RuntimeError as e:
                    self.error(node, e)
                except Exception:
                    self.error(node, traceback.format_exc())
                
    def visit_FunctionDef(self, node):
        """Searching for algorithm() function"""
        self.generic_visit(node)
        if node.name == 'algorithm':
            self.found_algorithm = True
            if len(node.args.args) != 0:
               self.error(node, 'algorithm() should not have any parameters')
    


class GeneratorTransformer(ast.NodeTransformer):
    """Transformer that replaces functions with generators"""
    def visit_Expr(self, node):
        """Visit a node"""
        self.generic_visit(node)
        # Replacing generator_function() with yield from generator_function()
        if (isinstance(node.value, ast.Call) and 
            isinstance(node.value.func, ast.Name)):
                if node.value.func.id in GENERATOR_FUNCTIONS:
                    return ast.Expr(value=ast.Yield(value=node.value))
                if node.value.func.id in MULTI_GENERATOR_FUNCTIONS:
                    return ast.Expr(value=ast.YieldFrom(value=node.value))
        return node
             