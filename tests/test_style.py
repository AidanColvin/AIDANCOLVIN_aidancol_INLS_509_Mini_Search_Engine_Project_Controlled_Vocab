"""Enforces the house style rules on every Python file under src/ and tests/."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANNED_DIRS = ("src", "tests")
SHADOWED_BUILTINS = frozenset({"dir", "id", "list", "type", "input", "file"})
BROAD_EXCEPTIONS = frozenset({"Exception", "BaseException"})
IMPLICIT_FIRST_PARAMS = frozenset({"self", "cls"})
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def list_python_files(root: Path, scanned_dirs: tuple[str, ...]) -> list[Path]:
    """
    Takes the repository root and the names of the directories to scan.
    Collects every .py file under those directories in sorted path order.
    Gives the list of paths, empty when no Python files exist there.
    """
    found: list[Path] = []
    for dir_name in scanned_dirs:
        found.extend(sorted((root / dir_name).rglob("*.py")))
    return found


def read_source(path: Path) -> str:
    """
    Takes a path to a Python source file.
    Reads the file as UTF-8 text without interpreting it.
    Gives the source text, or raises FileNotFoundError when the path is missing.
    """
    return path.read_text(encoding="utf-8")


def parse_source(source: str, filename: str) -> ast.Module:
    """
    Takes Python source text and the filename to report in errors.
    Parses the text into an abstract syntax tree.
    Gives the module node, or raises SyntaxError when the text is not valid Python.
    """
    return ast.parse(source, filename=filename)


def method_ids(tree: ast.Module) -> frozenset[int]:
    """
    Takes a parsed module.
    Collects the identity of every function defined directly inside a class body.
    Gives a frozenset of node ids, empty when the module has no methods.
    """
    ids: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                ids.add(id(child))
    return frozenset(ids)


def iter_functions(tree: ast.Module) -> list[tuple[FunctionNode, bool]]:
    """
    Takes a parsed module.
    Walks every function definition at any nesting depth and marks the methods.
    Gives a list of (function node, is_method) pairs, empty when there are no functions.
    """
    methods = method_ids(tree)
    return [
        (node, id(node) in methods)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def docstring_lines(node: FunctionNode) -> list[str]:
    """
    Takes a function node.
    Splits its docstring into stripped non-empty lines.
    Gives the list of lines, empty when the function has no docstring.
    """
    text = ast.get_docstring(node)
    if text is None:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def docstring_violations(node: FunctionNode, filename: str) -> list[str]:
    """
    Takes a function node and its filename.
    Checks that the docstring has exactly three lines starting with Takes and ending with Gives.
    Gives the list of violation messages, empty when the docstring conforms.
    """
    where = f"{filename}:{node.lineno} {node.name}"
    lines = docstring_lines(node)
    if len(lines) != 3:
        return [f"{where}: docstring must have exactly three non-empty lines, found {len(lines)}"]
    problems: list[str] = []
    if not lines[0].startswith("Takes"):
        problems.append(f"{where}: docstring line 1 must start with 'Takes'")
    if not lines[2].startswith("Gives"):
        problems.append(f"{where}: docstring line 3 must start with 'Gives'")
    return problems


def parameter_nodes(node: FunctionNode) -> list[ast.arg]:
    """
    Takes a function node.
    Gathers every parameter node in signature order, including *args and **kwargs.
    Gives the list of parameter nodes, empty for a function with no parameters.
    """
    params = [*node.args.posonlyargs, *node.args.args]
    if node.args.vararg is not None:
        params.append(node.args.vararg)
    params.extend(node.args.kwonlyargs)
    if node.args.kwarg is not None:
        params.append(node.args.kwarg)
    return params


def annotation_violations(node: FunctionNode, is_method: bool, filename: str) -> list[str]:
    """
    Takes a function node, whether it is a method, and its filename.
    Checks that every parameter and the return value carry a type hint.
    Gives the list of violation messages, empty when every hint is present.
    """
    where = f"{filename}:{node.lineno} {node.name}"
    problems: list[str] = []
    for index, param in enumerate(parameter_nodes(node)):
        if index == 0 and is_method and param.arg in IMPLICIT_FIRST_PARAMS:
            continue
        if param.annotation is None:
            problems.append(f"{where}: parameter '{param.arg}' lacks a type hint")
    if node.returns is None:
        problems.append(f"{where}: missing return type hint")
    return problems


def shadowing_violations(node: FunctionNode, filename: str) -> list[str]:
    """
    Takes a function node and its filename.
    Checks that no parameter name shadows a protected builtin.
    Gives the list of violation messages, empty when no parameter shadows one.
    """
    where = f"{filename}:{node.lineno} {node.name}"
    return [
        f"{where}: parameter '{param.arg}' shadows a builtin"
        for param in parameter_nodes(node)
        if param.arg in SHADOWED_BUILTINS
    ]


def exception_names(expr: ast.expr) -> set[str]:
    """
    Takes the expression of an except clause.
    Extracts the plain names of the exception classes it catches.
    Gives the set of names, empty when the expression is not a name, attribute, or tuple.
    """
    if isinstance(expr, ast.Name):
        return {expr.id}
    if isinstance(expr, ast.Attribute):
        return {expr.attr}
    if isinstance(expr, ast.Tuple):
        names: set[str] = set()
        for element in expr.elts:
            names |= exception_names(element)
        return names
    return set()


def except_violations(tree: ast.Module, filename: str) -> list[str]:
    """
    Takes a parsed module and its filename.
    Checks every except clause for a bare form or a catch of Exception.
    Gives the list of violation messages, empty when every clause is specific.
    """
    problems: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        where = f"{filename}:{node.lineno}"
        if node.type is None:
            problems.append(f"{where}: bare except is not allowed")
            continue
        broad = exception_names(node.type) & BROAD_EXCEPTIONS
        if broad:
            problems.append(f"{where}: catching {', '.join(sorted(broad))} is not allowed")
    return problems


def module_violations(tree: ast.Module, filename: str) -> list[str]:
    """
    Takes a parsed module and its filename.
    Runs every style check over the module's functions and except clauses.
    Gives the combined list of violation messages, empty when the module conforms.
    """
    problems: list[str] = []
    for node, is_method in iter_functions(tree):
        problems.extend(docstring_violations(node, filename))
        problems.extend(annotation_violations(node, is_method, filename))
        problems.extend(shadowing_violations(node, filename))
    problems.extend(except_violations(tree, filename))
    return problems


def file_violations(path: Path, root: Path) -> list[str]:
    """
    Takes a Python file path and the repository root.
    Reads, parses, and checks the file against every style rule.
    Gives the list of violation messages, empty when the file conforms.
    """
    filename = str(path.relative_to(root))
    tree = parse_source(read_source(path), filename)
    return module_violations(tree, filename)


def test_every_function_follows_house_style() -> None:
    """
    Takes no arguments.
    Checks every Python file under src/ and tests/ for docstring, hint, shadowing, and except rules.
    Gives nothing, or fails with every violation listed.
    """
    files = list_python_files(ROOT, SCANNED_DIRS)
    assert files, "no Python files found to check"
    problems = [problem for path in files for problem in file_violations(path, ROOT)]
    assert not problems, "\n" + "\n".join(problems)


def test_docstring_lines_handles_missing_docstring() -> None:
    """
    Takes no arguments.
    Parses a function with no docstring and reads its docstring lines.
    Gives nothing, or fails if the result is not an empty list.
    """
    tree = parse_source("def f(x: int) -> int:\n    return x\n", "<test>")
    node = tree.body[0]
    assert isinstance(node, ast.FunctionDef)
    assert docstring_lines(node) == []


def test_docstring_violations_reports_wrong_line_count() -> None:
    """
    Takes no arguments.
    Checks a function whose docstring has two lines.
    Gives nothing, or fails if no violation is reported.
    """
    source = 'def f(x: int) -> int:\n    """\n    Takes x.\n    Gives x.\n    """\n    return x\n'
    node = parse_source(source, "<test>").body[0]
    assert isinstance(node, ast.FunctionDef)
    assert docstring_violations(node, "<test>")


def test_annotation_violations_allows_self_on_methods() -> None:
    """
    Takes no arguments.
    Checks a method whose only unannotated parameter is self.
    Gives nothing, or fails if a violation is reported for self.
    """
    source = 'class A:\n    def m(self, x: int) -> int:\n        """\n        Takes x.\n        Returns x.\n        Gives x.\n        """\n        return x\n'
    tree = parse_source(source, "<test>")
    functions = iter_functions(tree)
    assert len(functions) == 1
    node, is_method = functions[0]
    assert is_method
    assert annotation_violations(node, is_method, "<test>") == []


def test_except_violations_flags_bare_and_broad() -> None:
    """
    Takes no arguments.
    Checks a module with a bare except and a catch of Exception.
    Gives nothing, or fails if fewer than two violations are reported.
    """
    source = "try:\n    pass\nexcept:\n    pass\ntry:\n    pass\nexcept Exception:\n    pass\n"
    assert len(except_violations(parse_source(source, "<test>"), "<test>")) == 2


def test_exception_names_handles_unknown_expression() -> None:
    """
    Takes no arguments.
    Extracts exception names from a call expression, which is not a name, attribute, or tuple.
    Gives nothing, or fails if the result is not an empty set.
    """
    expr = ast.parse("f()", mode="eval").body
    assert exception_names(expr) == set()


def test_list_python_files_empty_for_missing_dir(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Lists Python files under a directory name that does not exist there.
    Gives nothing, or fails if the result is not an empty list.
    """
    assert list_python_files(tmp_path, ("nothing_here",)) == []
