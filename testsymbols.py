
from symbol_table import SymbolTable

symbols = SymbolTable()

symbols.define("age", {"kind": "variable", "type": "number"})

print("Age:", symbols.lookup("age"))
print("Unknown:", symbols.lookup("marks"))

child = symbols.create_child_scope()
child.define("score", {"kind": "variable", "type": "number"})

print("Score in child:", child.lookup("score"))
print("Age from child:", child.lookup("age"))
print("Score in parent:", symbols.lookup("score"))