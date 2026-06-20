"""tests/test_mdq_rag_boundary.py
Boundary enforcement: MDQ/RAG cross-DB access and agent-layer direct DB access.
"""

from __future__ import annotations

from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"


def _py_files(subdir: str) -> list[Path]:
    return list((SCRIPTS / subdir).rglob("*.py"))


class TestMdqRagBoundary:
    def test_mdq_layer_has_no_rag_sqlite_references(self) -> None:
        """mcp/mdq/ must not reference rag.sqlite."""
        violations = [
            str(p)
            for p in _py_files("mcp/mdq")
            if "rag.sqlite" in p.read_text(encoding="utf-8")
        ]
        assert not violations, "rag.sqlite referenced in mcp/mdq/:\n" + "\n".join(
            f"  {v}" for v in violations
        )

    def test_rag_pipeline_layer_has_no_mdq_sqlite_references(self) -> None:
        """mcp/rag_pipeline/ must not reference mdq.sqlite."""
        violations = [
            str(p)
            for p in _py_files("mcp/rag_pipeline")
            if "mdq.sqlite" in p.read_text(encoding="utf-8")
        ]
        assert not violations, (
            "mdq.sqlite referenced in mcp/rag_pipeline/:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    def test_agent_layer_rag_sqlite_access_only_in_maintenance_service(self) -> None:
        """SQLiteHelper("rag") in agent/ must only appear in rag_maintenance_service.py."""
        ALLOWED = {"rag_maintenance_service.py"}
        pattern = 'SQLiteHelper("rag")'
        violations = [
            str(p)
            for p in _py_files("agent")
            if pattern in p.read_text(encoding="utf-8") and p.name not in ALLOWED
        ]
        assert not violations, (
            f"{pattern!r} found outside allowed files:\n"
            + "\n".join(f"  {v}" for v in violations)
        )
