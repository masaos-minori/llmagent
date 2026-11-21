#!/usr/bin/env python3
"""_agentcfg003_content_docs.py — Authored content for the agentcfg003 documentation rows.

Private module for tools/generate_agentcfg003_procedures.py; cannot run standalone.
"""

from __future__ import annotations

from tools._agentcfg003_content_base import DEFAULTS

DOC_DEFAULTS: dict[str, object] = dict(DEFAULTS)
DOC_DEFAULTS.update(
    {
        "assumptions": [
            "Phase 1's ADR approval record is written before the docs rows are executed."
        ],
        "alternatives": ["N/A: the wording follows the ADR change recorded in row 67."],
        "compat": ["N/A: documentation-only change."],
        "security": ["N/A: documentation-only change."],
        "rollback": ["N/A: revert the commit."],
        "method": ["N/A: documentation-only change."],
        "out_of_scope": ["N/A: this document covers only its target file."],
        "work_items": [],
    }
)

CONTENT: dict[str, dict[str, object]] = {}


def add_doc(path: str, *, checker: str, **fields: object) -> None:
    entry = dict(DOC_DEFAULTS)
    entry["validation"] = [f"`{checker}`"]
    entry["exec_steps"] = [
        [
            "1",
            "Update the passages named in Implementation > Procedure",
            "Pending",
            "—",
            "—",
            "Phase 7; documentation-only row",
        ],
        ["2", "Run the documentation checker", "Pending", "—", "—", f"`{checker}`"],
    ]
    entry.update(fields)
    CONTENT[path] = entry


add_doc(
    "docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md",
    checker="uv run python tools/check_docs_structure.py docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md",
    goal="Remove the configuration-map priority statement and the local capability set from the approval "
    "documentation (REQ-012; AC-11).",
    design=[
        "The evaluation-order paragraph is rewritten so the declared metadata is the source, and the tier-vs-risk "
        "vocabulary paragraph keeps its distinction without naming a config map.",
        "The fail-closed sentence is not restated here; it stays owned by ADR-004.",
    ],
    procedure="Update the evaluation-order paragraph, the vocabulary paragraph, the design-judgment paragraph, and "
    "the dry-run and plan-mode bullets so they describe declared metadata; the whitelist sentence about "
    "the local capability set is removed.",
    details=[
        "Verified 2026-11-21: the evaluation-order paragraph names the removed maps, and the whitelist "
        "paragraph names the local capability set this plan removes."
    ],
    completion=[
        "No passage in this file presents a configuration map or a static tool-name set as the decision "
        "source."
    ],
)

add_doc(
    "docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md",
    checker="uv run python tools/check_docs_structure.py docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md",
    goal="Move the canonical risk-level source from the configuration map to declared metadata (REQ-012; AC-11).",
    design=[
        "Only the canonical-source statements are changed; the exit-path table and the writer for each outcome "
        "stay as they are."
    ],
    procedure="Change the sentences that say a tool without a rule falls back to its safety-tier default so the "
    "fallback is the declared tier's mapped risk, and keep the cross-reference to the canonical "
    "evaluation order in agent_06_02.",
    details=[
        "Verified 2026-11-21: two paragraphs state the per-tool rule fallback as the canonical source."
    ],
    completion=[
        "The file names declared metadata as the level source, and the canonical cross-reference still "
        "points to agent_06_02."
    ],
)

add_doc(
    "docs/23_agent/agent_08_03_configuration-tools-memory.md",
    checker="uv run python tools/check_docs_structure.py docs/23_agent/agent_08_03_configuration-tools-memory.md",
    goal="Remove the removed configuration keys from the documented field set (REQ-012; AC-11).",
    design=[
        "The documented field set lists only the fields that remain, and the plan-mode sentence is reworded "
        "to the documented exception denylist on top of the declared tier."
    ],
    procedure="Remove the paragraphs that document the removed maps, and reword the plan-mode bullet so the "
    "denylist is described as an exception on top of the declared tier.",
    details=[
        "Verified 2026-11-21: the only remaining statement about the removed concept is the plan-mode bullet "
        "that describes the denylist as an extension of the tier rule."
    ],
    completion=[
        "The documented field set matches `scripts/agent/config_dataclasses.py` after row 30."
    ],
)

add_doc(
    "docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md",
    checker="uv run python tools/check_docs_structure.py docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md",
    goal="Remove the removed configuration keys and the precedence statement (REQ-012; AC-11).",
    design=[
        "The precedence paragraph is removed rather than reworded, because precedence between two "
        "configuration maps no longer exists."
    ],
    procedure="Remove the paragraphs that document the removed maps and the precedence statement, and keep the "
    "cross-reference to the canonical evaluation order.",
    details=[
        "Verified 2026-11-21: the file states per-tool base risk from the removed rule map, the precedence "
        "between the rule map and the tier map, and the unknown-key fatal consequence."
    ],
    completion=[
        "No paragraph documents a removed key, and the fatal-at-startup consequence is described only "
        "through the fail-closed registration path."
    ],
)

add_doc(
    "docs/91_security/security_02_high-risk-tool-common-policy.md",
    checker="uv run python tools/check_docs_structure.py docs/91_security/security_02_high-risk-tool-common-policy.md",
    goal="Update the fail-closed table and the approval-to-tier mapping to declared metadata (REQ-012; AC-11).",
    design=[
        "The allowlist rows of the fail-closed table are unchanged: they are operational exceptions the plan "
        "keeps."
    ],
    procedure="Change the mapping table's introduction so the tier is the declared value rather than a "
    "configuration map, and remove the statement that an explicit rule can override it.",
    details=[
        "Verified 2026-11-21: the table introduction attributes the default risk to the configuration map "
        "and describes an override that no longer exists."
    ],
    completion=[
        "The security document describes the tier as declared metadata, and the allowlist rows still "
        "describe the operational exceptions."
    ],
)
