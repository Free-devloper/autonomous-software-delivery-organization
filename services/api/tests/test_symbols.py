from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.indexer import (
    PythonLanguageParser,
    SymbolExtractionService,
    SymbolKind,
    TypeScriptLanguageParser,
    detect_language,
    get_language_parser,
)
from autonomous_sdo_api.policy import Role

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Python Parser Tests
# ---------------------------------------------------------------------------


def test_python_language_parser() -> None:
    code = '''"""Module docstring."""

class PaymentProcessor:
    """Processes tenant payments."""

    def __init__(self, key: str) -> None:
        self.key = key

    async def charge(self, amount: int) -> bool:
        """Charge the given amount."""
        return True

def helper_function() -> None:
    pass

def _private_func() -> None:
    pass
'''
    parser = PythonLanguageParser()
    symbols = parser.parse(code, "payment.py")

    names = [s.name for s in symbols]
    assert "PaymentProcessor" in names
    assert "__init__" in names
    assert "charge" in names
    assert "helper_function" in names
    assert "_private_func" in names

    # Check class
    cls_sym = next(s for s in symbols if s.name == "PaymentProcessor")
    assert cls_sym.kind == SymbolKind.CLASS
    assert cls_sym.docstring == "Processes tenant payments."
    assert cls_sym.is_exported is True
    assert cls_sym.qualified_name == "PaymentProcessor"

    # Check method hierarchy
    charge_sym = next(s for s in symbols if s.name == "charge")
    assert charge_sym.kind == SymbolKind.METHOD
    assert charge_sym.parent_id == cls_sym.id
    assert charge_sym.qualified_name == "PaymentProcessor.charge"
    assert charge_sym.docstring == "Charge the given amount."

    # Check private func export status
    priv_sym = next(s for s in symbols if s.name == "_private_func")
    assert priv_sym.is_exported is False
    assert priv_sym.kind == SymbolKind.FUNCTION


def test_python_language_parser_syntax_error_resilience() -> None:
    parser = PythonLanguageParser()
    symbols = parser.parse("def invalid syntax (():", "broken.py")
    assert symbols == []


# ---------------------------------------------------------------------------
# TypeScript Parser Tests
# ---------------------------------------------------------------------------


def test_typescript_language_parser() -> None:
    code = """export interface UserAccount {
  id: string;
}

export type UserId = string;

export class UserManager {
  name: string;
}

export async function getUser(): Promise<UserAccount> {
  return { id: "1" };
}

function internalHelper() {}
"""
    parser = TypeScriptLanguageParser()
    symbols = parser.parse(code, "user.ts")

    names = [s.name for s in symbols]
    assert "UserAccount" in names
    assert "UserId" in names
    assert "UserManager" in names
    assert "getUser" in names
    assert "internalHelper" in names

    iface_sym = next(s for s in symbols if s.name == "UserAccount")
    assert iface_sym.kind == SymbolKind.INTERFACE
    assert iface_sym.is_exported is True

    type_sym = next(s for s in symbols if s.name == "UserId")
    assert type_sym.kind == SymbolKind.TYPE_ALIAS
    assert type_sym.is_exported is True

    cls_sym = next(s for s in symbols if s.name == "UserManager")
    assert cls_sym.kind == SymbolKind.CLASS
    assert cls_sym.is_exported is True

    fn_sym = next(s for s in symbols if s.name == "getUser")
    assert fn_sym.kind == SymbolKind.FUNCTION
    assert fn_sym.is_exported is True

    internal_sym = next(s for s in symbols if s.name == "internalHelper")
    assert internal_sym.kind == SymbolKind.FUNCTION
    assert internal_sym.is_exported is False


# ---------------------------------------------------------------------------
# Language Detector & Service Tests
# ---------------------------------------------------------------------------


def test_detect_language() -> None:
    assert detect_language("app/main.py") == "python"
    assert detect_language("src/index.ts") == "typescript"
    assert detect_language("src/component.tsx") == "typescript"
    assert detect_language("src/util.js") == "javascript"
    assert detect_language("main.go") == "go"
    assert detect_language("Service.java") == "java"
    assert detect_language("main.rs") == "rust"
    assert detect_language("data.json") == "text"


def test_symbol_extraction_service() -> None:
    service = SymbolExtractionService()
    sha = "e" * 40

    res_py = service.extract_symbols(
        "calc.py",
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        sha,
    )
    assert res_py.commit_sha == sha
    assert res_py.language == "python"
    assert len(res_py.symbols) == 1
    assert res_py.symbols[0].name == "add"

    res_unknown = service.extract_symbols("calc.unknown", "code", sha)
    assert res_unknown.symbols == []
    assert res_unknown.language == "text"

    assert get_language_parser("unknown_lang") is None


# ---------------------------------------------------------------------------
# Symbols API Route Tests
# ---------------------------------------------------------------------------


def test_symbols_route() -> None:
    settings = Settings(service_name="asdo-symbols-test")
    app = create_app(settings=settings)
    client = TestClient(app)
    sha = "f" * 40

    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=UUID("018f0000-0000-7000-8000-000000000001"),
        actor_id="usr-symbols-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    res = client.get(
        f"/api/v1/repositories/symbols?commit_sha={sha}&file_path=services/api/src/autonomous_sdo_api/config.py"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["commit_sha"] == sha
    assert data["language"] == "python"
    symbol_names = [s["name"] for s in data["symbols"]]
    assert "Settings" in symbol_names
    assert "Environment" in symbol_names
