
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, name, symbol_info):
        if name in self.symbols:
            raise RuntimeError(
                f"Semantic error: '{name}' is already declared in this scope"
            )

        self.symbols[name] = symbol_info

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]

        if self.parent is not None:
            return self.parent.lookup(name)

        return None

    def create_child_scope(self):
        return SymbolTable(parent=self)