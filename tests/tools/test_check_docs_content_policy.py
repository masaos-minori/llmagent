"""tests/tools/test_check_docs_content_policy.py

Unit tests for tools/check_docs_content_policy.py's detection logic — one test
per remove-category, plus one confirming no false positive on
retain-category-only content.
"""

from __future__ import annotations

from pathlib import Path

from tools.check_docs_content_policy import (
    DocFile,
    check_full_file_tree,
    check_index_table,
    check_literal_port_number,
    check_location_mapping,
    check_per_file_description,
)


def _doc(text: str, rel_path: str = "fixture.md") -> DocFile:
    return DocFile(path=Path(rel_path), rel_path=rel_path, lines=text.splitlines())


def test_full_file_tree_detected() -> None:
    doc = _doc("## File Structure\n├─ rag-src/\n│   └─ chunk/\n└─ sqlite-vec/\n")
    issues = check_full_file_tree([doc])
    assert len(issues) >= 1
    assert all(i.severity == "WARNING" for i in issues)
    assert all("full file tree" in i.message for i in issues)


def test_per_file_description_detected() -> None:
    doc = _doc("├─ registered/  # Files ingested into DB\n")
    issues = check_per_file_description([doc])
    assert len(issues) == 1
    assert "per-file one-line description" in issues[0].message


def test_index_table_detected() -> None:
    doc = _doc(
        "**Public Functions**\n"
        "\n"
        "| Function | Signature | Description |\n"
        "|---|---|---|\n"
        "| foo | foo() -> None | does foo |\n"
    )
    issues = check_index_table([doc])
    assert len(issues) == 1
    assert "index table" in issues[0].message


def test_location_mapping_detected() -> None:
    doc = _doc("# Files ingested into DB (moved by ingester.py)\n")
    issues = check_location_mapping([doc])
    assert len(issues) == 1
    assert "location mapping" in issues[0].message


def test_literal_port_number_detected() -> None:
    doc = _doc("## file-write-mcp (Port 8007)\n")
    issues = check_literal_port_number([doc])
    assert len(issues) == 1
    assert "literal port number" in issues[0].message


def test_literal_port_number_exempts_illustrative_example() -> None:
    doc = _doc("For example, a server might listen on Port 9000 in a worked example.\n")
    issues = check_literal_port_number([doc])
    assert issues == []


def test_retain_category_only_content_has_no_false_positive() -> None:
    doc = _doc(
        "## Component Responsibility\n"
        "\n"
        "The RAG component owns the vector index and chunk metadata. It depends\n"
        "only on the Shared/DB layer for persistence, never directly on the Agent\n"
        "process. This separation exists because RAG runs as its own long-lived\n"
        "process with its own configuration, isolated from the Agent's lifecycle.\n"
    )
    issues: list = []
    issues += check_full_file_tree([doc])
    issues += check_per_file_description([doc])
    issues += check_index_table([doc])
    issues += check_location_mapping([doc])
    issues += check_literal_port_number([doc])
    assert issues == []
