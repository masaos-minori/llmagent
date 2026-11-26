## Goal
- Make File MCP fail closed with one schema and one authorization model: strict shared request models as the single schema source, symlink-excluding bounded traversal, dry-run and real deletion sharing the same authorization decision, intent audit before destructive operations, and complete removal of the unenforced `supported_extensions` setting.

## Priority
Medium

## Scope
- **In-Scope**: strict-base inheritance and shared schema-generator use for the read, write, and delete file tools; symlink exclusion and node/file/cumulative-byte/per-file-byte/deadline limits with a structured truncation reason in recursive traversal; allowed-root guard moved before the dry-run branch with validation shared between dry-run and real deletion; intent audit before destructive operations that fails closed, `applied_audit_failed` reporting, and session/request/logical-call identifiers in delete audit records; complete removal of `supported_extensions` from code, posture, tests, and documentation; rejection of empty edit lists and empty `old_text`; documentation of the facts this Plan establishes.
- **Out-of-Scope**: GitHub and Git servers; the dedup state machine; the insertion-operation design (rejected — empty edit lists and empty `old_text` are rejected instead); the final documentation consistency sweep, which is mcpai012's work; behavior of the three file servers other than the items listed here.
- **Dependencies**: mcpai003 (shared strict request base and schema generator), mcpai004 (logical-call ids), mcpai005 (structured dry-run semantics), and mcpai006 (shared write-audit contract) are all closed — their Plans are archived with only deploy-hand-off rows Pending, which is the user's decision; no ordering dependency remains. mcpai012 owns the final sweep of the same File MCP documents; see Assumptions.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 9). Step 2 verification against current source confirmed the Issue's `Explicit in code` evidence: the dry-run return before the allowed-root check (`scripts/mcp_servers/file/delete_service.py:219-224`), `rglob("*")` traversal without symlink handling (`scripts/mcp_servers/file/read_business.py:219,239`), and `supported_extensions` parsed in `scripts/mcp_servers/file/write_models.py:30` while posture reports it `not_applicable` as "parsed but not enforced" (`scripts/mcp_servers/file/write_security_validation.py:93-96`). The two `Needs confirmation` claims resolved against source: runtime audit failure is weaker than the startup posture (startup reports `server.audit_log_writable` FAILED, `delete_service.py:344-368`, while runtime `_audit_log_safe` swallows failures, `delete_server.py:178-185`, and the audit record is written only after deletion, `delete_service.py:152`); the schema-generation claim is confirmed as a drift risk — `read_tools.py` builds schemas from models with a local helper, `write_tools.py` and `delete_tools.py` are hand-maintained dictionaries, and no file model inherits the strict base in `scripts/mcp_servers/request_contract.py`. One Issue claim is corrected: `config/file_write_mcp_server.toml` does not contain the `supported_extensions` key (the value is parsed with an empty default), so the config file is not a modification target.

## Problem
Delete dry-run and real execution can disagree on the allowed-root guard: `delete_directory` returns the dry-run response before `_check_not_deleting_allowed_root` runs. Recursive tree, search, and grep authorize only the base path; traversal enumerates symlinked files and a symlinked file pointing outside the allowed roots is read through `_read_grep_text` (verified: `rglob("*")` lists symlink entries; `os.walk` does not descend directory symlinks but counts symlinked files, so the escape vector is file symlinks and the node count includes directory-symlink entries). Traversal has no node, cumulative-byte, or deadline limits (per-file and result-count limits exist: `max_search_results`, `max_matches`, `max_read_bytes`). Runtime audit failure never propagates and the audit record is written after the destructive operation, so an applied delete can be unrecorded; delete audit records carry no session, request, or logical-call identifiers (`delete_server.py` uses `extract_request_context(request)[:2]`, dropping the third element). A configured extension control is parsed but not enforced, and the posture reports this openly, so the runtime contract and the configuration contract disagree. Empty edit lists and empty `old_text` are accepted.

## Reason for Change
Security-sensitive: file access outside allowed roots and unaudited destructive operations. Configuration must not claim a control the runtime does not enforce.

## Implementation Intent
Fail closed with one schema and one authorization model: share validation between dry-run and real deletion, exclude symlinks during recursion by default, bound traversal with configurable limits and a structured truncation reason, audit intent before destruction, remove `supported_extensions` completely per the owner decision, and reject empty edit lists and empty `old_text`.

