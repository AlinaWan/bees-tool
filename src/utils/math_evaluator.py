import ast
import operator as op
from typing import final as sealed

@sealed
class MathEvaluator:

    _OPERATORS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
        ast.UAdd: op.pos,
        ast.USub: op.neg,
    }

    def __init__(self, variables=None):
        self._variables = variables or {}

    def _eval(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers allowed")

        if isinstance(node, ast.Name):
            if node.id in self._variables:
                return self._variables[node.id]
            raise ValueError(f"Unknown variable: {node.id}")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._OPERATORS:
                raise ValueError("Operator not allowed")

            return self._OPERATORS[op_type](
                self._eval(node.left),
                self._eval(node.right),
            )

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._OPERATORS:
                raise ValueError("Unary operator not allowed")

            return self._OPERATORS[op_type](self._eval(node.operand))

        raise ValueError("Unsupported expression")

    def evaluate(self, expression):
        if isinstance(expression, (int, float)):
            return expression

        if not isinstance(expression, str):
            return 0

        try:
            tree = ast.parse(expression, mode="eval")
            return self._eval(tree.body)
        except Exception:
            return 0
