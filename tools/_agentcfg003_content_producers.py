#!/usr/bin/env python3
"""_agentcfg003_content_producers.py — Authored content for the agentcfg003 MCP producer rows, computed from the current source.

Private module for tools/generate_agentcfg003_procedures.py; cannot run standalone.
"""

from __future__ import annotations

import re
from pathlib import Path

from tools._agentcfg003_content_base import DEFAULTS

REPO = Path(__file__).resolve().parent.parent

PRODUCERS = [
    "scripts/mcp_servers/cicd/cicd_tools.py",
    "scripts/mcp_servers/file/read_tools.py",
    "scripts/mcp_servers/file/write_tools.py",
    "scripts/mcp_servers/file/delete_tools.py",
    "scripts/mcp_servers/git/git_tools.py",
    "scripts/mcp_servers/github/tools_file.py",
    "scripts/mcp_servers/github/tools_issues.py",
    "scripts/mcp_servers/github/tools_pull_requests.py",
    "scripts/mcp_servers/github/tools_repository.py",
    "scripts/mcp_servers/mdq/mdq_tools.py",
    "scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py",
    "scripts/mcp_servers/shell/shell_tools.py",
    "scripts/mcp_servers/web_search/web_search_tools.py",
]

# Keys that the three named kinds cannot classify; they take the value the owner
# approved for keys no escalation rule reads.
NON_ESCALATING_KEYS = {"owner", "run_id", "workflow", "source", "destination"}

SHARED = {
    "goal": "Declare the extended per-tool field set on every tool entry in this module "
    "(REQ-003; AC-03).",
    "assumptions": [
        "The field set and the value types come from rows 01, 02 and 68 in the same release unit.",
        "No field-set version value is stated here; the version is recorded in one place (UNK-01).",
    ],
    "design": [
        "The declared values reproduce the classification this module already encodes, so the change is a "
        "declaration of what is already true, not a behavior change.",
        "Where the module already splits metadata into a shared TypedDict, the shared part is extended rather "
        "than repeated per entry, so the shared values stay in one place.",
    ],
    "alternatives": [
        "N/A: REQ-003 requires the fields to be declared by the producer, so a consumer-side default is not an "
        "option here."
    ],
    "compat": [
        "Every entry must carry the full set; `tests/mcp_servers/test_tool_schema_contract.py` (T-03) is the "
        "check that no entry is defaulted.",
    ],
    "security": [
        "A declaration that lowers risk relative to the current classification would change approval behaviour; "
        "the values are written from the current classification to keep it identical.",
    ],
    "rollback": ["N/A: revert the commit within the release unit."],
    "completion": [
        "Every entry in this module declares the required fields, and the contract test reports no entry with a "
        "missing field.",
        "The declared values match the classification the module expresses today.",
    ],
    "out_of_scope": [
        "The per-server write-protection gate that reads this module's tool list, and the runtime decision code "
        "that consumes the declared values (rows 22 to 25).",
    ],
}


def scan(path: str) -> dict[str, object]:
    text = (REPO / path).read_text(encoding="utf-8")
    entries = len(re.findall(r'^\s*"name": "', text, re.MULTILINE))
    helper = sorted(
        set(
            re.findall(
                r"^(?:class )?(_[A-Z_]+(?:HEAD|TAIL)|_[A-Z_]+_METADATA_[A-Z]+)",
                text,
                re.M,
            )
        )
    )
    typed_dict = bool(re.search(r"^class _\w+Metadata\w*\(TypedDict\):", text, re.M))
    kinds = sorted(set(re.findall(r'"resource_scope_kind": "([^"]*)"', text)))
    keys: list[str] = []
    for group in re.findall(r'"resource_scope_keys": \[([^\]]*)\]', text):
        keys.extend(k.strip().strip('"') for k in group.split(","))
        keys = [k for k in keys if k]
    keys = sorted(set(keys))
    non_escalating = sorted(set(keys) & NON_ESCALATING_KEYS)

    rec = dict(DEFAULTS)
    rec.update(SHARED)
    rec["goal"] = (
        f"Declare the extended per-tool field set on the {entries} tool entries in this module "
        f"(REQ-003; AC-03)."
    )
    rec["method"] = [
        "Add the new required fields to each entry with the values that match the classification this module "
        "already encodes (read entries declare `read_only`, write entries the matching write class).",
        "Convert `resource_scope_keys` from a key list to the key-to-kind mapping using the declared kind of "
        "this module's scope.",
    ]
    if typed_dict:
        rec["procedure"] = (
            f"Extend the shared metadata TypedDict and its literal ({', '.join('`' + h + '`' for h in helper)}) "
            "with the new fields, and leave the per-entry values that already vary inline unchanged."
        )
    else:
        rec["procedure"] = (
            "Add the new fields to each entry of the module's tool list; there is no shared metadata helper "
            "here, so the values are written per entry."
        )
    details = [
        f"Verified 2026-11-21: the module declares {entries} tool entries with scope kind "
        f"{'/'.join(kinds) if kinds else 'none'} and keys {', '.join(keys) if keys else 'none'}.",
    ]
    if typed_dict:
        details.append(
            "The shared head/tail split is preserved; only the fields that are identical across all entries move "
            "into the shared TypedDict."
        )
    if non_escalating:
        details.append(
            f"Keys {', '.join(non_escalating)} cannot be classified as path/branch/repo, so they take the value "
            "approved for keys no escalation rule reads."
        )
    rec["details"] = details
    rec["validation"] = [
        "`uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v`",
        "Run the validation sequence in `rules/toolchain.md`.",
    ]
    return rec


CONTENT: dict[str, dict[str, object]] = {path: scan(path) for path in PRODUCERS}