## Design decisions (Path B)
- **Symlink policy**: exclude symlinks by default during recursion (owner decision, 20261126). Alternative considered: resolve and re-authorize every candidate — rejected because it requires chain-depth bounds and per-candidate authorization on every walk step; exclusion is fail-closed and simpler. Compatibility impact: traversal results no longer include symlink entries; tests that pin current `rglob` behavior change.
- **Traversal limits**: plan-proposed defaults (owner approved, 20261126), configurable through `FileReadConfig`: `max_tree_nodes = 2000`, `max_scanned_files = 5000`, `max_total_scan_bytes = 10485760`, per-file bytes reuses the existing `max_read_bytes`, `traversal_deadline_sec = 10.0`. Truncation is reported as a structured reason field, not a silent stop.
- **Empty edits**: reject empty edit lists and empty `old_text` at the model boundary; no insertion operation is designed (plan default, owner approved).
- **Audit order**: intent audit written before the destructive call and failing closed (the operation is refused when the intent record cannot be written); completion audit after verification; an applied delete whose completion audit fails is reported as `applied_audit_failed` using the shared vocabulary. This replaces the current swallow-and-continue behavior for delete only.
- **Schema source**: file request models inherit `StrictRequestModel` from `scripts/mcp_servers/request_contract.py` and tool schemas are generated with `build_input_schema()`; the local `_input_schema` helper in `read_tools.py` is replaced by the shared generator. Compatibility impact: extra request fields are rejected for read and write tools (delete already forbids them).

