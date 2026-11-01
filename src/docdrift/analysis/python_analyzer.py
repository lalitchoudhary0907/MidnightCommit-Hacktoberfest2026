"""
Python source-code analyzer for DocDrift.

Extracts modules, constants, classes, functions and methods using AST.
"""

import ast
import hashlib
from pathlib import Path
from typing import Any

from docdrift.errors import CodeAnalysisError
from docdrift.models import CodeFact, Location


def _source(node: ast.AST | None) -> str | None:
    """Return source representation of an AST node."""
    return ast.unparse(node) if node is not None else None


def _value(node: ast.AST | None) -> Any:
    """Return a literal value when possible, otherwise source text."""
    if node is None:
        return None

    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return ast.unparse(node)


def _target_names(target: ast.AST) -> list[str]:
    """Extract variable names from assignment targets."""
    if isinstance(target, ast.Name):
        return [target.id]

    if isinstance(target, (ast.Tuple, ast.List)):
        names = []
        for element in target.elts:
            names.extend(_target_names(element))
        return names

    return []


class _PythonFactCollector:
    """Collect structured code facts from a Python AST."""

    def __init__(self, path: str):
        self.path = path
        self.facts: list[CodeFact] = []

    def add(
        self,
        kind: str,
        name: str,
        owner: str,
        node: ast.AST,
        value: Any,
        metadata: dict | None = None,
    ) -> None:
        line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", line)
        qualified_name = f"{owner}.{name}" if owner else name

        identifier = (
            f"{self.path}\0{kind}\0{qualified_name}\0{line}"
        )
        fact_id = hashlib.sha256(
            identifier.encode("utf-8")
        ).hexdigest()[:20]

        fact_metadata = {
            "qualified_name": qualified_name,
            **(metadata or {}),
        }

        self.facts.append(
            CodeFact(
                fact_id=f"py-{fact_id}",
                kind=kind,
                name=name,
                value=value,
                owner=owner,
                location=Location(
                    path=self.path,
                    line=line,
                    end_line=end_line,
                ),
                language="python",
                metadata=fact_metadata,
            )
        )

    def visit_assignment(
        self,
        node: ast.Assign | ast.AnnAssign,
        owner: str,
        scope_kind: str,
    ) -> None:
        if scope_kind not in ("module", "class"):
            return

        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value_node = node.value
        annotation = (
            _source(node.annotation)
            if isinstance(node, ast.AnnAssign)
            else None
        )

        for target in targets:
            for name in _target_names(target):
                if scope_kind == "module" and not name.isupper():
                    continue

                kind = "constant" if scope_kind == "module" else "attribute"

                self.add(
                    kind=kind,
                    name=name,
                    owner=owner,
                    node=node,
                    value=_value(value_node),
                    metadata={"annotation": annotation}
                    if annotation else {},
                )

    def nested_bodies(self, node: ast.AST) -> list[list[ast.stmt]]:
        """Find nested control-flow blocks without crossing scopes."""
        bodies = []

        for attribute in ("body", "orelse", "finalbody"):
            body = getattr(node, attribute, None)
            if isinstance(body, list) and body:
                bodies.append(body)

        for handler in getattr(node, "handlers", []):
            if handler.body:
                bodies.append(handler.body)

        for case in getattr(node, "cases", []):
            if case.body:
                bodies.append(case.body)

        return bodies

    def visit_scope(
        self,
        statements: list[ast.stmt],
        owner: str = "",
        scope_kind: str = "module",
    ) -> None:
        for node in statements:

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "method" if scope_kind == "class" else "function"
                qualified_name = (
                    f"{owner}.{node.name}" if owner else node.name
                )

                self.add(
                    kind=kind,
                    name=node.name,
                    owner=owner,
                    node=node,
                    value={
                        "signature": f"({ast.unparse(node.args)})",
                        "return_annotation": _source(node.returns),
                        "docstring": ast.get_docstring(node),
                        "decorators": [
                            ast.unparse(item) for item in node.decorator_list
                        ],
                    },
                    metadata={
                        "qualified_name": qualified_name,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                    },
                )

                self.visit_scope(
                    node.body,
                    owner=qualified_name,
                    scope_kind="function",
                )

            elif isinstance(node, ast.ClassDef):
                qualified_name = (
                    f"{owner}.{node.name}" if owner else node.name
                )

                self.add(
                    kind="class",
                    name=node.name,
                    owner=owner,
                    node=node,
                    value={
                        "bases": [ast.unparse(base) for base in node.bases],
                        "docstring": ast.get_docstring(node),
                        "decorators": [
                            ast.unparse(item) for item in node.decorator_list
                        ],
                    },
                )

                self.visit_scope(
                    node.body,
                    owner=qualified_name,
                    scope_kind="class",
                )

            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                self.visit_assignment(node, owner, scope_kind)

            else:
                for body in self.nested_bodies(node):
                    self.visit_scope(body, owner, scope_kind)

    def collect(self, tree: ast.Module) -> list[CodeFact]:
        module_docstring = ast.get_docstring(tree)

        if module_docstring and tree.body:
            module_name = (
                "module"
                if self.path == "<memory>"
                else Path(self.path).stem
            )

            self.add(
                kind="module",
                name=module_name,
                owner="",
                node=tree.body[0],
                value=module_docstring,
            )

        self.visit_scope(tree.body)

        return sorted(
            self.facts,
            key=lambda fact: (
                fact.location.line,
                fact.location.end_line,
                fact.kind,
                fact.name,
            ),
        )


def analyze_python_source(
    source: str,
    path: str = "<memory>",
) -> list[CodeFact]:
    """
    Analyze Python source text and return extracted CodeFact objects.

    Extracts:
        - Module docstrings
        - Module-level uppercase constants
        - Classes and their bases
        - Class attributes
        - Functions and methods
        - Signatures, annotations, decorators and docstrings

    Raises:
        CodeAnalysisError: If the source is invalid Python.
    """
    if not isinstance(source, str):
        raise CodeAnalysisError("Python source must be a string.")

    try:
        tree = ast.parse(source, filename=str(path), type_comments=True)
    except (SyntaxError, ValueError) as exc:
        line = getattr(exc, "lineno", None)
        location = f" at line {line}" if line else ""

        raise CodeAnalysisError(
            f"Unable to parse Python source '{path}'{location}: {exc}"
        ) from exc

    return _PythonFactCollector(str(path)).collect(tree)


def analyze_python_file(path: str | Path) -> list[CodeFact]:
    """
    Analyze a Python file from disk.

    Raises:
        CodeAnalysisError: If the file cannot be read or parsed.
    """
    file_path = Path(path)

    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CodeAnalysisError(
            f"Unable to read Python file '{file_path}': {exc}"
        ) from exc

    return analyze_python_source(source, str(file_path))


__all__ = ["analyze_python_source", "analyze_python_file"]
