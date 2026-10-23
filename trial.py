
# Runs lexical, syntax, and semantic analysis

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer, SemanticError
from impact_analyzer import VariableImpactAnalyzer

def main():

    with open("examples/test.nova", "r") as file:
        source_code = file.read()

    # -------------------------------
    # LEXICAL ANALYSIS
    # -------------------------------

    lexer = Lexer(source_code)

    try:
        tokens = lexer.tokenize()

        print("\n===== NOVASCRIPT TOKEN STREAM =====\n")

        for token in tokens:
            print(token)

    except RuntimeError as error:
        print("\nLEXICAL ERROR:")
        print(error)
        return

    # -------------------------------
    # SYNTAX ANALYSIS
    # -------------------------------

    parser = Parser(tokens)

    try:
        ast = parser.parse()

        print("\n===== NOVASCRIPT SYNTAX ANALYSIS =====\n")
        print("Syntax analysis successful!")

        print("\n===== NOVASCRIPT AST =====\n")
        print(ast)

    except SyntaxError as error:
        print("\nSYNTAX ERROR:")
        print(error)
        return

    # -------------------------------
    # SEMANTIC ANALYSIS
    # -------------------------------

    print("\n===== NOVASCRIPT SEMANTIC ANALYSIS =====\n")

    try:
        analyzer = SemanticAnalyzer(ast)
        analyzer.analyze()

        print("Semantic analysis successful!")

    except SemanticError as error:
        print("SEMANTIC ERROR:")
        print(error)

    print("\n===== NOVASCRIPT VARIABLE DEPENDENCY & IMPACT FLOW =====\n")
    impact_analyzer = VariableImpactAnalyzer(ast)
    impact_analyzer.analyze()
    print(impact_analyzer.report())


if __name__ == "__main__":
    main()