## Requirements
- `REQ-001`: Read, write, and delete tool schemas are generated from request models that inherit the shared strict base (`StrictRequestModel`) using the shared generator; only File-specific constraints stay local.
- `REQ-002`: Recursive traversal excludes symlinks by default; directory-symlink entries are not descended and file symlinks are not enumerated or read; loops and broken links are handled without hanging.
- `REQ-003`: Traversal enforces limits for tree nodes, scanned files, cumulative bytes, per-file bytes, and a deadline, and returns a structured truncation reason.
- `REQ-004`: The allowed-root guard runs before the dry-run branch, and dry-run and real deletion share the same validation and authorization path.
- `REQ-005`: Delete writes an intent audit before the destructive operation that fails closed; an applied delete whose completion audit fails is reported as `applied_audit_failed`; audit records carry session, request, and logical-call identifiers.
- `REQ-006`: `supported_extensions` is removed from code, posture, tests, and documentation (owner decision 20261126).
- `REQ-007`: Empty edit lists and empty `old_text` are rejected.
- `REQ-008`: Documentation records the facts this Plan establishes (symlink exclusion, traversal limits, dry-run parity, audit order); the final consistency sweep remains mcpai012's work.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261126; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/file/read_models.py` | Modify | Inherit the shared strict base; add the traversal-limit config fields with the plan defaults; add the structured truncation-reason field to traversal responses | REQ-001, REQ-003, AC-1, AC-2 | No `ConfigDict` in the file; models at lines 70, 83, 112 are plain `BaseModel` (checked in Step 2) | `tests/mcp_servers/file/test_file_read_mcp_models.py` | Verified |
| `scripts/mcp_servers/file/read_tools.py` | Modify | Replace the local `_input_schema` helper with the shared `build_input_schema()` generator | REQ-001, AC-1 | Local helper at line 32 builds schemas from models (corrected in Step 3a: line 33 was stale) | `tests/mcp_servers/file/test_file_schema_consistency.py` | Verified |
| `scripts/mcp_servers/file/write_models.py` | Modify | Inherit the shared strict base; remove the `supported_extensions` field; reject empty edit lists and empty `old_text` | REQ-001, REQ-006, REQ-007, AC-1, AC-5 | Field at line 30 parsed with empty default, no `ConfigDict`, no empty-list validation (checked in Step 2) | `tests/mcp_servers/file/test_file_write_mcp_service.py` | Verified |
| `scripts/mcp_servers/file/write_tools.py` | Modify | Generate tool schemas from the strict models with the shared generator instead of hand-maintained dictionaries | REQ-001, AC-1 | Hand-maintained `inputSchema` dicts at lines 17, 52, 101, 132 (checked in Step 2) | `tests/mcp_servers/file/test_file_schema_consistency.py` | Verified |
| `scripts/mcp_servers/file/delete_models.py` | Modify | Inherit the shared strict base (already `extra="forbid"`; align with the shared model) | REQ-001, AC-1 | `ConfigDict(extra="forbid")` at lines 74, 93 consistent with the archived sibling issue; base swap only (checked in Step 2) | `tests/mcp_servers/file/test_call_tool_validation.py` | Verified |
| `scripts/mcp_servers/file/delete_tools.py` | Modify | Generate tool schemas from the strict models with the shared generator | REQ-001, AC-1 | Hand-maintained `inputSchema` dicts at lines 20, 51 (checked in Step 2) | `tests/mcp_servers/file/test_file_schema_consistency.py` | Verified |
| `scripts/mcp_servers/file/read_business.py` | Modify | Exclude symlinks during `rglob` traversal; enforce node, scanned-file, cumulative-byte, per-file-byte, and deadline limits; return the structured truncation reason | REQ-002, REQ-003, AC-2 | `rglob("*")` at lines 219, 239 with no symlink handling; verified behavior: `rglob` lists symlink entries, `os.walk` counts symlinked files without descending directory symlinks (checked in Step 2) | `tests/mcp_servers/file/test_read_service.py` | Verified |
| `scripts/mcp_servers/file/read_static_helpers.py` | Modify | Make the traversal helpers (`build_tree`, `count_tree_nodes`, `has_depth_limit`) symlink-excluding and limit-aware | REQ-002, REQ-003, AC-2 | Helpers at lines 21, 54, 96; `build_tree` enumerates entries via `iterdir()` without symlink exclusion (corrected in Step 3a: the dry-run scan walk is `_scan_directory_for_dry_run` in `delete_service.py`, not in this file) | `tests/mcp_servers/file/test_read_service.py` | Verified |
| `scripts/mcp_servers/file/read_service.py` | Modify | Wire the new traversal-limit config fields from `FileReadConfig` through `build_service()` into `ReadFileService` (amendment, owner-approved 20261126: the limits cannot reach the traversal code without this; the file was not in the frozen table) | REQ-003, AC-2 | `build_service()` passes only `max_read_bytes`, `max_depth`, `max_files_per_batch` to `ReadFileService.__init__`; the seq 01 config fields have no consumer path to the traversal code (checked 20261126 during seq 07 Step 3a) | `tests/mcp_servers/file/test_read_service.py` | Verified |
| `scripts/mcp_servers/file/delete_service.py` | Modify | Move the allowed-root guard before the dry-run branch and share validation between dry-run and real deletion; write the intent audit before the destructive call (fail closed); report `applied_audit_failed` when the completion audit fails after an applied delete | REQ-004, REQ-005, AC-3, AC-4 | Dry-run return at lines 219-220 precedes `_check_not_deleting_allowed_root` at line 224; audit written only after deletion at line 152; audit-write errors logged but never propagated (checked in Step 2) | `tests/mcp_servers/file/test_delete_service.py` | Verified |
| `scripts/mcp_servers/file/delete_server.py` | Modify | Include session, request, and logical-call identifiers in delete audit records via the shared audit-record contract | REQ-005, AC-4 | `extract_request_context(request)[:2]` drops the third element (the logical-call id) at line 194 (corrected in Step 3a: line 196 was stale); `_audit_log_safe` swallows failures at lines 178-185 (checked in Step 2) | `tests/mcp_servers/file/test_file_server_audit_records.py` | Verified |
| `scripts/mcp_servers/file/write_security_validation.py` | Modify | Remove the `server.supported_extensions` posture check | REQ-006, AC-5 | Check at lines 93-96 reports `not_applicable` "parsed but not enforced" (checked in Step 2) | `tests/mcp_servers/file/test_file_security_validation.py` | Verified |
| `scripts/mcp_servers/file/write_server.py` | Modify | Remove `supported_extensions_count` from the health view | REQ-006, AC-5 | Health view line 75 reads `cfg.supported_extensions` (checked in Step 2 via consumer scan) | `tests/mcp_servers/file/test_file_write_health_posture.py` | Verified |
| `scripts/shared/security/posture_contract.py` | Modify | Remove `server.supported_extensions` from the `file_write` check inventory | REQ-006, AC-5 | Check id present in the `file_write` inventory at line 82 (checked in Step 2 via consumer scan) | `tests/shared/test_security_posture_contract.py` | Verified |
| `tests/mcp_servers/file/test_read_service.py` | Modify | Add symlink-exclusion tests (external file and directory symlinks, chain, loop, broken link) and limit tests (large flat directory, many-small-files, cumulative-byte, deadline) with the structured truncation reason | REQ-002, REQ-003, AC-2 | Existing file covers traversal without symlink cases (checked in Step 2) | itself | Verified |
| `tests/mcp_servers/file/test_delete_service.py` | Modify | Add allowed-root delete dry-run parity tests and audit fault-injection tests (audit permission, read-only filesystem, disk-full) | REQ-004, REQ-005, AC-3, AC-4 | Existing file has no dry-run-vs-real authorization-parity or audit-fault cases (checked in Step 2) | itself | Verified |
| `tests/mcp_servers/file/test_file_server_audit_records.py` | Modify | Assert the session, request, and logical-call identifiers in delete audit records | REQ-005, AC-4 | Existing file covers audit records without the identifier fields (checked in Step 2) | itself | Verified |
| `tests/mcp_servers/file/test_file_security_validation.py` | Modify | Remove the pinned `server.supported_extensions` check assertions | REQ-006, AC-5 | Pins the check at lines 47, 333, 341 and constructs configs with the field at lines 258, 264, 394 (checked in Step 2 via consumer scan) | itself | Verified |
| `tests/mcp_servers/file/test_file_write_health_posture.py` | Modify | Remove the pinned `server.supported_extensions` posture and health-view assertions | REQ-006, AC-5 | Pins the check at lines 32, 103, 128 (checked in Step 2 via consumer scan) | itself | Verified |
| `tests/shared/test_security_posture_contract.py` | Modify | Update the `file_write` inventory pin that includes `server.supported_extensions` | REQ-006, AC-5 | Inventory pin at line 74 (checked in Step 2 via consumer scan) | itself | Verified |
| `tests/mcp_servers/file/test_file_schema_consistency.py` | Create | New file: schema-and-model consistency tests for all file tools (runtime and discovery schemas match, extra fields rejected) | REQ-001, AC-1 | New file; `tests/mcp_servers/file/` exists and `test_mcp_tools_validation.py` checks tool names only, not schema-model consistency (checked in Step 2) | itself | Verified |
| `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` | Modify | Record the symlink-exclusion policy and the traversal limits as failure behavior | REQ-008, AC-6 | File-read section describes size and result limits only, no symlink or traversal-limit policy (checked in Step 2) | `uv run python tools/check_docs_quality.py` | Verified |
| `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | Modify | Record the dry-run/real-deletion authorization parity, the intent-audit order, and the `supported_extensions` removal | REQ-004, REQ-005, REQ-006, REQ-008, AC-3, AC-4, AC-6 | Write/delete sections describe postconditions and root protection without the dry-run parity and audit-order facts this Plan establishes (checked in Step 2) | `uv run python tools/check_docs_quality.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories, glob
patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/request_contract.py` | The shared strict base (`StrictRequestModel`, line 34) and generator (`build_input_schema`, line 44) the file models and tools must use | REQ-001 |
| `scripts/shared/write_outcome.py` | The shared write-audit vocabulary (`applied_audit_failed`) and field builder the delete audit path applies | REQ-005 |
| `scripts/mcp_servers/server.py` | `extract_request_context()` (line 263, corrected in Step 3a) returns the logical-call identifier as its third element | REQ-005 |
| `scripts/mcp_servers/file/common.py` | `FileSecurityMixin._resolve_safe()` and `validate_file_security_base()` are the authorization base the traversal and delete paths share; consumer scan found no change needed here — recorded as a reference row, not a target | REQ-004 |
| `tests/mcp_servers/file/test_file_common.py` | Existing authorization tests that must keep passing with the shared validation path | REQ-004 |

## Acceptance Criteria
- AC-1: Runtime and discovery schemas match for all file tools, and all file request models inherit the shared strict base (REQ-001).
- AC-2: Recursive operations cannot read or enumerate data outside allowed roots through symlinks; traversal stops at every configured limit and reports a structured truncation reason (REQ-002, REQ-003).
- AC-3: Dry-run and real deletion give the same authorization decision; the allowed root cannot be deleted in any mode (REQ-004).
- AC-4: Intent-audit failure prevents deletion; an applied delete plus completion-audit failure is reported as `applied_audit_failed`; audit records carry the three identifiers (REQ-005).
- AC-5: `supported_extensions` is completely removed from code, posture, tests, and documentation, and empty edit lists and empty `old_text` are rejected (REQ-006, REQ-007).
- AC-6: The File MCP documentation states the symlink policy, traversal limits, dry-run parity, and audit order as failure behavior (REQ-008).

## Tests
- Symlink tests: external file and directory symlinks, symlink chain, loop, and broken link (REQ-002).
- Limit tests: large flat directory, many-small-files, cumulative-byte limit, deadline, structured truncation reason (REQ-003).
- Allowed-root delete dry-run parity tests; audit permission, read-only filesystem, and disk-full fault injection (REQ-004, REQ-005).
- Schema and model consistency tests for all file tools (REQ-001).
- Vocabulary test that `applied_audit_failed` is reported when the completion audit fails after an applied delete (REQ-005).
- Run ruff, mypy, import-linter, bandit, and the full test suite per `rules/toolchain.md`.

## Documentation Impact
Yes. `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` and `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` (per `docs/00_index.md` "Document References by Task" → MCP) record the symlink policy, traversal limits, dry-run parity, audit order, and the extension removal as failure behavior, not as a blanket guarantee (REQ-008). The final consistency sweep of the same documents is mcpai012's work; this Plan writes only the facts it establishes.

## Assumptions
- Owner decisions recorded on 20261126 for this cycle: `supported_extensions` is removed completely (not enforced); symlinks are excluded by default during recursion; the plan may propose the traversal-limit defaults and reject empty edit lists and empty `old_text` without designing an insertion operation.
- The traversal-limit defaults listed in Design decisions are proposed values, configurable through `FileReadConfig`; they do not add new posture checks, so the posture inventory change is limited to the `supported_extensions` removal.
- mcpai012's documentation plan is compatible with this Plan on the two File MCP documents: this Plan writes the facts it establishes, mcpai012 performs the final consistency sweep afterward.
- `config/file_write_mcp_server.toml` is not a target: the `supported_extensions` key is absent from the file (corrected in Step 2); removal touches only code, posture, and tests.
- The consumer scan for `supported_extensions` (11 test candidates plus `posture_contract.py` and `write_server.py`) is fully recorded as target rows; no candidate is left unaccounted.
- Step 3a correction (20261126): the row-8 phrase "the dry-run scan walk" was a misattribution — the dry-run scan (`_scan_directory_for_dry_run`) lives in `delete_service.py`, not in `read_static_helpers.py`; row 8's symlink-exclusion target is `build_tree` (line 21). The delete dry-run scan is not a symlink-exclusion target: `os.walk` does not descend directory symlinks and the scan only counts, so the escape vector remains the read traversal path per the Problem analysis; REQ-002's test scope (`test_read_service.py`) is unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | N/A: the Issue's three `Unresolved Questions` (extension decision, symlink policy, limit values and insertion design) were resolved by owner decision on 20261126 and are recorded in Assumptions | — | — | — |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/file/read_models.py` | Modify | Medium (6 importers within the file package) | 0 | High (single author, 49 commits in `scripts/mcp_servers/file/`) | not applicable (rsynced) |
| `scripts/mcp_servers/file/read_tools.py` | Modify | Low | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_models.py` | Modify | Medium (4 importers) | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_tools.py` | Modify | Low | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_models.py` | Modify | Low (3 importers) | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_tools.py` | Modify | Low | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/read_business.py` | Modify | Medium (read_service and the read dispatch path) | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/read_static_helpers.py` | Modify | Low (2 importers) | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_service.py` | Modify | Medium (delete dispatch and startup posture) | 3 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_server.py` | Modify | Medium (health endpoint test imports it) | 6 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_security_validation.py` | Modify | Low (1 importer) | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_server.py` | Modify | Medium | 6 | High (single author) | not applicable (rsynced) |
| `scripts/shared/security/posture_contract.py` | Modify | Medium (shared inventory consumed by all posture domains and its test) | 2 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/file/test_read_service.py` | Modify | Low | 0 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/file/test_delete_service.py` | Modify | Low | 3 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/file/test_file_server_audit_records.py` | Modify | Low | 0 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/file/test_file_security_validation.py` | Modify | Low | 0 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/file/test_file_write_health_posture.py` | Modify | Low | 0 | High (single author) | not applicable (rsynced) |
| `tests/shared/test_security_posture_contract.py` | Modify | Low | 2 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/file/test_file_schema_consistency.py` | Create | Low | N/A (new file) | High (single author) | not applicable (rsynced) |
| `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` | Modify | Low | 3 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | Modify | Low | 1 | High (single author) | not applicable (docs not deployed) |

