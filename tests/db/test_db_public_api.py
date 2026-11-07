"""tests/test_db_public_api.py

Tests for the db package public API:
- __all__ exists in db.__init__
- Every symbol in __all__ is actually importable
- Wildcard imports work without error
"""

from __future__ import annotations

import importlib
import sys

import pytest


@pytest.fixture()
def _reload_db():
    """Reload the db module to avoid stale __all__ from previous test runs."""
    # Save originals before evicting — the freshly created db module will NOT have
    # submodule attributes (e.g. .recovery, .helper) because Python's import cache
    # returns cached submodules without calling setattr() on the new parent module.
    # We must restore the originals after yield to avoid contaminating later tests.
    saved = {mod: sys.modules[mod] for mod in ("db",) if mod in sys.modules}
    for mod in ("db",):
        if mod in sys.modules:
            del sys.modules[mod]
    yield importlib.import_module("db")
    # Restore originals
    for mod in ("db",):
        if mod in sys.modules:
            del sys.modules[mod]
    sys.modules.update(saved)


def test_db_all_exists(_reload_db):
    db_mod = _reload_db
    assert hasattr(db_mod, "__all__"), "db.__all__ does not exist"


def test_db_all_symbols_exist(_reload_db):
    db_mod = _reload_db
    for name in db_mod.__all__:
        assert hasattr(db_mod, name), (
            f"{name!r} is listed in db.__all__ but not found on the module"
        )


def test_db_wildcard_import_works():
    """from db import * should not raise."""
    ns: dict = {}
    exec("from db import *", ns)  # noqa: S102
