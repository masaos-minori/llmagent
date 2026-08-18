"""tests/test_maintenance_boundaries.py
AST-based boundary tests verifying db/maintenance.py has no rag layer imports.
"""

from __future__ import annotations

import ast
from pathlib import Path

DB_MAINTENANCE = Path("scripts/db/maintenance.py")


def _get_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


class TestMaintenanceBoundaries:
    def test_db_maintenance_has_no_rag_imports(self) -> None:
        """db/maintenance.py must not import from rag layer after extraction."""
        imports = _get_imports(DB_MAINTENANCE)
        rag_imports = [i for i in imports if i.startswith("rag")]
        assert rag_imports == [], (
            f"db/maintenance.py imports rag modules: {rag_imports}"
        )

    def test_rotate_rag_db_removed_from_db_maintenance(self) -> None:
        """rotate_rag_db() must not exist in db/maintenance.py after move."""
        source = DB_MAINTENANCE.read_text()
        assert "rotate_rag_db" not in source, (
            "rotate_rag_db still present in db/maintenance.py"
        )