## Design
- **One authorization model**: the allowed-root guard and path validation run once, before the dry-run branch, so dry-run and real deletion cannot disagree (REQ-004). The shared validation stays in the service layer; `common.py` is not modified.
- **Symlink exclusion at traversal boundaries**: `read_business.py` and `read_static_helpers.py` skip entries whose `is_symlink()` is true; broken links are skipped without raising, and a symlink loop cannot occur because symlinks are never descended (REQ-002). The structured truncation reason is a response field, so callers can distinguish "stopped by limit" from "complete".
- **Limit ownership**: limits are configuration-owned (`FileReadConfig` defaults per the plan proposal) and enforced in the traversal helpers, not in the servers, so all three recursive paths (tree, search, grep) share one enforcement point (REQ-003).
- **Audit order for delete**: intent record → destructive call → postcondition verification → completion record. Intent-record failure refuses the operation before any filesystem change; completion-record failure after an applied delete reports `applied_audit_failed` through the shared vocabulary (REQ-005). The `_audit_log_safe` swallow remains for non-destructive audit paths only.
- **Predictable fallout**: no target file crosses the 24576 B module-size gate at its current size (largest: `delete_service.py` 14488 B), so no split row is required. Pinned counts: the posture-inventory pins in `test_file_security_validation.py`, `test_file_write_health_posture.py`, and `tests/shared/test_security_posture_contract.py` are target rows. No tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected. No generated-reference domain is touched. Consumer scan for `supported_extensions` recorded every candidate as a target row; `common.py` is `not affected` as a modification target (reference row).
- **Validation quality baseline**: `radon cc -s` reports all Python targets at grade A except `validate_file_write_security` at B(9) in `write_security_validation.py`. `vulture scripts/mcp_servers/file/ --min-confidence 80` reports no findings. `bandit -r scripts/mcp_servers/file/ -c pyproject.toml` reports 3 low-severity `B101` asserts, none medium or high. `diff-cover coverage.xml --compare-branch=master` currently reports no lines with coverage information (clean tree at Plan creation); the implementation must reach the `rules/toolchain.md` threshold of 90% on changed lines.
- **Path B architecture analysis**: grimp import graph over `mcp_servers` — no cycles inside `mcp_servers.file`; import-linter contracts all kept (6/6). `pip-audit` reports two external findings unrelated to File MCP (`wcmatch` 8.5.2 → 11.2, `werkzeug` 3.1.8 → 3.1.9); recorded here, not a target of this Plan.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table.

