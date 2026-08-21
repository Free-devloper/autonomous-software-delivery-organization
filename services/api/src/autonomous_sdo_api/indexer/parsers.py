import ast
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from autonomous_sdo_api.indexer.models import CodeSymbol, SymbolKind, SymbolLocation


class LanguageParser(ABC):
    """Abstract base parser for source code symbol extraction."""

    @abstractmethod
    def parse(self, code: str, file_path: str) -> list[CodeSymbol]:
        """Extract symbols from source code."""


class PythonLanguageParser(LanguageParser):
    """AST-based symbol parser for Python files."""

    def parse(self, code: str, file_path: str) -> list[CodeSymbol]:
        try:
            tree = ast.parse(code, filename=file_path)
        except SyntaxError:
            return []

        symbols: list[CodeSymbol] = []

        def _traverse(
            node: ast.AST,
            parent_id: str | None = None,
            parent_qual: str = "",
        ) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    sym_id = f"sym_{uuid.uuid4().hex[:8]}"
                    qual_name = f"{parent_qual}.{child.name}" if parent_qual else child.name
                    loc = SymbolLocation(
                        start_line=child.lineno,
                        start_column=child.col_offset,
                        end_line=child.end_lineno or child.lineno,
                        end_column=child.end_col_offset or child.col_offset,
                    )
                    doc = ast.get_docstring(child)
                    is_exp = not child.name.startswith("_")

                    symbols.append(
                        CodeSymbol(
                            id=sym_id,
                            name=child.name,
                            qualified_name=qual_name,
                            kind=SymbolKind.CLASS,
                            location=loc,
                            docstring=doc,
                            is_exported=is_exp,
                            parent_id=parent_id,
                        )
                    )
                    _traverse(child, parent_id=sym_id, parent_qual=qual_name)

                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sym_id = f"sym_{uuid.uuid4().hex[:8]}"
                    qual_name = f"{parent_qual}.{child.name}" if parent_qual else child.name
                    loc = SymbolLocation(
                        start_line=child.lineno,
                        start_column=child.col_offset,
                        end_line=child.end_lineno or child.lineno,
                        end_column=child.end_col_offset or child.col_offset,
                    )
                    doc = ast.get_docstring(child)
                    is_exp = not child.name.startswith("_")
                    kind = SymbolKind.METHOD if parent_id else SymbolKind.FUNCTION

                    symbols.append(
                        CodeSymbol(
                            id=sym_id,
                            name=child.name,
                            qualified_name=qual_name,
                            kind=kind,
                            location=loc,
                            docstring=doc,
                            is_exported=is_exp,
                            parent_id=parent_id,
                        )
                    )
                    _traverse(child, parent_id=sym_id, parent_qual=qual_name)

        _traverse(tree)
        return symbols


class TypeScriptLanguageParser(LanguageParser):
    """Regex-based symbol extractor for TypeScript and JavaScript."""

    _FUNCTION_PATTERN = re.compile(
        r"^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(", re.MULTILINE
    )
    _CLASS_PATTERN = re.compile(
        r"^(?:export\s+)?(?:abstract\s+)?class\s+([a-zA-Z0-9_$]+)", re.MULTILINE
    )
    _INTERFACE_PATTERN = re.compile(r"^(?:export\s+)?interface\s+([a-zA-Z0-9_$]+)", re.MULTILINE)
    _TYPE_PATTERN = re.compile(r"^(?:export\s+)?type\s+([a-zA-Z0-9_$]+)\s*=", re.MULTILINE)

    def parse(self, code: str, file_path: str) -> list[CodeSymbol]:
        symbols: list[CodeSymbol] = []
        lines = code.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            is_exported = line.strip().startswith("export ")

            # Check interface
            match_iface = self._INTERFACE_PATTERN.search(line)
            if match_iface:
                name = match_iface.group(1)
                symbols.append(
                    CodeSymbol(
                        id=f"sym_{uuid.uuid4().hex[:8]}",
                        name=name,
                        qualified_name=name,
                        kind=SymbolKind.INTERFACE,
                        location=SymbolLocation(
                            start_line=line_idx,
                            start_column=0,
                            end_line=line_idx,
                            end_column=len(line),
                        ),
                        is_exported=is_exported,
                    )
                )
                continue

            # Check class
            match_class = self._CLASS_PATTERN.search(line)
            if match_class:
                name = match_class.group(1)
                symbols.append(
                    CodeSymbol(
                        id=f"sym_{uuid.uuid4().hex[:8]}",
                        name=name,
                        qualified_name=name,
                        kind=SymbolKind.CLASS,
                        location=SymbolLocation(
                            start_line=line_idx,
                            start_column=0,
                            end_line=line_idx,
                            end_column=len(line),
                        ),
                        is_exported=is_exported,
                    )
                )
                continue

            # Check function
            match_fn = self._FUNCTION_PATTERN.search(line)
            if match_fn:
                name = match_fn.group(1)
                symbols.append(
                    CodeSymbol(
                        id=f"sym_{uuid.uuid4().hex[:8]}",
                        name=name,
                        qualified_name=name,
                        kind=SymbolKind.FUNCTION,
                        location=SymbolLocation(
                            start_line=line_idx,
                            start_column=0,
                            end_line=line_idx,
                            end_column=len(line),
                        ),
                        is_exported=is_exported,
                    )
                )
                continue

            # Check type alias
            match_type = self._TYPE_PATTERN.search(line)
            if match_type:
                name = match_type.group(1)
                symbols.append(
                    CodeSymbol(
                        id=f"sym_{uuid.uuid4().hex[:8]}",
                        name=name,
                        qualified_name=name,
                        kind=SymbolKind.TYPE_ALIAS,
                        location=SymbolLocation(
                            start_line=line_idx,
                            start_column=0,
                            end_line=line_idx,
                            end_column=len(line),
                        ),
                        is_exported=is_exported,
                    )
                )

        return symbols


def detect_language(file_path: str) -> str:
    """Detect language name from file extension."""
    ext = Path(file_path).suffix.lower()
    if ext in (".py", ".pyi"):
        return "python"
    if ext in (".ts", ".tsx", ".mts", ".cts"):
        return "typescript"
    if ext in (".js", ".jsx", ".mjs", ".cjs"):
        return "javascript"
    if ext == ".go":
        return "go"
    if ext in (".java", ".kt"):
        return "java"
    if ext == ".rs":
        return "rust"
    return "text"


def get_language_parser(language: str) -> LanguageParser | None:
    """Resolve the appropriate symbol parser for a language."""
    if language == "python":
        return PythonLanguageParser()
    if language in ("typescript", "javascript"):
        return TypeScriptLanguageParser()
    return None
