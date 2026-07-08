"""Ticket generator for algorithms"""
import ast
import traceback
import inspect
from typing import Generator

from manager.algorithms import Algorithm
from manager.algorithms.algorithm import GENERATOR_FUNCTIONS, VALUE_FUNCTIONS



def check_algorithm_code(algorithm_code: str) -> tuple[bool, str]:
    """Check if algorithm code can be compiled.

    Args:
        algorithm_code (str): Algorithm code.

    Returns:
        status, result (tuple[bool, str]]): Status: if True, algorithm compiles fine.
            result: Transformed generator or errors if occurred.
    """
    try:
        tree = ast.parse(algorithm_code)
    except Exception:
        return False, traceback.format_exc()
        
    # Adding parents
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent
    try:      
        # Validating code
        validator = CodeValidator()
        validator.visit(tree)
        if len(validator.errors) > 0:
            return False, 'Error(s) occurred:\n' + '\n'.join(validator.errors)
        # Transforming generator statements
        new_tree = GeneratorTransformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return True, new_tree
    except Exception:
        return False, traceback.format_exc()


def algorithm_generator(algorithm_code: str, initial_resistance: float = 0) -> Generator[list, None, None]:
    """Ticket generator for algorithms.

    Args:
        algorithm_code (str): Algorithm code.
        initial_resistance (float, optional): Initial resistance (from the database). Defaults to 0.

    Yields:
        Generator[list, None, None]: Ticket generator.
    """
    print('CHECKING')
    status, result = check_algorithm_code(algorithm_code)
    print('CHECKING DONE:', status, result)
    if not status:
        raise RuntimeError(f'Could not create a generator from code! Algorithm:\n{algorithm_code}\nError:{result}')
    tree = ast.parse(result)
    # Creating namespace based on Algorithm methods
    alg = Algorithm(initial_resistance=initial_resistance)
    namespace = {}
    for name, method in inspect.getmembers(alg, inspect.ismethod):
        if name in GENERATOR_FUNCTIONS or name in VALUE_FUNCTIONS:
            namespace[name] = method
    # Creating generator
    compiled = compile(tree, '<algorithm>', 'exec')
    exec(compiled, namespace)
    yield from namespace['user_algorithm']()


class CodeValidator(ast.NodeVisitor):
    """Validator for the algorithm"""
    def __init__(self):
        self.errors = []
    
    
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
        
    # Semantic check
    def visit_Call(self, node):
        self.generic_visit(node)
        if (isinstance(node.func, ast.Name) and 
            node.func.id in GENERATOR_FUNCTIONS):
            # Checking if the generator is expected to return values
            if isinstance(node.parent, (ast.Assign, ast.Call, ast.If, ast.BinOp)):
                self.error(node, f'{node.func.id}() does not return a value')  
            if not isinstance(node.parent, ast.Expr):
                self.error(node, f'{node.func.id} cannot be transformed to a generator in this expression')    
    


class GeneratorTransformer(ast.NodeTransformer):
    """Transformer that replaces functions with generators"""
    def visit_Expr(self, node):
        """Visit a node"""
        self.generic_visit(node)
        # Replacing generator_function() with yield from generator_function()
        if (isinstance(node.value, ast.Call) and 
            isinstance(node.value.func, ast.Name) and 
            node.value.func.id in GENERATOR_FUNCTIONS):
            return ast.Expr(value=ast.Yield(value=node.value))
        return node
    