1. **Phase 1: Schema tests first, then strict base and shared generator**
   - [ ] Write the schema-and-model consistency tests for all file tools against the unmodified tools and models (REQ-001, AC-1; `tests/mcp_servers/file/test_file_schema_consistency.py`)
   - [ ] Make the read, write, and delete request models inherit `StrictRequestModel` and switch the tool schemas to `build_input_schema()` (REQ-001, AC-1; `scripts/mcp_servers/file/read_models.py`, `scripts/mcp_servers/file/write_models.py`, `scripts/mcp_servers/file/delete_models.py`, `scripts/mcp_servers/file/read_tools.py`, `scripts/mcp_servers/file/write_tools.py`, `scripts/mcp_servers/file/delete_tools.py`)
2. **Phase 2: Symlink exclusion and traversal limits**
   - [ ] Write the symlink (external file and directory, chain, loop, broken link) and limit tests first (REQ-002, REQ-003, AC-2; `tests/mcp_servers/file/test_read_service.py`)
   - [ ] Add the limit config fields and the structured truncation-reason field (REQ-003, AC-2; `scripts/mcp_servers/file/read_models.py`)
   - [ ] Exclude symlinks and enforce the limits in the traversal paths and helpers (REQ-002, REQ-003, AC-2; `scripts/mcp_servers/file/read_business.py`, `scripts/mcp_servers/file/read_static_helpers.py`)
