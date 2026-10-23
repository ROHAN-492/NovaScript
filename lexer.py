#Contains actual lexical analyzer :
from tokens import Token


class Lexer:
    KEYWORDS = {
        "let",
        "if",
        "elif",
        "else",
        "while",
        "def",
        "return",
        "print",
        "true",
        "false"
    }

    TWO_CHAR_OPERATORS = {
        "==",
        "!=",
        "<=",
        ">="
    }

    ONE_CHAR_OPERATORS = {
        "+",
        "-",
        "*",
        "/",
        "=",
        "<",
        ">"
    }

    SYMBOLS = {
        "(",
        ")",
        "{",
        "}",
        ",",
        ";"
    }

    def __init__(self, source):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def advance(self):
        char = self.source[self.position]
        self.position += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def peek(self, offset=0):
        index = self.position + offset

        if index >= len(self.source):
            return "\0"

        return self.source[index]

    def skip_whitespace(self):
        while self.peek() in " \t\r\n":
            self.advance()

    def read_identifier(self):
        start_line = self.line
        start_column = self.column

        value = ""

        while self.peek().isalnum() or self.peek() == "_":
            value += self.advance()

        if value in self.KEYWORDS:
            token_type = "KEYWORD"
        else:
            token_type = "IDENTIFIER"

        return Token(
            token_type,
            value,
            start_line,
            start_column
        )

    def read_number(self):
        start_line = self.line
        start_column = self.column

        value = ""

        while self.peek().isdigit():
            value += self.advance()

        # Check for decimal part
        if self.peek() == "." and self.peek(1).isdigit():
            value += self.advance()

            while self.peek().isdigit():
                value += self.advance()

        return Token(
            "NUMBER",
            value,
            start_line,
            start_column
        )

    def read_string(self):
        start_line = self.line
        start_column = self.column

        # Consume opening quote
        self.advance()

        value = ""

        while self.peek() != '"' and self.peek() != "\0":
            value += self.advance()

        if self.peek() == "\0":
            raise RuntimeError(
                f"Unterminated string at line {start_line}, "
                f"column {start_column}"
            )

        # Consume closing quote
        self.advance()

        return Token(
            "STRING",
            value,
            start_line,
            start_column
        )

    def tokenize(self):
        tokens = []

        while self.position < len(self.source):

            self.skip_whitespace()

            if self.position >= len(self.source):
                break

            char = self.peek()

            # Identifier or keyword
            if char.isalpha() or char == "_":
                tokens.append(self.read_identifier())
                continue

            # Number
            if char.isdigit():
                tokens.append(self.read_number())
                continue

            # String
            if char == '"':
                tokens.append(self.read_string())
                continue

            # Two-character operators
            two_char = char + self.peek(1)

            if two_char in self.TWO_CHAR_OPERATORS:
                line = self.line
                column = self.column

                self.advance()
                self.advance()

                tokens.append(
                    Token(
                        "OPERATOR",
                        two_char,
                        line,
                        column
                    )
                )

                continue

            # One-character operators
            if char in self.ONE_CHAR_OPERATORS:
                line = self.line
                column = self.column

                self.advance()

                tokens.append(
                    Token(
                        "OPERATOR",
                        char,
                        line,
                        column
                    )
                )

                continue

            # Symbols / delimiters
            if char in self.SYMBOLS:
                line = self.line
                column = self.column

                self.advance()

                tokens.append(
                    Token(
                        "SYMBOL",
                        char,
                        line,
                        column
                    )
                )

                continue

            # Unknown character
            raise RuntimeError(
                f"Unexpected character '{char}' "
                f"at line {self.line}, column {self.column}"
            )

        # End of file token
        tokens.append(
            Token(
                "EOF",
                "",
                self.line,
                self.column
            )
        )

        return tokens