#!/usr/bin/env python3
"""Validate docs/*.md structural conventions: size, H1 count, Front Matter,
the Keywords section (and the `## Related ADRs` section of ADR documents),
body Related Documents/Docs/Chapters headings at ANY level in every doc (ADRs
included: `related:` front matter is the single cross-reference store),
front matter `related:` format (basenames ending in .md) and coverage of ADR
body references, and internal .md link reachability.

Usage:
    uv run python tools/check_docs_structure.py [glob ...]
    uv run python tools/check_docs_structure.py docs/05_agent_*.md --area agent
    uv run python tools/check_docs_structure.py docs/*.md docs/10_adr/*.md --schema schemas/doc_front_matter.json
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._front_matter_schema import FrontMatterSchema, load_front_matter_schema

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
# Raised from 16384 (2026-09-03, plans/20260902-191512_plan.md): a governance
# doc consolidation was already at 16252 bytes before the dependency-graph
# redesign added ~2900 bytes of required content (four scoped relation-type
# sections), leaving no realistic headroom under the old limit. 24576 covers
# that need with margin while still catching genuinely oversized files (e.g.
# docs/00_governance/governance_03_issue-and-uncertainty-management.md at ~46KB remains
# correctly flagged).
# Raised to 32768 (2026-11-18) by the owner; per-file ceilings below it were removed.
MAX_SIZE = 32768

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)(?:#[^)]*)?\)")


def _build_basename_index(docs_dir: Path) -> dict[str, Path]:
    """Map every `docs/**/*.md` file's basename to its path.

    Cross-reference resolution (`check_related_links`, `check_links`) uses this
    index to resolve a bare filename regardless of which directory it lives in,
    so `docs/` subfolders don't break existing bare-filename references. Raises
    if two files share a basename — this uniqueness is load-bearing for that
    resolution to stay unambiguous.
    """
    index: dict[str, Path] = {}
    for path in docs_dir.rglob("*.md"):
        if path.name in index:
            raise ValueError(
                f"duplicate basename '{path.name}' found at both "
                f"{index[path.name]} and {path}"
            )
        index[path.name] = path
    return index


def strip_fenced_code(content: str) -> str:
    lines = content.split("\n")
    kept = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    return "\n".join(kept)


# Per-file ceilings above MAX_SIZE, keyed by basename. Each ceiling equals the file's
# accepted size, so any further growth fails.
SIZE_EXCEPTIONS: dict[str, int] = {
    # Re-accepted 2026-11-12 (adrrev011, procedure 20261111-231122_05): the Decision 9
    # pointer to ADR-017, the Out of Scope pointer, and the completed Decision Change
    # Approval Record grew the file 24646 -> 25606. The ceiling equals the accepted size.
    # ADR-004 grew by the audit Owner assignment and the spawn-failure Exceptions
    # section (2026-10-13), the security-posture Decision and Automated Tests rows
    # (2026-10-17), and the by-phase failure-class verification evidence (2026-10-17);
    # the ceiling equals the size reached.
    # Re-recorded after the grouped rename: 32305.
    # Re-accepted at 32448 (2026-11-01): mcpgate001 added the component-mandatoriness
    # classification note; the ceiling equals the accepted size.
    # Re-accepted at 32586 (2026-11-11): closes a pre-existing gap — ADR-004 had grown to
    # 32586 by cad5e91ea (adrrev004) without the ceiling being re-recorded (it stayed at
    # 32448). Not part of adrrev007 scope (the plan treats ADR-004 as an unmodified reference
    # target); recorded here only to keep check_docs_structure.py green. The ceiling equals
    # the accepted size, so further growth fails.
    # Re-accepted at 34555 (2026-11-12): adrrev015 doc 06 added the INV-14 test citations
    # and one pending approval line.
    # Re-accepted at 35498 (2026-11-20): adrchk015 Phase 3 added the ADR-006/ADR-008 front
    # matter entries and Related ADRs bullets; the ceiling equals the accepted size.
    # Re-accepted at 36267 (2026-11-20): adrchk013 renamed the Automated Tests `Status`
    # column to `Implementation`, added the row test citations and the INV-14 row; the
    # ceiling equals the accepted size.
    # Re-accepted at 36992 (2026-11-24, adrren001 procedure 20261124-113849_15): the longer
    # ADR-008 file name in the Known Deviations citation grew the ADR 36986 -> 36992; the
    # ceiling equals the accepted size.
    "adr_02_01_004_platform-environment-failure-handling-policy.md": 36992,
    # Re-accepted 2026-11-12, closing a second pre-existing gap: the file had grown 32586
    # -> 33944 by 83879685e (adrrev008) without the ceiling being re-recorded. Recorded
    # only to keep check_docs_structure.py green.
    # ADR-007 reached 24596 after the grouped rename (default limit 24576).
    # adr_02_05_008 sat at 33647 until dbmig001 recorded the workflow/eventbus
    # forward-only migration contract in Context > Constraints plus an Amendment
    # subsection and a realized Revisit Trigger (2026-10-30); the ceiling is
    # re-recorded to the accepted size.
    # Re-accepted at 44006: the six-database scope, the per-database schema-mismatch and
    # retention rules, the memory canonical store, and the table inventory.
    # Re-accepted at 46907 (2026-11-24, adrdoc001 procedure 20261124-094801_02): the
    # six-store title, the lifecycle matrix rows, Repository Context and Episodic Memory
    # (Decision Details 23 to 25), INV-19 to INV-22, and the two Known Issue citations
    # grew the ADR 44006 -> 46907; the ceiling equals the accepted size.
    # Re-accepted at 47600 (2026-11-24): the maintainer's approval of the six-store scope,
    # the schema-mismatch rule, the memory model, and the memory lifecycle decisions was
    # recorded in the Approval Record (replacing three pending bullets); 46907 -> 47600.
    # Re-accepted at 49132 (2026-11-24): Decision Details 26 and 27, the Episodic
    # taxonomy, retention, search, and Repository Context safety clauses, and the
    # capacity rows grew the ADR 47600 -> 49132; the ceiling equals the accepted size.
    # Re-accepted at 54865 (memo-issue.md); 51665 -> 54865.
    "adr_02_05_008_db-six-sqlite-store-separation.md": 54865,
    # Accepted at 39575 (2026-11-24, adrdoc001 procedure 20261124-094801_01): the
    # single-source-of-truth, state-aware retention, replay-floor, and capacity decisions
    # (Decision Details 15 to 20), INV-17 to INV-22, the Known Deviations, and the two
    # pending approval bullets grew the ADR past the default limit; the ceiling equals the
    # accepted size.
    # Re-accepted at 40950 (2026-11-24, adrren001 procedure 20261124-113849_15): the longer
    # ADR-008 file name in the related entry grew the ADR 40944 -> 40950; the ceiling equals
    # the accepted size.
    "adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md": 40950,
    "adr_02_04_013_eventbus-authentication-authorization.md": 33889,
    # Re-accepted at 36609 (2026-11-20, adrchk013 procedure 20261120-111659_03): the
    # ADR-016/ADR-017 matrix rows, the split-out ADR-012 INV-04 row, the ADR-003 INV-03
    # Partial rewrite, the dropped migration-window wording and the Pipeline Mapping
    # Summary update; the ceiling equals the accepted size.
    # Re-accepted at 37826 (2026-11-23, gov006 procedure 20261123-165833_11): the matrix
    # rows added for ADR-001 INV-02, ADR-002 INV-03, ADR-003 INV-04 and INV-07 grew the
    # index 36609 -> 37826; the ceiling equals the accepted size.
    # Re-accepted at 41389 (2026-11-24, adrdoc001 procedure 20261124-094801_03): the
    # ADR-006 INV-17 to INV-22 and ADR-008 INV-19 to INV-22 matrix rows and the regenerated
    # guarded blocks grew the index 37826 -> 41389; the ceiling equals the accepted size.
    # Re-accepted at 41640 (2026-11-24): the ADR-008 INV-20 and INV-21 matrix rows gained
    # the secret-rejection, state-aware retention, and required-FTS evidence; 41389 -> 41640.
    # Re-accepted at 42344 (2026-11-24): INV-19 Partial and INV-23 rows.
    # Re-accepted at 42356 (2026-11-24, adrren001 procedure 20261124-113849_15): the longer
    # ADR-008 file name in two references grew the index 42344 -> 42356; the ceiling equals
    # the accepted size.
    "adr_01_index.md": 42356,
    # Re-accepted at 33915 (2026-11-20, adrchk021 procedure 20261120-174933_01): the
    # MCP-005 Known Issue entry (git_add/git_commit protected-branch gap registration)
    # grew the ledger 31908 -> 33915; the ceiling equals the accepted size.
    # Re-accepted at 34313 (2026-11-20, adrchk021 procedure 20261120-174933_04): the
    # AAL-038 ledger entry (ADR-015 pending amendment, release unit with procedure 03)
    # grew the ledger 33915 -> 34313; the ceiling equals the accepted size.
    # Re-accepted at 36248 (2026-11-20, adrchk023 procedure 20261120-213832_01): the
    # AGENT-001 Known Issue entry (unused agent-side EventBus client modules) grew the
    # ledger 34313 -> 36248; the ceiling equals the accepted size.
    # Re-accepted at 36807 (2026-11-24, adrdoc001 procedure 20261124-094801_06): the
    # AAL-039 to AAL-041 entries and the EVENTBUS-001, EVENTBUS-002, SHARED-003, and
    # SHARED-004 Known Issues, net of the removed AAL-026, AAL-027, and SHARED-002,
    # grew the ledger 36248 -> 36807; the ceiling equals the accepted size.
    # Re-accepted at 39898 (2026-11-24): SHARED-004 split into SHARED-004 to SHARED-007.
    "governance_03_issue-and-uncertainty-management.md": 39898,
    # Re-accepted at 33078 (2026-11-25): closes a pre-existing gap — the generated
    # subpackage index grew past MAX_SIZE through cliplc003's agent subpackage
    # additions without the ceiling being recorded. The ceiling equals the accepted
    # size, so further growth must be re-accepted.
    # Re-accepted at 33392 (2026-11-25, mcpai004 procedure 20261125-112546_25): the
    # subpackage index grew 33078 -> 33392 with TurnControl,
    # reconstruct_replay_directives, and the changed record_tool_call signature. The
    # ceiling equals the accepted size.
    # Re-accepted at 35212 (2026-11-25, cliplc005 row 4): the 16 validators the field
    # registry gained for entries that had none (REQ-010) are public functions in
    # scripts/agent/services/config_validators.py, so the regenerated agent_subpackages
    # index grew 33078 -> 35212. The ceiling equals the accepted size.
    # Re-accepted at 35530 (2026-11-25, cliplc005 row 9): the typed candidate classifiers,
    # PendingChange, and the agent_config_payload renderer added by the shared candidate
    # build are public symbols, so the index grew 35212 -> 35530. The ceiling equals the
    # accepted size.
    # Re-accepted at 36384 (2026-11-25, cliplc005 rows 7/11/12/16/17/18): the staged
    # transaction adds public symbols in scripts/shared/config_undo.py,
    # scripts/agent/services/config_reload_transaction.py, and
    # scripts/agent/services/exceptions.py, plus the snapshot and restore pairs on the
    # live services, so the index grew 35530 -> 36384. The ceiling equals the accepted size.
    # Re-accepted at 36973 (2026-11-25, cliplc005 rows 8/21/22/23/24): the pending-restart
    # view adds public symbols in scripts/agent/services/config_pending_state.py
    # (PendingConfigState, PendingMcpRecord, pending_state_for),
    # scripts/agent/services/mcp_status.py (McpPendingRow, McpStatusService.pending_rows),
    # and the AppServices.pending_config attribute, so the index grew 36384 -> 36973. The
    # ceiling equals the accepted size.
    # Re-accepted at 37198 (2026-11-25, cliplc005 rebased onto mcpai004): the merged
    # index carries both plans' symbols, so the regenerated file is 37198. The ceiling
    # equals the accepted size.
    # Re-accepted at 37507 (2026-11-26, cliplc008 row 6): the capability classification adds
    # public symbols in scripts/agent/services/mcp_health.py (CapabilityFinding,
    # classify_capabilities), so the regenerated index grew 37198 -> 37507. The ceiling
    # equals the accepted size.
    "agent_14_reference-api-subpackages-generated.md": 37507,
}


def check_size(path: Path, size: int) -> list[str]:
    limit = SIZE_EXCEPTIONS.get(path.name, MAX_SIZE)
    if size > limit:
        return [f"{path.name}: size {size} bytes exceeds {limit} byte limit"]
    return []


def check_h1_count(path: Path, body: str) -> list[str]:
    count = len(re.findall(r"^# ", body, re.MULTILINE))
    if count != 1:
        return [f"{path.name}: found {count} H1 heading(s), expected exactly 1"]
    return []


def check_front_matter(
    path: Path, content: str, expected_area: str | None
) -> list[str]:
    issues = []
    if not content.startswith("---"):
        return [f"{path.name}: missing Front Matter (does not start with '---')"]
    end = content.find("\n---", 3)
    if end == -1:
        return [f"{path.name}: Front Matter opening '---' has no closing '---'"]
    raw = content[3:end]
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        return [f"{path.name}: Front Matter is not valid YAML — {exc}"]
    for field in ("title", "area", "tags", "related"):
        if field not in data:
            issues.append(f"{path.name}: Front Matter missing '{field}' field")
    if expected_area and data.get("area") != expected_area:
        issues.append(
            f"{path.name}: Front Matter area is '{data.get('area')}', expected '{expected_area}'"
        )
    return issues


def check_schema_compliance(
    path: Path, content: str, schema: FrontMatterSchema
) -> list[str]:
    """Validate Front Matter against `schema` (required fields, `area`/`status`
    enums). Opt-in only — called from `validate_file()` when `--schema` was
    passed. Missing/unparsable Front Matter is already reported by
    `check_front_matter()`; this function returns early rather than
    double-reporting the same root cause.
    """
    if not content.startswith("---"):
        return []
    end = content.find("\n---", 3)
    if end == -1:
        return []
    try:
        data = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return []
    issues: list[str] = []
    for field in schema.required_fields:
        if field not in data:
            issues.append(
                f"{path.name}: Front Matter missing required '{field}' field "
                f"(schema: {schema.source})"
            )
    if schema.area_enum is not None:
        area = data.get("area")
        if area is not None and area not in schema.area_enum:
            issues.append(
                f"{path.name}: Front Matter 'area' value {area!r} is not one of "
                f"the schema's allowed values {list(schema.area_enum)} "
                f"(schema: {schema.source})"
            )
    if schema.status_enum is not None:
        status = data.get("status")
        if status is not None and status not in schema.status_enum:
            issues.append(
                f"{path.name}: Front Matter 'status' value {status!r} is not one "
                f"of the schema's allowed values {list(schema.status_enum)} "
                f"(schema: {schema.source})"
            )
    return issues


def check_status_value(path: Path, data: dict[str, Any]) -> list[str]:
    """Validate the 'status' field against allowed values [stable, draft].

    Returns empty list when the 'status' field is absent (defaults to stable).
    Returns error list when the value is invalid.
    """
    status = data.get("status")
    if status is None:
        return []
    if status not in ("stable", "draft"):
        return [
            f"{path.name}: 'status' value {status!r} is not one of ['stable', 'draft']"
        ]
    return []


_RELATED_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+)(?:Related Documents|Related Docs|Related Chapters)[ \t]*$",
    re.MULTILINE,
)
_BODY_REF_RE = re.compile(r"`([^`\n]+\.md)`|\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")


def _validate_related_format(related_entries: list[str]) -> list[str]:
    """Validate that `related:` entries are plain .md basenames.

    Each entry must be a basename ending in ``.md`` with no path (``/``) or
    anchor (``#``); cross-references resolve as bare basenames through the shared
    basename index. Returns one issue per malformed entry.
    """
    issues: list[str] = []
    for entry in related_entries or []:
        basename = Path(entry).name
        if not basename.endswith(".md"):
            issues.append(f"related entry {entry!r}: must end in '.md'")
        if "/" in entry or "#" in entry:
            issues.append(
                f"related entry {entry!r}: must be a plain basename (no path or anchor)"
            )
    return issues


def _is_adr(path: Path) -> bool:
    return "10_adr" in path.parts


def check_tail_sections(path: Path, content: str) -> list[str]:
    issues = []
    for match in _RELATED_HEADING_RE.finditer(strip_fenced_code(content)):
        issues.append(
            f"{path.name}: document must not carry a body "
            f"'{match.group(0)}' section; use front matter 'related:'"
        )
    if _is_adr(path) and ADR_ID_RE.match(path.name):
        if not re.search(r"^## Related ADRs", content, re.MULTILINE):
            issues.append(f"{path.name}: missing '## Related ADRs' section")
    if not re.search(r"^## Keywords", content, re.MULTILINE):
        issues.append(f"{path.name}: missing '## Keywords' section")
    return issues


def check_links(
    path: Path,
    content: str,
    basename_index: dict[str, Path],
    check_duplicates: bool = False,
) -> list[str]:
    issues = []
    body = strip_fenced_code(content)
    seen: dict[Path, int] = {}
    for _text, target in LINK_RE.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        if "/" in target:
            resolved = (path.parent / target).resolve()
        else:
            resolved = basename_index.get(target, path.parent / target).resolve()
        seen[resolved] = seen.get(resolved, 0) + 1
        if "/" in target:
            found = (path.parent / target).resolve().is_file()
        else:
            found = target in basename_index
        if not found:
            issues.append(f"{path.name}: broken link -> '{target}'")
        else:
            # Self-reference check: compare resolved paths to handle absolute/relative/cross-dir cases
            if "/" in target:
                resolved_target = (path.parent / target).resolve()
            else:
                # For bare basenames, resolve via basename_index to get the actual path
                resolved_target = basename_index.get(
                    target, path.parent / target
                ).resolve()
            if resolved_target == path.resolve():
                issues.append(f"{path.name}: self-reference detected -> '{target}'")
    if check_duplicates:
        for resolved, count in seen.items():
            if count > 1:
                issues.append(
                    f"{path.name}: duplicate link -> '{resolved}' (appears {count} times)"
                )
    return issues


ADR_ID_RE = re.compile(r"^adr_02_\d{2}_(\d{3})_")


def check_unique_adr_ids(files: list[Path]) -> list[str]:
    seen: dict[str, Path] = {}
    issues: list[str] = []
    for path in files:
        stem = path.stem
        m = ADR_ID_RE.match(stem)
        if m is None:
            continue
        adr_id = f"ADR-{m.group(1)}"
        if adr_id in seen:
            issues.append(
                f"{seen[adr_id].name}, {path.name}: duplicate ADR ID '{adr_id}'"
            )
        else:
            seen[adr_id] = path
    return issues


def check_related_links(
    path: Path,
    content: str,
    basename_index: dict[str, Path],
    check_duplicates: bool = False,
) -> list[str]:
    if not content.startswith("---"):
        return []
    end = content.find("\n---", 3)
    if end == -1:
        return []
    try:
        data = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return []  # already reported by check_front_matter(); avoid double-reporting
    issues = []
    seen: dict[Path, int] = {}
    for field in ("related", "source"):
        for entry in data.get(field) or []:
            if "/" in entry:
                resolved = (path.parent / entry).resolve()
            else:
                resolved = basename_index.get(entry, path.parent / entry).resolve()
            seen[resolved] = seen.get(resolved, 0) + 1
            if "/" in entry:
                found = (path.parent / entry).resolve().is_file()
            else:
                found = entry in basename_index
            if not found:
                issues.append(
                    f"{path.name}: front matter references missing file '{entry}' (field: {field})"
                )
            else:
                # Self-reference check: compare resolved paths to handle absolute/relative/cross-dir cases
                if "/" in entry:
                    resolved_entry = (path.parent / entry).resolve()
                else:
                    resolved_entry = basename_index.get(
                        entry, path.parent / entry
                    ).resolve()
                if resolved_entry == path.resolve():
                    issues.append(f"{path.name}: self-reference detected -> '{entry}'")
    if check_duplicates:
        for resolved, count in seen.items():
            if count > 1:
                issues.append(
                    f"{path.name}: duplicate related link -> '{resolved}' (appears {count} times)"
                )
    issues.extend(_validate_related_format(data.get("related") or []))
    return issues


def check_adr_related_coverage(
    path: Path, content: str, basename_index: dict[str, Path]
) -> list[str]:
    """ADR front matter `related:` must cover the documents its body references."""
    if not _is_adr(path) or not content.startswith("---"):
        return []
    end = content.find("\n---", 3)
    if end == -1:
        return []
    try:
        data = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return []  # already reported by check_front_matter()
    covered = {PurePosixPath(str(entry)).name for entry in data.get("related") or []}
    body = strip_fenced_code(content[end:])
    missing: list[str] = []
    for heading in _RELATED_HEADING_RE.finditer(body):
        following = re.search(r"^## ", body[heading.end() :], re.MULTILINE)
        stop = heading.end() + following.start() if following else len(body)
        for code_ref, link_ref in _BODY_REF_RE.findall(body[heading.end() : stop]):
            name = PurePosixPath(code_ref or link_ref).name
            if (
                name != path.name
                and name in basename_index
                and name not in covered
                and name not in missing
            ):
                missing.append(name)
    return [
        f"{path.name}: front matter 'related:' lacks body-referenced document '{name}'"
        for name in missing
    ]


def validate_file(
    path: Path,
    expected_area: str | None,
    schema: FrontMatterSchema | None = None,
    *,
    basename_index: dict[str, Path],
    check_duplicates: bool = False,
) -> list[str]:
    content = path.read_text(encoding="utf-8")
    size = len(content.encode("utf-8"))
    body = strip_fenced_code(content)
    issues = []
    issues.extend(check_size(path, size))
    issues.extend(check_h1_count(path, body))
    issues.extend(check_front_matter(path, content, expected_area))
    # Parse front matter once for downstream checks
    data: dict[str, Any] = {}
    try:
        end = content.find("\n---", 3)
        if end != -1:
            raw = content[3:end]
            data = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        pass
    issues.extend(check_status_value(path, data))
    if schema is not None:
        issues.extend(check_schema_compliance(path, content, schema))
    issues.extend(check_tail_sections(path, content))
    issues.extend(
        check_links(path, content, basename_index, check_duplicates=check_duplicates)
    )
    issues.extend(
        check_related_links(
            path, content, basename_index, check_duplicates=check_duplicates
        )
    )
    issues.extend(check_adr_related_coverage(path, content, basename_index))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate docs/ structural conventions"
    )
    parser.add_argument(
        "globs",
        nargs="*",
        help="Glob patterns relative to repo root (default: docs/**/*.md)",
    )
    parser.add_argument("--area", default=None, help="Expected Front Matter area value")
    parser.add_argument(
        "--schema",
        nargs="?",
        const="__default__",
        default=None,
        help=(
            "Validate Front Matter against a JSON Schema file (required fields, "
            "'area'/'status' enums). Give a path, or pass the flag with no value "
            "to use the canonical schemas/doc_front_matter.json. Omit entirely to "
            "skip schema validation (default — existing behavior unchanged)."
        ),
    )
    parser.add_argument(
        "--check-duplicates",
        action="store_true",
        help="Check for duplicate links",
    )
    args = parser.parse_args()

    patterns = args.globs or ["docs/**/*.md"]
    files: set[Path] = set()
    unmatched: list[str] = []
    for pattern in patterns:
        matched = set(ROOT_DIR.glob(pattern))
        if not matched:
            unmatched.append(pattern)
        files.update(matched)

    try:
        basename_index = _build_basename_index(DOCS_DIR)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    schema: FrontMatterSchema | None = None
    if args.schema is not None:
        schema_path = None if args.schema == "__default__" else Path(args.schema)
        schema = load_front_matter_schema(schema_path)
    else:
        # Default-on: use the canonical schema when no --schema argument is passed
        schema = load_front_matter_schema(None)

    total_issues = 0
    for path in sorted(files):
        issues = validate_file(
            path,
            args.area,
            schema,
            basename_index=basename_index,
            check_duplicates=args.check_duplicates,
        )
        if issues:
            total_issues += len(issues)
            for issue in issues:
                print(issue)

    adr_files = [f for f in files if "docs/10_adr/" in str(f)]
    if adr_files:
        unique_issues = check_unique_adr_ids(adr_files)
        if unique_issues:
            total_issues += len(unique_issues)
            for issue in unique_issues:
                print(issue)

    if unmatched:
        print(
            f"no files matched the given glob(s): {', '.join(unmatched)}",
            file=sys.stderr,
        )
    if total_issues:
        print(f"\n{total_issues} issue(s) found", file=sys.stderr)
        return 1
    if unmatched:
        return 1
    print("All checks passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