3. **Phase 3: Delete dry-run parity**
   - [ ] Write the allowed-root dry-run parity tests first (REQ-004, AC-3; `tests/mcp_servers/file/test_delete_service.py`)
   - [ ] Move the allowed-root guard before the dry-run branch and share validation between dry-run and real deletion (REQ-004, AC-3; `scripts/mcp_servers/file/delete_service.py`)
4. **Phase 4: Audit order and identifiers**
   - [ ] Write the audit fault-injection tests first (audit permission, read-only filesystem, disk-full) (REQ-005, AC-4; `tests/mcp_servers/file/test_delete_service.py`)
   - [ ] Implement the intent audit before the destructive call (fail closed) and `applied_audit_failed` reporting (REQ-005, AC-4; `scripts/mcp_servers/file/delete_service.py`)
   - [ ] Add the session, request, and logical-call identifiers to delete audit records (REQ-005, AC-4; `scripts/mcp_servers/file/delete_server.py`, `tests/mcp_servers/file/test_file_server_audit_records.py`)
5. **Phase 5: `supported_extensions` removal**
   - [ ] Remove the field, the posture check, the health-view entry, and the inventory id, and update the pinned tests (REQ-006, AC-5; `scripts/mcp_servers/file/write_models.py`, `scripts/mcp_servers/file/write_security_validation.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/shared/security/posture_contract.py`, `tests/mcp_servers/file/test_file_security_validation.py`, `tests/mcp_servers/file/test_file_write_health_posture.py`, `tests/shared/test_security_posture_contract.py`)
   - [ ] Reject empty edit lists and empty `old_text` with model-boundary validation and tests (REQ-007, AC-5; `scripts/mcp_servers/file/write_models.py`, `tests/mcp_servers/file/test_file_write_mcp_service.py`)
