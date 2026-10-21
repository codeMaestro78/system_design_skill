"""Guard the declared Python floor.

The package declares support for Python 3.9. Two things break that at run
time rather than at import time: syntax newer than 3.9, and PEP 604 unions
used in a position that is evaluated eagerly. The latter is easy to miss,
because a file without ``from __future__ import annotations`` evaluates
``dict | None`` when the function is defined, and the error only appears on
the older interpreter.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 9)


def python_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.py")
        if ".git" not in path.parts and "__pycache__" not in path.parts
    )


def annotation_nodes(tree: ast.AST) -> list[ast.expr]:
    """Return every annotation that Python evaluates eagerly.

    Function annotations are evaluated when the definition is executed unless
    the module opted into postponed evaluation, so they count. Local variable
    annotations are never evaluated, so they do not.
    """
    found: list[ast.expr] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = node.args
            for argument in (
                list(arguments.posonlyargs)
                + list(arguments.args)
                + list(arguments.kwonlyargs)
            ):
                if argument.annotation is not None:
                    found.append(argument.annotation)
            if arguments.vararg is not None and arguments.vararg.annotation is not None:
                found.append(arguments.vararg.annotation)
            if arguments.kwarg is not None and arguments.kwarg.annotation is not None:
                found.append(arguments.kwarg.annotation)
            if node.returns is not None:
                found.append(node.returns)
        elif isinstance(node, ast.AnnAssign):
            # A module or class level annotation is evaluated; a function local
            # one is not. Distinguish by scope.
            if isinstance(node.target, ast.Name):
                found.append(node.annotation)
    return found


def has_postponed_evaluation(tree: ast.AST) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )


class PythonFloorTests(unittest.TestCase):
    def test_repository_has_python_files(self):
        self.assertTrue(python_files(), "no Python files found")

    def test_every_file_parses_under_the_declared_floor(self):
        for path in python_files():
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                ast.parse(source, feature_version=MIN_PYTHON)

    def test_no_match_statement(self):
        """``match`` is 3.10 and cannot be parsed under the declared floor.

        ``ast.Match`` only exists from 3.10, so on an older interpreter a
        match statement cannot even be parsed and this check has nothing to
        look for.
        """
        match_node = getattr(ast, "Match", None)
        if match_node is None:
            self.skipTest("ast.Match is unavailable before Python 3.10")
        for path in python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            with self.subTest(path=path.name):
                self.assertEqual(
                    [],
                    [node for node in ast.walk(tree) if isinstance(node, match_node)],
                    "match statements need Python 3.10",
                )

    def test_no_eagerly_evaluated_pep604_unions(self):
        """``X | Y`` fails at definition time without postponed evaluation."""
        for path in python_files():
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            if has_postponed_evaluation(tree):
                continue
            for annotation in annotation_nodes(tree):
                for node in ast.walk(annotation):
                    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                        self.fail(
                            f"{path.name} uses a PEP 604 union in an eagerly evaluated "
                            "annotation; add `from __future__ import annotations`"
                        )


if __name__ == "__main__":
    unittest.main()
