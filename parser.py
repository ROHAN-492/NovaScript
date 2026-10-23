# Contains the syntax analyzer / parser for NovaScript

from tokens import Token


class ASTNode:
    def __init__(self, node_type, **kwargs):
        self.node_type = node_type
        self.attributes = kwargs

    def __repr__(self):
        return self._format(0)

    def _format(self, level):
        indent = "  " * level
        result = indent + self.node_type

        for key, value in self.attributes.items():

            if isinstance(value, ASTNode):
                result += f"\n{indent}  {key}:"
                result += "\n" + value._format(level + 2)

            elif isinstance(value, list):
                result += f"\n{indent}  {key}:"
                for item in value:
                    if isinstance(item, ASTNode):
                        result += "\n" + item._format(level + 2)
                    else:
                        result += f"\n{indent}    {item}"

            else:
                result += f"\n{indent}  {key}: {value}"

        return result
    
    def __str__(self):
        return self._format(0)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    # --------------------------------------------------
    # BASIC TOKEN FUNCTIONS
    # --------------------------------------------------

    def current(self):
        return self.tokens[self.position]

    def peek(self, offset=1):
        index = self.position + offset

        if index >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[index]

    def advance(self):
        token = self.current()

        if self.position < len(self.tokens) - 1:
            self.position += 1

        return token

    def check(self, token_type, value=None):
        token = self.current()

        if token.type != token_type:
            return False

        if value is not None and token.value != value:
            return False



        return True

    def match(self, token_type, value=None):
        if self.check(token_type, value):
            return self.advance()

        return None

    def expect(self, token_type, value=None):
        token = self.current()

        if not self.check(token_type, value):

            expected = value if value is not None else token_type

            raise SyntaxError(
                f"Expected {expected} at line "
                f"{token.line}, column {token.column}, "
                f"but found '{token.value}'"
            )

        return self.advance()

    # --------------------------------------------------
    # PROGRAM
    # --------------------------------------------------

    def parse(self):
        statements = []

        while not self.check("EOF"):
            statements.append(self.parse_statement())

        return ASTNode(
            "Program",
            statements=statements
        )

    # --------------------------------------------------
    # STATEMENTS
    # --------------------------------------------------

    def parse_statement(self):

        # let statement
        if self.check("KEYWORD", "let"):
            return self.parse_variable_declaration()

        # if statement
        if self.check("KEYWORD", "if"):
            return self.parse_if_statement()

        # while statement
        if self.check("KEYWORD", "while"):
            return self.parse_while_statement()

        # function definition
        if self.check("KEYWORD", "def"):
            return self.parse_function_definition()

        # return statement
        if self.check("KEYWORD", "return"):
            return self.parse_return_statement()

        # print statement
        if self.check("KEYWORD", "print"):
            return self.parse_print_statement()

        # assignment
        if (
            self.check("IDENTIFIER")
            and self.peek().type == "OPERATOR"
            and self.peek().value == "="
        ):
            return self.parse_assignment()

        # expression statement
        expression = self.parse_expression()
        self.expect("SYMBOL", ";")

        return ASTNode(
            "ExpressionStatement",
            expression=expression
        )

    # --------------------------------------------------
    # VARIABLE DECLARATION
    # --------------------------------------------------

    def parse_variable_declaration(self):

        self.expect("KEYWORD", "let")

        name = self.expect("IDENTIFIER")

        self.expect("OPERATOR", "=")

        expression = self.parse_expression()

        self.expect("SYMBOL", ";")

        return ASTNode(
            "VariableDeclaration",
            name=name.value,
            expression=expression
        )

    # --------------------------------------------------
    # ASSIGNMENT
    # --------------------------------------------------

    def parse_assignment(self):

        name = self.expect("IDENTIFIER")

        self.expect("OPERATOR", "=")

        expression = self.parse_expression()

        self.expect("SYMBOL", ";")

        return ASTNode(
            "Assignment",
            name=name.value,
            expression=expression
        )

    # --------------------------------------------------
    # IF / ELIF / ELSE
    # --------------------------------------------------

    def parse_if_statement(self):

        self.expect("KEYWORD", "if")

        self.expect("SYMBOL", "(")

        condition = self.parse_expression()

        self.expect("SYMBOL", ")")

        body = self.parse_block()

        elif_blocks = []

        while self.match("KEYWORD", "elif"):

            self.expect("SYMBOL", "(")

            elif_condition = self.parse_expression()

            self.expect("SYMBOL", ")")

            elif_body = self.parse_block()

            elif_blocks.append(
                ASTNode(
                    "ElifBlock",
                    condition=elif_condition,
                    body=elif_body
                )
            )

        else_body = None

        if self.match("KEYWORD", "else"):
            else_body = self.parse_block()

        return ASTNode(
            "IfStatement",
            condition=condition,
            body=body,
            elif_blocks=elif_blocks,
            else_body=else_body
        )

    # --------------------------------------------------
    # WHILE
    # --------------------------------------------------

    def parse_while_statement(self):

        self.expect("KEYWORD", "while")

        self.expect("SYMBOL", "(")

        condition = self.parse_expression()

        self.expect("SYMBOL", ")")

        body = self.parse_block()

        return ASTNode(
            "WhileStatement",
            condition=condition,
            body=body
        )

    # --------------------------------------------------
    # FUNCTION DEFINITION
    # --------------------------------------------------

    def parse_function_definition(self):

        self.expect("KEYWORD", "def")

        name = self.expect("IDENTIFIER")

        self.expect("SYMBOL", "(")

        parameters = []

        if not self.check("SYMBOL", ")"):

            parameter = self.expect("IDENTIFIER")
            parameters.append(parameter.value)

            while self.match("SYMBOL", ","):
                parameter = self.expect("IDENTIFIER")
                parameters.append(parameter.value)

        self.expect("SYMBOL", ")")

        body = self.parse_block()

        return ASTNode(
            "FunctionDefinition",
            name=name.value,
            parameters=parameters,
            body=body
        )

    # --------------------------------------------------
    # RETURN
    # --------------------------------------------------

    def parse_return_statement(self):

        self.expect("KEYWORD", "return")

        expression = self.parse_expression()

        self.expect("SYMBOL", ";")

        return ASTNode(
            "ReturnStatement",
            expression=expression
        )

    # --------------------------------------------------
    # PRINT
    # --------------------------------------------------

    def parse_print_statement(self):

        self.expect("KEYWORD", "print")

        self.expect("SYMBOL", "(")

        expression = self.parse_expression()

        self.expect("SYMBOL", ")")

        self.expect("SYMBOL", ";")

        return ASTNode(
            "PrintStatement",
            expression=expression
        )

    # --------------------------------------------------
    # BLOCK
    # --------------------------------------------------

    def parse_block(self):

        self.expect("SYMBOL", "{")

        statements = []

        while not self.check("SYMBOL", "}"):

            if self.check("EOF"):
                token = self.current()

                raise SyntaxError(
                    f"Expected '}}' at line "
                    f"{token.line}, column {token.column}"
                )

            statements.append(self.parse_statement())

        self.expect("SYMBOL", "}")

        return statements

    # --------------------------------------------------
    # EXPRESSIONS
    # --------------------------------------------------

    def parse_expression(self):
        return self.parse_equality()

    # == !=
    def parse_equality(self):

        left = self.parse_comparison()

        while (
            self.check("OPERATOR", "==")
            or self.check("OPERATOR", "!=")
        ):

            operator = self.advance()

            right = self.parse_comparison()

            left = ASTNode(
                "BinaryExpression",
                operator=operator.value,
                left=left,
                right=right
            )

        return left

    # < > <= >=
    def parse_comparison(self):

        left = self.parse_term()

        while (
            self.check("OPERATOR", "<")
            or self.check("OPERATOR", ">")
            or self.check("OPERATOR", "<=")
            or self.check("OPERATOR", ">=")
        ):

            operator = self.advance()

            right = self.parse_term()

            left = ASTNode(
                "BinaryExpression",
                operator=operator.value,
                left=left,
                right=right
            )

        return left

    # + -
    def parse_term(self):

        left = self.parse_factor()

        while (
            self.check("OPERATOR", "+")
            or self.check("OPERATOR", "-")
        ):

            operator = self.advance()

            right = self.parse_factor()

            left = ASTNode(
                "BinaryExpression",
                operator=operator.value,
                left=left,
                right=right
            )

        return left

    # * /
    def parse_factor(self):

        left = self.parse_primary()

        while (
            self.check("OPERATOR", "*")
            or self.check("OPERATOR", "/")
        ):

            operator = self.advance()

            right = self.parse_primary()

            left = ASTNode(
                "BinaryExpression",
                operator=operator.value,
                left=left,
                right=right
            )

        return left

    # --------------------------------------------------
    # PRIMARY EXPRESSIONS
    # --------------------------------------------------

    def parse_primary(self):

        token = self.current()

        # Number
        if token.type == "NUMBER":

            self.advance()

            return ASTNode(
                "NumberLiteral",
                value=token.value
            )

        # String
        if token.type == "STRING":

            self.advance()

            return ASTNode(
                "StringLiteral",
                value=token.value
            )

        # Boolean
        if token.type == "KEYWORD" and token.value in {"true", "false"}:

            self.advance()

            return ASTNode(
                "BooleanLiteral",
                value=token.value
            )

        # Identifier / function call
        if token.type == "IDENTIFIER":

            self.advance()

            # Function call
            if self.match("SYMBOL", "("):

                arguments = []

                if not self.check("SYMBOL", ")"):

                    arguments.append(
                        self.parse_expression()
                    )

                    while self.match("SYMBOL", ","):
                        arguments.append(
                            self.parse_expression()
                        )

                self.expect("SYMBOL", ")")

                return ASTNode(
                    "FunctionCall",
                    name=token.value,
                    arguments=arguments
                )

            return ASTNode(
                "Identifier",
                name=token.value
            )

        # Parenthesized expression
        if self.match("SYMBOL", "("):

            expression = self.parse_expression()

            self.expect("SYMBOL", ")")

            return expression

        raise SyntaxError(
            f"Unexpected token '{token.value}' "
            f"at line {token.line}, column {token.column}"
        )