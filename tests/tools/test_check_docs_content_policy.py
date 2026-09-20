"""tests/tools/test_check_docs_content_policy.py

Unit tests for tools/check_docs_content_policy.py's detection logic — one test
per remove-category, plus one confirming no false positive on
retain-category-only content.
"""

from __future__ import annotations

from pathlib import Path

from tools.check_docs_content_policy import (
    DocFile,
    check_cli_argument_table,
    check_cli_command_enumeration,
    check_config_file_inventory_table,
    check_ddl_schema_block,
    check_default_value_restatement,
    check_environment_setup_sequence,
    check_error_handling_table,
    check_field_type_table,
    check_full_file_tree,
    check_full_json_example,
    check_index_table,
    check_literal_port_number,
    check_location_mapping,
    check_per_file_description,
    check_typed_dict_table,
)
from tools.generate_reference_table import GUARD_START_MCP


def _doc(text: str, rel_path: str = "fixture.md") -> DocFile:
    return DocFile(path=Path(rel_path), rel_path=rel_path, lines=text.splitlines())


def test_full_file_tree_detected() -> None:
    doc = _doc("## File Structure\n├─ rag-src/\n│   └─ chunk/\n└─ sqlite-vec/\n")
    issues = check_full_file_tree([doc])
    assert len(issues) >= 1
    assert all(i.severity == "WARNING" for i in issues)
    assert all("full file tree" in i.message for i in issues)


def test_non_tree_diagram_not_flagged() -> None:
    """State-transition diagram should NOT be flagged as a full file tree."""
    doc = _doc(
        "## McpServerHealthRegistry State Transitions\n"
        "\n"
        "HEALTHY ──(failure × threshold)──→ UNAVAILABLE\n"
        "   ↑                                    │\n"
        "   │                            (cooldown 30s elapsed)\n"
        "   │                                    ↓\n"
        "   └──(record_success)────────── HALF_OPEN (trial probe)\n"
        "                                         │\n"
        "                               (failure)─┘ → UNAVAILABLE (cooldown reset)\n"
    )
    issues = check_full_file_tree([doc])
    assert issues == []


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


def test_literal_port_number_exempted_inside_auto_generated_block() -> None:
    doc = _doc(
        "<!-- AUTO-GENERATED -->\n"
        "## Server Port & Tool Reference\n"
        "Port 8001: agent-server\n"
        "Port 8002: mcp-server\n"
        "Port 8003: rag-server\n"
        "<!-- END AUTO-GENERATED -->\n"
    )
    issues = check_literal_port_number([doc])
    assert issues == []


def test_literal_port_number_flagged_outside_auto_generated_block() -> None:
    doc = _doc(
        "<!-- AUTO-GENERATED -->\n"
        "## Server Port & Tool Reference\n"
        "Port 8001: agent-server\n"
        "Port 8002: mcp-server\n"
        "Port 8003: rag-server\n"
        "<!-- END AUTO-GENERATED -->\n"
        "## Additional Info (Port 9000)\n"
    )
    issues = check_literal_port_number([doc])
    assert len(issues) == 1
    assert "literal port number" in issues[0].message


def test_default_value_restatement_detected() -> None:
    doc = _doc("The `max_retry` defaults to `3` (see config.py).\n")
    issues = check_default_value_restatement([doc])
    assert len(issues) == 1
    assert "default-value restatement" in issues[0].message


def test_default_value_restatement_not_flagged_with_rationale() -> None:
    doc = _doc(
        "`max_retry` defaults to `3` because a lower value causes premature "
        "DLQ promotion under transient failures.\n"
    )
    issues = check_default_value_restatement([doc])
    assert issues == []


def test_field_type_table_detected() -> None:
    doc = _doc(
        "| Field | Type | Default |\n"
        "|---|---|---|\n"
        "| a | int | 1 |\n"
        "| b | str | x |\n"
        "| c | bool | true |\n"
    )
    issues = check_field_type_table([doc])
    assert len(issues) == 1
    assert "field/type/default table" in issues[0].message


def test_field_type_table_not_flagged_when_short() -> None:
    doc = _doc("| Field | Type | Default |\n|---|---|---|\n| a | int | 1 |\n")
    issues = check_field_type_table([doc])
    assert issues == []


def test_config_file_inventory_table_detected() -> None:
    doc = _doc("### Configuration Fields\n\n- `port` — HTTP listening port\n")
    issues = check_config_file_inventory_table([doc])
    assert len(issues) == 1
    assert "config-file inventory" in issues[0].message


def test_config_file_inventory_table_not_flagged_without_heading() -> None:
    doc = _doc("## Notes\n\n- `port` — an example field name mentioned in passing\n")
    issues = check_config_file_inventory_table([doc])
    assert issues == []


def test_cli_command_enumeration_detected() -> None:
    doc = _doc(
        "## CLI Commands\n"
        "\n"
        "```bash\n"
        "cmd1\n"
        "```\n"
        "```bash\n"
        "cmd2\n"
        "```\n"
        "```bash\n"
        "cmd3\n"
        "```\n"
    )
    issues = check_cli_command_enumeration([doc])
    assert len(issues) == 3
    assert all("CLI-command enumeration" in i.message for i in issues)


