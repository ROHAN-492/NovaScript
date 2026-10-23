"""Static variable dependency and impact analysis for NovaScript.

This module consumes NovaScript's existing AST. It does not execute the source
program; it builds a conservative, syntax-based dependency graph.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass
class VariableInfo:
    key: str
    name: str
    scope_path: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    outputs: Set[str] = field(default_factory=set)

    @property
    def display_name(self) -> str:
        if self.scope_path == "global":
            return self.name
        return f"{self.name} [{self.scope_path}]"


class _Scope:
    def __init__(self, path: str, parent: Optional["_Scope"] = None):
        self.path = path
        self.parent = parent
        self.symbols: Dict[str, str] = {}

    def resolve(self, name: str) -> Optional[str]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.resolve(name)
        return None


class VariableImpactAnalyzer:
    """Build a variable-to-variable dependency graph from a NovaScript AST."""

    def __init__(self, ast):
        self.ast = ast
        self.variables: Dict[str, VariableInfo] = {}
        self._scope_counters: Dict[str, int] = {}

    def analyze(self) -> Dict[str, VariableInfo]:
        self.variables.clear()
        self._scope_counters.clear()
        global_scope = _Scope("global")
        self._visit(self.ast, global_scope, frozenset(), None)
        return self.variables

    def _new_child_scope(self, parent: _Scope, kind: str) -> _Scope:
        count = self._scope_counters.get(kind, 0) + 1
        self._scope_counters[kind] = count
        label = f"{kind} {count}"
        return _Scope(f"{parent.path}/{label}", parent)

    def _declare(self, name: str, scope: _Scope) -> str:
        key = f"{scope.path}::{name}"
        # Semantic analysis should already have rejected duplicate declarations.
        # Reuse the existing record defensively if the analyzer is called alone.
        if name in scope.symbols:
            return scope.symbols[name]
        scope.symbols[name] = key
        self.variables[key] = VariableInfo(key=key, name=name, scope_path=scope.path)
        return key

    def _resolve_identifier(self, name: str, scope: _Scope) -> Optional[str]:
        key = scope.resolve(name)
        if key is not None and key not in self.variables:
            # This should not normally occur after successful semantic analysis,
            # but avoid crashing if the impact analyzer is run independently.
            return None
        return key

    def _add_dependencies(self, target_key: str, source_keys: Iterable[str]) -> None:
        target = self.variables.get(target_key)
        if target is None:
            return
        for source_key in source_keys:
            source = self.variables.get(source_key)
            if source is None:
                continue
            target.dependencies.add(source_key)
            source.dependents.add(target_key)

    def _expression_variables(self, node, scope: _Scope) -> Set[str]:
        """Return variables referenced by an expression, including call arguments."""
        result: Set[str] = set()
        if node is None:
            return result
        kind = getattr(node, "node_type", None)
        attrs = getattr(node, "attributes", {})

        if kind == "Identifier":
            key = self._resolve_identifier(attrs.get("name", ""), scope)
            if key is not None:
                result.add(key)
        elif kind == "BinaryExpression":
            result.update(self._expression_variables(attrs.get("left"), scope))
            result.update(self._expression_variables(attrs.get("right"), scope))
        elif kind == "FunctionCall":
            for argument in attrs.get("arguments", []):
                result.update(self._expression_variables(argument, scope))
        else:
            # Literals carry no variable dependencies.
            # This fallback also makes the analyzer tolerant of future expression
            # nodes that store child AST nodes in their attributes.
            for value in attrs.values():
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, "node_type"):
                            result.update(self._expression_variables(item, scope))
                elif hasattr(value, "node_type"):
                    result.update(self._expression_variables(value, scope))
        return result

    def _expression_label(self, node) -> str:
        if node is None:
            return "<empty expression>"
        kind = getattr(node, "node_type", None)
        attrs = getattr(node, "attributes", {})
        if kind == "Identifier":
            return str(attrs.get("name", "?"))
        if kind in {"NumberLiteral", "StringLiteral", "BooleanLiteral"}:
            return str(attrs.get("value", "?"))
        if kind == "BinaryExpression":
            left = self._expression_label(attrs.get("left"))
            right = self._expression_label(attrs.get("right"))
            operator = attrs.get("operator", "?")
            return f"({left} {operator} {right})"
        if kind == "FunctionCall":
            args = ", ".join(self._expression_label(arg) for arg in attrs.get("arguments", []))
            return f"{attrs.get('name', '?')}({args})"
        return kind or "expression"

    def _attach_output(self, source_keys: Iterable[str], output: str) -> None:
        for key in source_keys:
            info = self.variables.get(key)
            if info is not None:
                info.outputs.add(output)

    def _visit(self, node, scope: _Scope, control_dependencies: frozenset,
               function_name: Optional[str]) -> None:
        if node is None:
            return
        if isinstance(node, list):
            for item in node:
                self._visit(item, scope, control_dependencies, function_name)
            return

        kind = getattr(node, "node_type", None)
        attrs = getattr(node, "attributes", {})

        if kind == "Program":
            self._visit(attrs.get("statements", []), scope, control_dependencies, function_name)

        elif kind == "VariableDeclaration":
            expression = attrs.get("expression")
            sources = self._expression_variables(expression, scope)
            sources.update(control_dependencies)
            target_key = self._declare(attrs.get("name", "?"), scope)
            self._add_dependencies(target_key, sources)

        elif kind == "Assignment":
            name = attrs.get("name", "?")
            target_key = self._resolve_identifier(name, scope)
            sources = self._expression_variables(attrs.get("expression"), scope)
            sources.update(control_dependencies)
            if target_key is not None:
                self._add_dependencies(target_key, sources)

        elif kind == "PrintStatement":
            expression = attrs.get("expression")
            label = f"print({self._expression_label(expression)})"
            sources = self._expression_variables(expression, scope)
            sources.update(control_dependencies)
            self._attach_output(sources, label)

        elif kind == "ReturnStatement":
            expression = attrs.get("expression")
            label = f"return from {function_name}" if function_name else "return value"
            sources = self._expression_variables(expression, scope)
            sources.update(control_dependencies)
            self._attach_output(sources, label)

        elif kind == "ExpressionStatement":
            expression = attrs.get("expression")
            if getattr(expression, "node_type", None) == "FunctionCall":
                label = f"call {self._expression_label(expression)}"
                sources = self._expression_variables(expression, scope)
                sources.update(control_dependencies)
                self._attach_output(sources, label)
            else:
                self._visit(expression, scope, control_dependencies, function_name)

        elif kind == "IfStatement":
            condition = attrs.get("condition")
            condition_vars = self._expression_variables(condition, scope)
            self._attach_output(condition_vars, f"controls if ({self._expression_label(condition)})")

            branch_scope = self._new_child_scope(scope, "if block")
            self._visit(attrs.get("body", []), branch_scope,
                        frozenset(set(control_dependencies) | condition_vars), function_name)

            all_condition_vars = set(condition_vars)
            for block in attrs.get("elif_blocks", []):
                block_attrs = getattr(block, "attributes", {})
                elif_condition = block_attrs.get("condition")
                elif_vars = self._expression_variables(elif_condition, scope)
                self._attach_output(elif_vars, f"controls elif ({self._expression_label(elif_condition)})")
                combined = all_condition_vars | elif_vars | set(control_dependencies)
                elif_scope = self._new_child_scope(scope, "elif block")
                self._visit(block_attrs.get("body", []), elif_scope, frozenset(combined), function_name)
                all_condition_vars.update(elif_vars)

            else_body = attrs.get("else_body")
            if else_body is not None:
                else_scope = self._new_child_scope(scope, "else block")
                self._visit(else_body, else_scope,
                            frozenset(set(control_dependencies) | all_condition_vars), function_name)

        elif kind == "WhileStatement":
            condition = attrs.get("condition")
            condition_vars = self._expression_variables(condition, scope)
            self._attach_output(condition_vars, f"controls while ({self._expression_label(condition)})")
            loop_scope = self._new_child_scope(scope, "while block")
            self._visit(attrs.get("body", []), loop_scope,
                        frozenset(set(control_dependencies) | condition_vars), function_name)

        elif kind == "FunctionDefinition":
            name = attrs.get("name", "function")
            function_scope = self._new_child_scope(scope, f"function {name}")
            for parameter in attrs.get("parameters", []):
                self._declare(parameter, function_scope)
            self._visit(attrs.get("body", []), function_scope, frozenset(), name)

        elif kind == "FunctionCall":
            # A stand-alone call is handled by ExpressionStatement. Calls used
            # inside expressions contribute dependencies from their arguments.
            return

        elif kind in {"Identifier", "NumberLiteral", "StringLiteral", "BooleanLiteral"}:
            return

        elif kind == "BinaryExpression":
            return

        else:
            raise ValueError(f"Impact analyzer does not support AST node '{kind}'")

    def report(self, max_paths: int = 20) -> str:
        """Create a report for every variable, including downstream impact paths."""
        if not self.variables:
            return "No variables were found in the program."

        ordered = sorted(self.variables.values(), key=lambda item: (item.scope_path, item.name))
        lines: List[str] = []
        for number, variable in enumerate(ordered, start=1):
            lines.append(f"{number}. VARIABLE: {variable.display_name}")

            if variable.dependencies:
                names = sorted(self.variables[key].display_name for key in variable.dependencies if key in self.variables)
                lines.append("   Direct dependencies: " + ", ".join(names))
            else:
                lines.append("   Direct dependencies: None")

            if variable.dependents:
                names = sorted(self.variables[key].display_name for key in variable.dependents if key in self.variables)
                lines.append("   Directly affects: " + ", ".join(names))
            else:
                lines.append("   Directly affects: None")

            paths = self._impact_paths(variable.key, max_paths)
            if paths:
                lines.append("   Impact flow:")
                for path in paths:
                    lines.append("     " + path)
            else:
                lines.append("   Impact flow: No downstream variables or output statements found")
            lines.append("")
        return "\n".join(lines)

    def _impact_paths(self, start_key: str, max_paths: int) -> List[str]:
        paths: List[str] = []

        def walk(current_key: str, chain: List[str], visited: Set[str]) -> None:
            if len(paths) >= max_paths:
                return
            current = self.variables.get(current_key)
            if current is None:
                return
            for output in sorted(current.outputs):
                if len(paths) < max_paths:
                    paths.append(" -> ".join(chain + [output]))
            for child_key in sorted(current.dependents):
                if child_key in visited:
                    continue
                child = self.variables.get(child_key)
                if child is None:
                    continue
                walk(child_key, chain + [child.display_name], visited | {child_key})

        start = self.variables.get(start_key)
        if start is not None:
            walk(start_key, [start.display_name], {start_key})
        return paths