6. **Phase 6: Documentation, validation, and deployment**
   - [ ] Record the symlink policy, traversal limits, dry-run parity, audit order, and extension removal in the two File MCP documents (REQ-008, AC-6; `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`)
   - [ ] Run the full validation sequence (`rules/toolchain.md`: format → lint → type → arch → security → test → coverage) and the docs gates `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp` (REQ-008)
   - [ ] Hand off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (REQ-001..REQ-008)

### Release units
N/A: no release unit — each phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/file/read_models.py`, `read_tools.py`, `write_models.py`, `write_tools.py`, `delete_models.py`, `delete_tools.py` | Unit (schema-model consistency) | `uv run pytest tests/mcp_servers/file/test_file_schema_consistency.py -v` | Runtime and discovery schemas match for all file tools; extra fields rejected |
| `scripts/mcp_servers/file/read_business.py`, `read_static_helpers.py` | Integration on a temporary directory with symlinks | `uv run pytest tests/mcp_servers/file/test_read_service.py -v` | Symlink entries excluded; limits stop traversal with a structured reason |
| `scripts/mcp_servers/file/delete_service.py` | Unit plus fault injection | `uv run pytest tests/mcp_servers/file/test_delete_service.py -v` | Dry-run and real deletion agree; intent-audit failure refuses the delete; `applied_audit_failed` reported |
| `scripts/mcp_servers/file/delete_server.py` | Unit | `uv run pytest tests/mcp_servers/file/test_file_server_audit_records.py -v` | Audit records carry the three identifiers |
| `scripts/shared/security/posture_contract.py` and the write posture files | Unit | `uv run pytest tests/shared/test_security_posture_contract.py tests/mcp_servers/file/test_file_security_validation.py tests/mcp_servers/file/test_file_write_health_posture.py -v` | `server.supported_extensions` absent from inventory, posture, and health view |
| All Python targets | Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |
| `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | Documentation consistency | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | No findings |

