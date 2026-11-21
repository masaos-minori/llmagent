#!/usr/bin/env python3
"""tools/remove_agentcfg003_toml_sections.py

One-shot edit for config/agent.toml per implementation procedure row 32
(agentcfg003): delete the [approval_risk_rules], [approval_resource_keys] and
[tool_safety_tiers] sections, the approval_dry_run_tools key, and rewrite the
comments that stated the removed precedence. Idempotent: a second run makes no
change.
"""

from __future__ import annotations

import sys
from pathlib import Path

CONFIG = Path("/home/sugimoto/llmagent/config/agent.toml")

PLAN_COMMENT_OLD = """# Explicit extension of the plan-mode block: the tool_safety_tiers rule is the
# authority (only READ_ONLY tools pass); this list adds tools blocked regardless
# of tier, redundant under the current tiers by design (DT-03 Option A).
"""
PLAN_COMMENT_NEW = """# Documented exception denylist on top of each tool's declared agent_safety_tier
# (agentcfg003 REQ-005/REQ-011): plan mode blocks these tools regardless of the
# tier their producer declares (DT-03 Option A retained as an operational
# exception, not a tier read).
"""
DRY_RUN_COMMENT_NEW = """# Dry-run capability is declared per tool (preview_capability in the tool's
# producer); no dry-run tool list exists in configuration (agentcfg003 REQ-005).
"""
RISK_COMMENT_OLD = """# approval_risk_rules is authoritative for approval risk: rules are consulted
# first, and a tool's tool_safety_tiers value is only consulted when no rule
# matches it.
"""
TIER_COMMENT_OLD = """# Tier entries for approval-rule-eligible tools exist for plan-mode blocking and
# the ADR-003 tier-vs-write classification, not for approval-risk escalation
# (defense-in-depth; DT-01 Option A).
"""


def _drop_section(lines: list[str], header: str) -> list[str]:
    """Remove a TOML table block including the comment lines directly above it."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].rstrip() == header:
            # rewind: drop preceding contiguous comment block
            while out and (out[-1].lstrip().startswith("#") or out[-1].strip() == ""):
                if out[-1].strip() == "" and not (
                    len(out) >= 2 and out[-2].lstrip().startswith("#")
                ):
                    break
                out.pop()
            # skip until the next table header (or EOF); map entries may be
            # unindented, so only a header ends the block
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith("["):
                    break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return out


def main() -> int:
    text = CONFIG.read_text(encoding="utf-8")
    if "[tool_safety_tiers]" not in text and "approval_dry_run_tools" not in text:
        print("already applied; no change")
        return 0
    lines = text.splitlines(keepends=True)

    # 1. approval_dry_run_tools key block (top-level list).
    start = next(
        i for i, line in enumerate(lines) if line.startswith("approval_dry_run_tools")
    )
    end = start
    while not lines[end].strip().endswith("]"):
        end += 1
    del lines[start : end + 1]

    # 2. table sections, each with its preceding comment block.
    lines = _drop_section(lines, "[approval_risk_rules]")
    lines = _drop_section(lines, "[approval_resource_keys]")
    lines = _drop_section(lines, "[tool_safety_tiers]")

    text = "".join(lines)
    assert PLAN_COMMENT_OLD in text
    text = text.replace(PLAN_COMMENT_OLD, PLAN_COMMENT_NEW)
    assert RISK_COMMENT_OLD not in text  # removed with its section
    assert TIER_COMMENT_OLD not in text  # removed with its section

    # 3. keep a note where the dry-run list used to live (above allowed_root).
    text = text.replace(
        'allowed_root = "/opt/llm"', DRY_RUN_COMMENT_NEW + 'allowed_root = "/opt/llm"'
    )

    CONFIG.write_text(text, encoding="utf-8")
    print("applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
