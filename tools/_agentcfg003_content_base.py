#!/usr/bin/env python3
"""_agentcfg003_content_base.py — Default field values shared by the agentcfg003 content modules.

Private module for tools/generate_agentcfg003_procedures.py; cannot run standalone.
Every content module fills only the fields it authored, so this module holds the
values a row is assumed to have when nothing was authored for it.
"""

from __future__ import annotations

DEFAULTS: dict[str, object] = {
    "assumptions": [
        "No field-set version value is asserted here; the value is UNK-01."
    ],
    "alternatives": ["N/A: the plan's design section fixes the shape of this change."],
    "compat": ["N/A: no public contract is changed by this file alone."],
    "security": ["N/A: no trust boundary is crossed by this file."],
    "rollback": ["N/A: revert the commit within the release unit."],
    "validation": ["Run the validation sequence in `rules/toolchain.md`."],
    "out_of_scope": ["N/A: this document covers only its target file."],
    "goal": "N/A",
    "design": [],
    "procedure": "N/A",
    "method": [],
    "details": [],
    "completion": [
        "The change described in Implementation is present, and the validation plan passes."
    ],
    "exec_steps": [],
    "blockers": [],
    "work_items": [],
}

CONTENT: dict[str, dict[str, object]] = {}


def add(path: str, **fields: object) -> None:
    entry = dict(DEFAULTS)
    entry.update(fields)
    CONTENT[path] = entry