## Risks
- **Risk**: making read and write models strict rejects request fields that callers currently send harmlessly → **Mitigation**: the change is the point of REQ-001; blast radius measured through the consumer scan (file-package importers and the existing validation tests), and the schema-consistency tests pin the new contract before the switch.
- **Risk**: symlink exclusion changes traversal results for callers that relied on symlink entries → **Mitigation**: the structured truncation/skip reporting makes the difference visible; the policy is the owner decision recorded in Assumptions.
- **Risk**: intent audit failing closed can refuse deletes on an audit path that is writable at startup but fails at runtime (disk full) → **Mitigation**: this is the intended fail-closed behavior per the shared write-audit contract; fault-injection tests cover audit permission, read-only filesystem, and disk-full.
- **Risk**: removing `server.supported_extensions` changes the shared posture contract inventory consumed by all domains → **Mitigation**: the change is additive-negative to one domain tuple only; the pinned inventory test is a target row.
- **Risk**: `Bus Factor` is high for every target (single author across `scripts/mcp_servers/file/`) → **Mitigation**: keep each phase independently revertable and land the tests before the implementation.
- **Risk**: overlap with mcpai012 on the two File MCP documents → **Mitigation**: judged compatible (this Plan writes only the facts it establishes; mcpai012 sweeps afterward), recorded in Assumptions.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Schema tests first, then strict base and shared generator | Completed | — | 20261126-201554 | — |
| 2 | Symlink exclusion and traversal limits | Completed | — | 20261126-201554 | — |
| 3 | Delete dry-run parity | Completed | — | 20261126-201554 | — |
| 4 | Audit order and identifiers | Completed | — | 20261126-201554 | — |
| 5 | `supported_extensions` removal and empty-edit rejection | Completed | — | 20261126-201554 | — |
| 6 | Documentation, validation, and deploy hand-off | In Progress | — | — | deploy is the user's decision Docs rows (seq 21, 22) complete and the docs checkers pass; the full validation sequence passes (ruff format/check, mypy, lint-imports, ast-grep, bandit, pre-commit, reference-drift, cited-adr-tests) and the end-of-batch full-suite run passed 15774 passed / 5 skipped with diff-cover 100% on changed lines. Remaining: commit + push, then deploy hand-off is the user's decision. Intermittent flaky failures observed in 3 unrelated tests under -n logical (eventbus x2, integration session sqlite), all pass serially. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at Plan creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-171048_01_scripts_mcp_servers_file_read_models.py.md` | 1, 2 | Procedure | Completed | — | — |
| `implementations/20261126-171048_02_scripts_mcp_servers_file_read_tools.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-171048_03_scripts_mcp_servers_file_write_models.py.md` | 1, 5 | Procedure | Completed | — | — |
| `implementations/20261126-171048_04_scripts_mcp_servers_file_write_tools.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-171048_05_scripts_mcp_servers_file_delete_models.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-171048_06_scripts_mcp_servers_file_delete_tools.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-171048_07_scripts_mcp_servers_file_read_business.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-171048_08_scripts_mcp_servers_file_read_static_helpers.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-171048_09_scripts_mcp_servers_file_delete_service.py.md` | 3, 4 | Procedure | Completed | — | — |
| `implementations/20261126-171048_10_scripts_mcp_servers_file_delete_server.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-171048_11_scripts_mcp_servers_file_write_security_validation.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261126-171048_12_scripts_mcp_servers_file_write_server.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261126-171048_13_scripts_shared_security_posture_contract.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261126-171048_14_tests_mcp_servers_file_test_read_service.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-171048_20_tests_mcp_servers_file_test_file_schema_consistency.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-171048_21_docs_22_mcp_mcp_04_01_web-search-file-read-github.md.md` | 6 | Procedure | Completed | — | — |
| `implementations/20261126-171048_22_docs_22_mcp_mcp_04_02_file-write-file-delete-shell.md.md` | 6 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-065258
- **Related target files**: `scripts/mcp_servers/file/read_models.py`, `scripts/mcp_servers/file/read_tools.py`, `scripts/mcp_servers/file/write_models.py`, `scripts/mcp_servers/file/write_tools.py`, `scripts/mcp_servers/file/delete_models.py`, `scripts/mcp_servers/file/delete_tools.py`, `scripts/mcp_servers/file/read_business.py`, `scripts/mcp_servers/file/read_static_helpers.py`, `scripts/mcp_servers/file/delete_service.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/write_security_validation.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/shared/security/posture_contract.py`, `tests/mcp_servers/file/test_read_service.py`, `tests/mcp_servers/file/test_delete_service.py`, `tests/mcp_servers/file/test_file_server_audit_records.py`, `tests/mcp_servers/file/test_file_security_validation.py`, `tests/mcp_servers/file/test_file_write_health_posture.py`, `tests/shared/test_security_posture_contract.py`, `tests/mcp_servers/file/test_file_schema_consistency.py`, `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `read_tools.py:33`, `write_tools.py:17`, `delete_tools.py:20`, `request_contract.py:34,44` | `scripts/mcp_servers/file/read_models.py`, `read_tools.py`, `write_models.py`, `write_tools.py`, `delete_models.py`, `delete_tools.py` | Phase 1 | AC-1 | `tests/mcp_servers/file/test_file_schema_consistency.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; `read_business.py:219,239`; verified `rglob` symlink behavior (Step 2) | `scripts/mcp_servers/file/read_business.py`, `read_static_helpers.py` | Phase 2 | AC-2 | `tests/mcp_servers/file/test_read_service.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; no node/cumulative-byte/deadline limits found in Step 2 | `scripts/mcp_servers/file/read_models.py`, `read_business.py`, `read_static_helpers.py` | Phase 2 | AC-2 | `tests/mcp_servers/file/test_read_service.py` | Confirmed by repository evidence |
| REQ-004 | Problem; `delete_service.py:219-224` | `scripts/mcp_servers/file/delete_service.py` | Phase 3 | AC-3 | `tests/mcp_servers/file/test_delete_service.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; `delete_service.py:152`, `delete_server.py:178-185,194` | `scripts/mcp_servers/file/delete_service.py`, `delete_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/file/test_delete_service.py`, `tests/mcp_servers/file/test_file_server_audit_records.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; `write_models.py:30`, `write_security_validation.py:93-96`, `posture_contract.py:82` | `scripts/mcp_servers/file/write_models.py`, `write_security_validation.py`, `write_server.py`, `scripts/shared/security/posture_contract.py` | Phase 5 | AC-5 | `tests/mcp_servers/file/test_file_security_validation.py`, `tests/mcp_servers/file/test_file_write_health_posture.py`, `tests/shared/test_security_posture_contract.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; no empty-edit validation found in Step 2 | `scripts/mcp_servers/file/write_models.py` | Phase 5 | AC-5 | `tests/mcp_servers/file/test_file_write_mcp_service.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact | `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | Phase 6 | AC-6 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-171048 -->