def test_cli_command_enumeration_not_flagged_for_single_example() -> None:
    doc = _doc("## CLI Commands\n\n```bash\ncmd1\n```\n")
    issues = check_cli_command_enumeration([doc])
    assert issues == []


def test_environment_setup_sequence_detected() -> None:
    doc = _doc(
        "## Setup\n"
        "\n"
        "1. Install dependencies\n"
        "2. Configure environment\n"
        "3. Run the server\n"
    )
    issues = check_environment_setup_sequence([doc])
    assert len(issues) == 3
    assert all("environment-setup command sequence" in i.message for i in issues)


def test_environment_setup_sequence_not_flagged_when_short() -> None:
    doc = _doc("## Setup\n\n1. Install dependencies\n2. Run the server\n")
    issues = check_environment_setup_sequence([doc])
    assert issues == []


def test_ddl_schema_block_detected() -> None:
    doc = _doc("```sql\nCREATE TABLE events (id INTEGER PRIMARY KEY);\n```\n")
    issues = check_ddl_schema_block([doc])
    assert len(issues) == 1
    assert "DDL/schema block" in issues[0].message


def test_ddl_schema_block_not_flagged_without_ddl_statement() -> None:
    doc = _doc("```sql\nSELECT * FROM events WHERE id = 1;\n```\n")
    issues = check_ddl_schema_block([doc])
    assert issues == []


def test_guard_detection_recognizes_real_generator_format() -> None:
    doc = _doc(
        f"{GUARD_START_MCP}\n"
        "## File Structure\n"
        "├─ rag-src/\n"
        "└─ sqlite-vec/\n"
        "\n"
        "| Function | Signature | Description |\n"
        "|---|---|---|\n"
        "| foo | foo() -> None | does foo |\n"
        "\n"
        "# Files ingested into DB (moved by ingester.py)\n"
        "\n"
        "## file-write-mcp (Port 8007)\n"
        "<!-- END AUTO-GENERATED -->\n"
    )
    assert check_full_file_tree([doc]) == []
    assert check_index_table([doc]) == []
    assert check_location_mapping([doc]) == []
    assert check_literal_port_number([doc]) == []


def test_typed_dict_table_detected() -> None:
    doc = _doc(
        "**Typed dict**\n"
        "\n"
        "| TypedDict | Purpose |\n"
        "|---|---|\n"
        "| CrawlJsonPayload | Typed dictionary for crawl output JSON files |\n"
    )
    issues = check_typed_dict_table([doc])
    assert len(issues) == 1
    assert "TypedDict/DTO field table" in issues[0].message


def test_typed_dict_table_not_flagged_for_unrelated_table() -> None:
    doc = _doc("| Component | Owner |\n|---|---|\n| RAG | rag-team |\n")
    issues = check_typed_dict_table([doc])
    assert issues == []


def test_cli_argument_table_detected() -> None:
    doc = _doc(
        "### CLI Arguments\n"
        "\n"
        "| Argument | Description | Default |\n"
        "|---|---|---|\n"
        "| `--file PATH` | Process only one file | all files |\n"
    )
    issues = check_cli_argument_table([doc])
    assert len(issues) == 1
    assert "CLI argument table" in issues[0].message


def test_cli_argument_table_not_flagged_without_cli_heading() -> None:
    doc = _doc(
        "## Notes\n"
        "\n"
        "| Argument | Description | Default |\n"
        "|---|---|---|\n"
        "| `--file PATH` | Process only one file | all files |\n"
    )
    issues = check_cli_argument_table([doc])
    assert issues == []


def test_error_handling_table_detected_by_heading() -> None:
    doc = _doc(
        "### Error Handling\n"
        "\n"
        "| Case | Action |\n"
        "|---|---|\n"
        "| Tokenization error | Raises TokenizationError |\n"
    )
    issues = check_error_handling_table([doc])
    assert len(issues) == 1
    assert "error-handling table" in issues[0].message


def test_error_handling_table_detected_by_header_shape_without_heading() -> None:
    doc = _doc(
        "## Notes\n"
        "\n"
        "| Case | Action |\n"
        "|---|---|\n"
        "| Tokenization error | Raises TokenizationError |\n"
    )
    issues = check_error_handling_table([doc])
    assert len(issues) == 1
    assert "error-handling table" in issues[0].message


def test_error_handling_table_not_flagged_for_unrelated_table() -> None:
    doc = _doc("## Notes\n\n| Component | Owner |\n|---|---|\n| RAG | rag-team |\n")
    issues = check_error_handling_table([doc])
    assert issues == []


def test_full_json_example_detected() -> None:
    lines = "\n".join(f'  "field{i}": {i},' for i in range(16))
    doc = _doc(f"```json\n{{\n{lines}\n}}\n```\n")
    issues = check_full_json_example([doc])
    assert len(issues) == 1
    assert "full JSON payload example" in issues[0].message


def test_full_json_example_not_flagged_for_short_snippet() -> None:
    doc = _doc('```json\n{"status": "ok"}\n```\n')
    issues = check_full_json_example([doc])
    assert issues == []
