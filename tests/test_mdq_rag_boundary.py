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
        """mcp_servers/mdq/ must not reference rag.sqlite."""
        violations = [
            str(p)
            for p in _py_files("mcp_servers/mdq")
            if "rag.sqlite" in p.read_text(encoding="utf-8")
        ]
        assert not violations, (
            "rag.sqlite referenced in mcp_servers/mdq/:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    def test_rag_pipeline_layer_has_no_mdq_sqlite_references(self) -> None:
        """mcp_servers/rag_pipeline/ must not reference mdq.sqlite."""
        violations = [
            str(p)
            for p in _py_files("mcp_servers/rag_pipeline")
            if "mdq.sqlite" in p.read_text(encoding="utf-8")
        ]
        assert not violations, (
            "mdq.sqlite referenced in mcp_servers/rag_pipeline/:\n"
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

    def test_agent_layer_has_no_direct_mdq_sqlite_access(self) -> None:
        """scripts/agent/ must not access the MDQ SQLite DB or import MdqService
        directly (static string/import scan, not a runtime guarantee)."""
        violations = [
            str(p)
            for p in _py_files("agent")
            if "mdq.sqlite" in (text := p.read_text(encoding="utf-8"))
            or "from mcp_servers.mdq" in text
        ]
        assert not violations, (
            "Direct MDQ DB/import access found in scripts/agent/:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    def test_shared_layer_has_no_direct_mdq_rag_sqlite_access(self) -> None:
        """scripts/shared/ must not access the MDQ or RAG SQLite DBs directly."""
        ALLOWED: set[str] = (
            set()
        )  # empty today; add a filename here only with an inline comment explaining the reviewed exception
        forbidden = ("mdq.sqlite", "rag.sqlite", "sqlite3.connect")
        violations = [
            str(p)
            for p in _py_files("shared")
            if p.name not in ALLOWED
            and any(pattern in p.read_text(encoding="utf-8") for pattern in forbidden)
        ]
        assert not violations, (
            "Direct MDQ/RAG SQLite access found in scripts/shared/ (not in allowlist):\n"
            + "\n".join(f"  {v}" for v in violations)
        )
