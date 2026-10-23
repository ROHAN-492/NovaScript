
from symbol_table import SymbolTable


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.inside_function = False

    def define_symbol(self, name, info):
        try:
            self.current_scope.define(name, info)
        except RuntimeError as error:
            raise SemanticError(str(error)) from error

    def require_symbol(self, name):
        symbol = self.current_scope.lookup(name)

        if symbol is None:
            raise SemanticError(
                f"'{name}' is used but has not been declared"
            )

        return symbol

    def analyze(self):
        self.visit(self.ast)
        return self.global_scope

    def visit(self, node):
        if isinstance(node, list):
            for statement in node:
                self.visit(statement)
            return

        if node is None:
            return

        kind = node.node_type
        attrs = node.attributes

        if kind == "Program":
            self.visit(attrs["statements"])

        elif kind == "VariableDeclaration":
            # Check the initializer before declaring the new variable.
            self.visit(attrs["expression"])
            self.define_symbol(
                attrs["name"],
                {"kind": "variable"}
            )

        elif kind == "Assignment":
            symbol = self.require_symbol(attrs["name"])

            if symbol["kind"] != "variable":
                raise SemanticError(
                    f"'{attrs['name']}' is not a variable"
                )

            self.visit(attrs["expression"])

        elif kind == "Identifier":
            symbol = self.require_symbol(attrs["name"])

            if symbol["kind"] != "variable":
                raise SemanticError(
                    f"Function '{attrs['name']}' cannot be used "
                    "as a variable"
                )

        elif kind == "BinaryExpression":
            self.visit(attrs["left"])
            self.visit(attrs["right"])

        elif kind in {
            "NumberLiteral",
            "StringLiteral",
            "BooleanLiteral"
        }:
            pass

        elif kind == "FunctionDefinition":
            name = attrs["name"]
            parameters = attrs["parameters"]

            self.define_symbol(
                name,
                {
                    "kind": "function",
                    "parameters": parameters
                }
            )

            previous_scope = self.current_scope
            previous_function_state = self.inside_function

            self.current_scope = previous_scope.create_child_scope()
            self.inside_function = True

            try:
                for parameter in parameters:
                    self.define_symbol(
                        parameter,
                        {"kind": "variable"}
                    )

                self.visit(attrs["body"])

            finally:
                self.current_scope = previous_scope
                self.inside_function = previous_function_state

        elif kind == "FunctionCall":
            function = self.require_symbol(attrs["name"])

            if function["kind"] != "function":
                raise SemanticError(
                    f"'{attrs['name']}' is not a function"
                )

            arguments = attrs["arguments"]
            expected = len(function["parameters"])
            received = len(arguments)

            if expected != received:
                raise SemanticError(
                    f"Function '{attrs['name']}' expects "
                    f"{expected} argument(s), but got {received}"
                )

            for argument in arguments:
                self.visit(argument)

        elif kind == "PrintStatement":
            self.visit(attrs["expression"])

        elif kind == "ExpressionStatement":
            self.visit(attrs["expression"])

        elif kind == "IfStatement":
            self.visit(attrs["condition"])

            previous_scope = self.current_scope
            self.current_scope = previous_scope.create_child_scope()

            try:
                self.visit(attrs["body"])

                for block in attrs["elif_blocks"]:
                    self.visit(block.attributes["condition"])
                    self.visit(block.attributes["body"])

                self.visit(attrs["else_body"])

            finally:
                self.current_scope = previous_scope

        elif kind == "WhileStatement":
            self.visit(attrs["condition"])

            previous_scope = self.current_scope
            self.current_scope = previous_scope.create_child_scope()

            try:
                self.visit(attrs["body"])
            finally:
                self.current_scope = previous_scope

        elif kind == "ReturnStatement":
            if not self.inside_function:
                raise SemanticError(
                    "'return' can only be used inside a function"
                )

            self.visit(attrs["expression"])

        else:
            raise SemanticError(
                f"Semantic analyzer does not support node '{kind}' yet"
            )