"""tests/test_db_public_api.py

Tests for the db package public API:
- __all__ exists in db.store and db.__init__
- Every symbol in __all__ is actually importable
- Wildcard imports work without error
"""

from __future__ import annotations

import importlib
import sys

import pytest


@pytest.fixture()
def _reload_db():
    """Reload modules to avoid stale __all__ from previous test runs."""
    for mod in ("db", "db.store"):
        if mod in sys.modules:
            del sys.modules[mod]
    yield importlib.import_module("db.store"), importlib.import_module("db")


def test_store_all_exists(_reload_db):
    store, _ = _reload_db
    assert hasattr(store, "__all__"), "db.store.__all__ does not exist"


def test_db_all_exists(_reload_db):
    _, db_mod = _reload_db
    assert hasattr(db_mod, "__all__"), "db.__all__ does not exist"


def test_store_all_symbols_exist(_reload_db):
    store, _ = _reload_db
    for name in store.__all__:
        assert hasattr(store, name), (
            f"{name!r} is listed in db.store.__all__ but not found on the module"
        )


def test_db_all_symbols_exist(_reload_db):
    _, db_mod = _reload_db
    for name in db_mod.__all__:
        assert hasattr(db_mod, name), (
            f"{name!r} is listed in db.__all__ but not found on the module"
        )


def test_store_wildcard_import_works():
    """from db.store import * should not raise."""
    # Create a fresh namespace and import * from db.store
    ns: dict = {}
    exec("from db.store import *", ns)  # noqa: S102
    # If the exec succeeds without ImportError, the wildcard import works.


def test_db_wildcard_import_works():
    """from db import * should not raise."""
    ns: dict = {}
    exec("from db import *", ns)  # noqa: S102
