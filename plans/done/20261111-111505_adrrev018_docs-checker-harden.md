## Goal
Extend the existing documentation checkers so the defect classes found in the ADR review fail automatically in CI: an inventory-style table of the `eventbus_08` shape, history phrasings and plan IDs, the specific free-text contradictions that were fixed, and a Known Deviation entry that cites no ledger ID, each with a regression test, without writing a parallel tool and without failing the current corpus.

## Priority
Medium

## Scope
- **In-Scope**: Widen `_INDEX_TABLE_HEADER_RE` in `tools/check_docs_content_policy.py` (after extracting helpers to stay within the module-size baseline); add rules to `config/doc_quality_rules.json` for history phrasings, plan IDs, and the lexical signatures of the resolved contradictions (DLQ threshold operator, offset monotonicity, empty-token startup statement); add a check to `tools/check_known_deviation_sync.py` that a Known Deviations bullet cites a ledger ID; register the four decision targets (posture-failure handling, empty-token handling, DLQ promotion threshold, offset monotonicity) in `config/documentation_canonical_sources.toml`; regression tests for each; `governance_04` and `tools/TOOL_DESCRIPTIONS.md` descriptions.
- **Out-of-Scope**: Fixing the documents the checkers flag (the owning Plans); a semantic or NLP detector for arbitrary free-text contradictions (the registry maps decision targets to sources and cannot compare statements; only stable lexical signatures are enforced); exempting generated blocks differently (ADR-015 and GV-018 keep guarded blocks exempt); changing ADR content or governance rules; CI or pre-commit wiring (`check_docs_quality` already runs as a pre-commit hook and `check_docs_content_policy.py --strict` in CI).
- **Dependencies**: New rules must start green, so this Plan lands after the plans that clean the corpus and fix the contradictions; each is a real ordering dependency.
  - **Depends on**: plans/20261111-110144_adrrev017_docs-history-wording.md | phase all | removes the history wording and plan IDs that the new rules flag.
  - **Depends on**: plans/20261111-104147_adrrev015_adr-index-matrix.md | phase all | fixes ADR-006 INV-13 ("exceeded max_retry") and the index "strictly monotonic" wording that two new rules flag.
  - **Depends on**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md | phase all | fixes the empty-token sentences in `mcp_02_02` and `mcp_06_14` that a new rule flags and creates the authentication ADR.

## Background
Verification (2026-11-11) showed the `eventbus_08` miss has two causes: the table lies inside an `AUTO-GENERATED` block, which `check_docs_content_policy.py` exempts by design (ADR-015, GV-018), and `_INDEX_TABLE_HEADER_RE` only matches a first column of `Function`, `Method`, or `Class`, so a hand-written `| File | Class/Function | Signature | Summary |` table would pass (a broadened pattern finds none in the current corpus outside generated blocks). Forbidden patterns live in `config/doc_quality_rules.json`, run by `tools/check_docs_quality.py` (a pre-commit hook); the rule `history_marker_in_active_doc` covers `(Added <date>`, `done/` paths, `REQ-NNN`, Resolved bullets, strikethrough, and Traceability headings but not "Amendment (", "superseded", "replaces the previous", "was removed", "formerly", or plan IDs. A generic plan-ID shape matches 11 distinct plan IDs in `docs/` and nothing in `docs/00_governance/`. `VALID_CLAIM_TYPES` already holds 13 claim types; the four requested topics are decision targets, not claim types. The Known Deviation sync check ran against an empty ledger (all 15 ADRs say "Not applicable"), reports a dangling ID only as a WARNING, and does not check a bullet that has no ID. The four tools `check_docs_content_policy.py`, `check_docs_quality.py`, and the two canonical-source tools are grandfathered at their sizes in `tools/check_module_size_tools_baseline.txt`, so any growth fails the gate.

## Problem
- A Blocking rule that a document passes untouched means an exemption or a pattern gap, and both make it unreliable.
- Free-text contradictions are invisible to a check that compares only registered sources, so the same defect classes can return after the other fixes in this batch.
- History wording and plan IDs pass the forbidden-pattern checks, and a Known Deviation entry without a ledger ID cannot be checked at all.

## Reason for Change
Manual review does not scale; each major finding of the ADR review was a contradiction that tooling could in principle detect. The Plan lands after the corpus is clean so the new rules start green.

## Implementation Intent
Extend the existing checkers and the existing rule file; add no new checker. Reproduce each miss first with a failing fixture, then fix it. Keep every new rule specific enough to have no false positive on the current corpus, and state in the documentation which defect classes are covered lexically and which are not.

## Requirements
- `REQ-001`: `_INDEX_TABLE_HEADER_RE` also matches a header whose first column is `File` or `Module`, whose first cell may be `Class/Function`-shaped, and whose last column is `Summary`, so the `eventbus_08` table shape outside a guarded block is flagged while guarded blocks stay exempt.
- `REQ-002`: `config/doc_quality_rules.json` gains rules for history phrasings (an Amendment heading with a date, "superseded <date>", "replaces the previous", "was/were removed (at|in|by) ...", "formerly") and for plan IDs (`\b[A-Za-z]{4,12}[0-9]{3}\b`), with a severity the maintainer confirms (default ERROR), and no `exempt_historical_context`.
- `REQ-003`: `config/doc_quality_rules.json` gains one rule per resolved contradiction class with a stable lexical signature: the DLQ promotion operator ("exceeded max_retry"), offset monotonicity ("strictly monotonic" applied to offsets), and the empty-token startup statement ("starts, but health checks fail" / "skips the authentication check"); each is verified to have no match on the corpus once the owning Plans have landed.
- `REQ-004`: `tools/check_known_deviation_sync.py` reports an ERROR for an ADR `## Known Deviations` bullet that cites no Known Issue ID (the only exempt text is the "Not applicable" marker), and tests pin the existing behaviors (dangling ID WARNING, uncited target ADR WARNING, resolved bullet ERROR).
- `REQ-005`: The four decision targets are registered in `config/documentation_canonical_sources.toml` with their owning ADR as normative source (ADR-004 for posture-failure handling, ADR-017 or ADR-007 for empty-token handling, ADR-006 for the DLQ promotion threshold and for offset monotonicity), valid for `check_canonical_source_registry.py` (Accepted status, single normative source).
- `REQ-006`: Each defect class has a regression test that re-introduces it and asserts failure: an inventory table of the `eventbus_08` shape, each history phrasing, a plan ID, each lexical contradiction signature, and a Known Deviation bullet without an ID.
- `REQ-007`: `governance_04` and `tools/TOOL_DESCRIPTIONS.md` describe the extended checks (intent, scope, failure behavior, and the explicit limit that free-text contradictions are covered only by lexical signatures), and the module-size baseline records the reduced size of `check_docs_content_policy.py` after extraction.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_docs_content_policy.py` | Modify | Widen `_INDEX_TABLE_HEADER_RE` (line 47) after moving existing helpers out so the file does not grow past its baseline (33240 bytes) | REQ-001 / AC-1 | `_INDEX_TABLE_HEADER_RE` requires `(?:Function\|Method\|Class)` first and `(?:Signature\|Description)` last; a direct test returns False for the `eventbus_08` header; guarded-block exemption at lines 124-137 (checked in Step 2) | `tests/tools/test_check_docs_content_policy.py` | Verified |
| `tools/_docs_content_policy_helpers.py` | Create | Receive helpers extracted with `module_nodes.py` so `check_docs_content_policy.py` shrinks before the change (the final name and node list are chosen at extraction, UNK-03) | REQ-001, REQ-007 / AC-1, AC-7 | `tools/check_module_size_tools_baseline.txt` grandfathers `check_docs_content_policy.py` at 33240 bytes and growth fails; `tools/module_nodes.py` exists (checked in Step 3). New file; `tools/` exists | `tests/tools/test_check_docs_content_policy.py`, `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Verified |
| `tools/check_module_size_tools_baseline.txt` | Modify | Lower the recorded size of `check_docs_content_policy.py` to its size after extraction (the baseline only shrinks) | REQ-007 / AC-7 | Line `check_docs_content_policy.py	33240` (checked in Step 3) | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Verified |
| `config/doc_quality_rules.json` | Modify | Add the history-phrasing, plan-ID, and contradiction-signature rules | REQ-002, REQ-003 / AC-2, AC-3 | Six existing named rules (`history_marker_in_active_doc`, ...) with `pattern`, `severity`, `description`; no path scoping (checked in Step 2) | `tests/tools/test_check_docs_quality.py` | Verified |
| `tools/check_known_deviation_sync.py` | Modify | Add the "bullet without a ledger ID" ERROR check (21410 bytes, headroom 3166 bytes to the 24576 gate) | REQ-004 / AC-4 | Checks 1-4 documented in the module docstring; a dangling ID is a WARNING and exit code 1 only on ERROR (lines 12-21, 544); every ADR Known Deviations section reads "Not applicable" (checked in Step 2) | `tests/tools/test_check_known_deviation_sync.py` | Verified |
| `config/documentation_canonical_sources.toml` | Modify | Register the four decision targets with their normative ADR sources | REQ-005 / AC-5 | Registry holds 10 `[[canonical_sources]]` entries (Step 3a: the Plan said 11), none ADR-sourced; claim types `runtime-behavior` and `security-policy` are valid (`VALID_CLAIM_TYPES`) (checked in Step 2) | `uv run python tools/check_canonical_source_registry.py`, `tests/tools/test_check_canonical_source_registry.py` | Verified |
| `tests/tools/test_check_docs_content_policy.py` | Modify | Add the fixture with the `eventbus_08` table shape (flagged outside a guarded block, exempt inside one) | REQ-001, REQ-006 / AC-1, AC-6 | File exists and tests the content-policy checker (checked in Step 3) | itself | Verified |
| `tests/tools/test_check_docs_quality.py` | Modify | Add regression tests per new rule using the existing `_run_live_rule(...)` helper (line 471 pattern) | REQ-002, REQ-003, REQ-006 / AC-2, AC-3, AC-6 | Existing live-rule tests for `history_marker_in_active_doc` at lines 441-480 (checked in Step 3) | itself | Verified |
| `tests/tools/test_check_known_deviation_sync.py` | Modify | Add tests for the new ERROR and pin the existing WARNING and ERROR behaviors | REQ-004, REQ-006 / AC-4, AC-6 | `test_unresolvable_id_is_reported_as_dangling` (line 104) and `test_uncited_target_adr_is_reported` (line 307) exist (checked in Step 3) | itself | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Describe the extended GV-018 table pattern, the new custom rules, and the Known Deviation check, including the lexical-only limit | REQ-007 / AC-7 | Custom-rules paragraph at lines 38-43 and GV-018 row at line 297 (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Update the descriptions of the changed tools and list the new helper module | REQ-007 / AC-7 | Documents every `tools/*.py`; `check_tool_descriptions_sync.py` enforces it (checked in Step 3) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_docs_quality.py` | Loads `config/doc_quality_rules.json` and runs the rules; at its baseline size it must not change (JSON-only rule additions) | REQ-002, REQ-003 |
| `tools/check_canonical_source_registry.py` | `VALID_CLAIM_TYPES`, ADR-status check, single-normative-source rule | REQ-005 |
| `tools/check_canonical_source_conflicts.py` | Semantic registry checks (`CANONICAL-*`); at baseline size, unchanged | REQ-005 |
| `tools/module_nodes.py` | `measure` and `extract` commands for the extraction | REQ-001, REQ-007 |
| `tools/check_module_size.py` | The size gate and baseline rules | REQ-007 |
| `tools/_docs_consistency_lib.py` | Shared `Issue` and `report_and_exit` used by the checkers | REQ-004 |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | States the guarded-block exemption that must stay | REQ-001 |
| `docs/24_eventbus/eventbus_08_reference_api.md` | The generated table of the `eventbus_08` shape (exempt); the fixture must not depend on it | REQ-001 |
| `docs/00_governance/governance_01_documentation-policy.md` | Current-Specification-Only Policy the rules enforce | REQ-002 |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Owner of the DLQ threshold and offset monotonicity decisions | REQ-003, REQ-005 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Owner of posture-failure handling | REQ-005 |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Fallback owner of empty-token handling until the authentication ADR is Accepted | REQ-005 |
| `config/adr_authority.toml` | Existing decision targets the registry names should mirror | REQ-005 |
| `.pre-commit-config.yaml` | `check_docs_quality` hook that already runs the rules; no wiring change | REQ-002 |

## Acceptance Criteria
- AC-1: A table with header `| File | Class/Function | Signature | Summary |` outside a guarded block is reported by `check_docs_content_policy.py`, the same table inside an `AUTO-GENERATED` block is not, and the checker does not exceed its baseline size (`REQ-001`).
- AC-2: Each history phrasing and a plan ID in a fixture line fails `check_docs_quality.py` (`REQ-002`).
- AC-3: Each resolved-contradiction signature in a fixture line fails `check_docs_quality.py`, and none matches the current corpus (`REQ-003`).
- AC-4: A Known Deviations bullet with no ledger ID fails `check_known_deviation_sync.py` with exit 1, "Not applicable" does not, and the existing WARNING and ERROR behaviors are pinned by tests (`REQ-004`).
- AC-5: `check_canonical_source_registry.py` passes with the four new decision targets (`REQ-005`).
- AC-6: Each defect class has a failing-then-passing regression test (`REQ-006`).
- AC-7: `governance_04` and `tools/TOOL_DESCRIPTIONS.md` describe the changes and the lexical-only limit; the module-size gates, `check_tool_descriptions_sync.py`, ruff, mypy, and bandit pass for the changed tools (`REQ-007`).
- AC-8: The checkers pass on the current corpus: `check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_known_deviation_sync.py`, `check_canonical_source_registry.py`.

## Tests
- `REQ-001`: in `tests/tools/test_check_docs_content_policy.py`, a fixture document with the `eventbus_08` header shape (a) outside a guarded block is reported, (b) inside an `<!-- AUTO-GENERATED ... -->` block is exempt, and (c) a legitimate non-inventory table of similar width is not reported.
- `REQ-002`, `REQ-003`: in `tests/tools/test_check_docs_quality.py`, via `_run_live_rule(...)`, one failing and one passing line per new rule (each history phrasing, a plan ID and a non-ID token such as `http200`-free prose, each contradiction signature and its corrected wording).
- `REQ-004`: in `tests/tools/test_check_known_deviation_sync.py`, a Known Deviations bullet without an ID gives an ERROR and exit 1; "Not applicable" gives none; existing dangling and uncited-target WARNING tests keep passing.
- Each new test is written first and shown to fail against the unmodified checker; a smoke run of each changed checker against the real `docs/` closes the Plan.

## Documentation Impact
`docs/00_governance/governance_04_documentation-checks.md` (GV-018, custom rules, Known Deviation check) and `tools/TOOL_DESCRIPTIONS.md`; locate them through `docs/00_index.md` "Document References by Task" (governance area). State intent, scope, failure behavior, and that free-text contradictions are covered only by lexical signatures. Write in English.

## Assumptions
- Severity of the new history and plan-ID rules, and of the Known Deviation bullet check, is ERROR once the corpus is clean (the issue leaves Blocking versus Warning to the maintainer; UNK-01).
- The generic plan-ID shape is acceptable because it has no match in non-plan prose today; a future legitimate token of that shape is handled by rewording or by narrowing the rule (UNK-02).
- The registry entries mirror, and do not replace, the decision targets of `config/adr_authority.toml` (ADR-016); the maintainer confirms that listing them in both registries is wanted (UNK-04).
- Overlap judgment (`tools/check_plan_target_overlaps.py`): `docs/00_governance/governance_04_documentation-checks.md` and the tool files are not targets of other open Plans, except `tools/TOOL_DESCRIPTIONS.md`, which `plans/20261112-122408_rmcompat008_compat-checker-patterns.md` also edits (different rows; compatible).
- Step 3a (2026-11-12): the Plan's claims were re-verified. The corpus is not yet clean: history phrasings, `exceeded max_retry`, `strictly monotonic`, and the empty-token sentences still match until the procedures of adrrev015, adrrev017, and adrrev011 are executed (the `Depends on` lines cover this). The plan-ID shape also matches documents that no open Plan edits (`agent_10_01`, `governance_03`, `db_03_07` for toolexec001/adrrev008, `agent_04_03`, `mcp_06_06`); the Phase 4 smoke run decides whether the rule is kept, narrowed, or those documents are assigned to a Plan (UNK-02). ADR-017 does not exist yet, so the empty-token source defaults to ADR-007 (UNK-04). `check_known_deviation_sync.py` is no longer run against an empty ledger (ADR-008 cites SHARED-001/002 since adrrev009). `tests/tools/test_check_docs_quality.py` and `tests/tools/test_check_known_deviation_sync.py` are companions of their rows' procedures (04 and 05).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Severity (ERROR versus WARNING) of the new history, plan-ID, signature, and Known Deviation checks | Maintainer decision | Assume ERROR; the maintainer confirms at review; changing it is a JSON or one-line change | False |
| UNK-02 | Whether the generic plan-ID shape produces false positives in future documents | Only today's corpus was scanned | Verify with a corpus smoke run in Phase 5; narrow the shape if a legitimate token appears | False |
| UNK-03 | Which helper nodes of `check_docs_content_policy.py` to extract and the final helper module name | `module_nodes.py measure` was not run | Run `measure` in Phase 1; amend the module path through `tools/amend_plan.py` (fallout class) if it differs | False |
| UNK-04 | Whether registering the four targets in both the documentation registry and `config/adr_authority.toml` is wanted, and which ADR is the empty-token source before the authentication ADR is Accepted | Maintainer decision; the registry has no ADR-sourced entry yet | Default to ADR-007 for empty-token handling and the existing ADRs for the others; the maintainer confirms | False |
| UNK-05 | Whether the lexical signature rules may be added only after the owning Plans land | Depends on landing order | The `Depends on` lines enforce it; if a signature still matches, report the document for the owning Plan, not edit it (issue instruction) | False |
| UNK-06 | Maintainer position on a semantic checker for free-text contradictions | Out of scope here | Recorded as a limitation in `governance_04`; a separate issue can propose one | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_docs_content_policy.py` | Modify | Medium (CI `--strict` gate; pre-commit) | 1 | N/A | not applicable (`tools/` is not deployed) |
| `tools/_docs_content_policy_helpers.py` | Create | Low | N/A | N/A | not applicable (`tools/` is not deployed) |
| `tools/check_module_size_tools_baseline.txt` | Modify | Low (size gate input) | N/A | N/A | not applicable |
| `config/doc_quality_rules.json` | Modify | High (read by the pre-commit docs-quality hook and the RAG docs-quality workflow) | 0 | N/A | not applicable (`config/` rule file for tools only; not deployed to `/opt/llm`) |
| `tools/check_known_deviation_sync.py` | Modify | Medium (pre-commit hook) | 4 | N/A | not applicable |
| `config/documentation_canonical_sources.toml` | Modify | Medium (governance workflow input) | 2 | N/A | not applicable |
| `tests/tools/test_check_docs_content_policy.py` | Modify | Low | 1 | N/A | not applicable (tests are not deployed) |
| `tests/tools/test_check_docs_quality.py` | Modify | Low | 3 | N/A | not applicable (tests are not deployed) |
| `tests/tools/test_check_known_deviation_sync.py` | Modify | Low | 2 | N/A | not applicable (tests are not deployed) |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Medium (high churn) | 32 | N/A | not applicable (docs) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low (high churn) | 85 | N/A | not applicable (docs) |

## Design
Path B (more than 3 files, new tool module, rule and registry configuration). Findings from the inspection:
- Architecture: the tools import only `_docs_consistency_lib` and the standard library; the extracted helper module is imported by `check_docs_content_policy.py` with the same package-relative pattern as the other `tools/_*.py` modules. No import cycle.
- Dependency graph: `config/doc_quality_rules.json` is read by `check_docs_quality.py`, which runs as a pre-commit hook and in the RAG docs-quality workflow; the rules apply to all active documents, with no path scoping, so each pattern must be specific.
- Historical: churn from `git log --since=30.days`; bus factor `N/A` (git-fame not installed).
- Operational: none (tools and configuration only). Persisted schema: not applicable. Consumer scan: no persisted schema, public API, or shared constant changes (`not affected`; the JSON rule file is read by one checker).
- Design decisions: (1) JSON rules rather than checker code for patterns (the four large tools are at their size baselines, and rules are the existing extension point); (2) extract before changing `check_docs_content_policy.py` instead of raising its baseline (the baseline only shrinks); (3) lexical signatures only, since the registry cannot compare statements; (4) a new ERROR check for a Known Deviation bullet without an ID, because a bullet without an ID cannot have a ledger counterpart.
- Ordering: the extraction and its green size gate come first, then the failing tests, then the rule additions; the registry entries and rules that match fixed documents land last so they start green.
- Smoke run: every changed checker is run against real `docs/` content before the Plan closes (`routing.md` "Adding a new tool" item 4).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Extract helpers to make room** (REQ-001, REQ-007; `tools/check_docs_content_policy.py`, `tools/_docs_content_policy_helpers.py`, `tools/check_module_size_tools_baseline.txt`)
   - [ ] Run `uv run python tools/module_nodes.py measure` on `tools/check_docs_content_policy.py` and choose nodes to extract (UNK-03).
   - [ ] Extract them to the helper module, run the module's tests and the size gate, and lower the recorded size in the baseline.
2. **Phase 2: Inventory-table pattern** (REQ-001, REQ-006; `tools/check_docs_content_policy.py`, `tests/tools/test_check_docs_content_policy.py`)
   - [ ] Write the fixture tests first (outside a guarded block flagged, inside exempt, a non-inventory table not flagged) and see them fail.
   - [ ] Widen `_INDEX_TABLE_HEADER_RE`; run the checker with `--strict` against real `docs/`.
3. **Phase 3: Known Deviation check** (REQ-004, REQ-006; `tools/check_known_deviation_sync.py`, `tests/tools/test_check_known_deviation_sync.py`)
   - [ ] Pin the existing WARNING and ERROR behaviors with tests, write the failing test for a bullet without an ID, then add the ERROR check.
4. **Phase 4: Rules and registry** (REQ-002, REQ-003, REQ-005, REQ-006; `config/doc_quality_rules.json`, `tests/tools/test_check_docs_quality.py`, `config/documentation_canonical_sources.toml`)
   - [ ] Write failing live-rule tests, add the history, plan-ID, and signature rules, and confirm none matches the corpus once the Depends-on Plans have landed.
   - [ ] Register the four decision targets and run `check_canonical_source_registry.py`.
5. **Phase 5: Documentation and verification** (REQ-007; `docs/00_governance/governance_04_documentation-checks.md`, `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Update both documents (including the lexical-only limit) and run `check_tool_descriptions_sync.py`.
   - [ ] Run the Validation plan commands and the `rules/toolchain.md` sequence; do the corpus smoke run; report any flagged document to its owning Plan without editing it.
   - [ ] No deploy step: `tools/` and tool configuration are not deployed to `/opt/llm`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_docs_content_policy.py`, `test_check_docs_quality.py`, `test_check_known_deviation_sync.py`, `test_check_canonical_source_registry.py` | Unit | `uv run pytest tests/tools -q` | Pass |
| Changed `tools/*.py` | Format, lint, type, security | `uv run ruff format <file>`, `uv run ruff check <file>`, `uv run mypy <file>`, `uv run bandit <file>` | Clean |
| `tools/check_docs_content_policy.py` and helper | Tool module size gate | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Pass |
| Tool descriptions | Tool inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | Pass |
| Real corpus | Smoke runs | `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_known_deviation_sync.py`, `check_canonical_source_registry.py`, `check_canonical_source_conflicts.py` | Pass |
| `docs/00_governance/governance_04_documentation-checks.md` | Documentation checks | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| Rule consistency | Validation gate parity | `uv run python tools/run_validation_gates.py` | No Fail |

## Risks
- **Risk**: A new rule matches a legitimate phrase and blocks unrelated documentation work. → **Mitigation**: Each pattern is specific, has a passing fixture, and is smoke-run on the whole corpus; the Plan lands after the cleaning Plans; severity is confirmed by the maintainer (UNK-01).
- **Risk**: Extraction changes behavior of `check_docs_content_policy.py`. → **Mitigation**: Extract with `module_nodes.py` (mechanical), run the existing tests before and after, and keep the exemption logic untouched.
- **Risk**: The generic plan-ID shape flags a future legitimate token. → **Mitigation**: UNK-02 smoke run; narrow the shape or reword the text; the false-positive test documents the intent.
- **Risk**: The new Known Deviation ERROR fails a legitimate free-text entry added later. → **Mitigation**: The message states the fix (cite a ledger ID or remove the bullet); "Not applicable" stays exempt.
- **Risk**: Registering targets in two registries drifts from `config/adr_authority.toml`. → **Mitigation**: Mirror the same target names and ADRs; recorded as UNK-04 for maintainer confirmation.
- **Risk**: The Plan is implemented before its Depends-on Plans and the rules start red. → **Mitigation**: The `Depends on` lines make the dependency visible to `plan_dependency_order.py`, and Phase 4 verifies zero corpus matches before the rules are kept.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extract helpers to make room (REQ-001, REQ-007) | Completed | — | 20261112-211859 |  |
| 2 | Inventory-table pattern (REQ-001, REQ-006) | Completed | — | 20261112-211859 |  |
| 3 | Known Deviation check (REQ-004, REQ-006) | Completed | — | 20261112-215701 |  |
| 4 | Rules and registry (REQ-002, REQ-003, REQ-005, REQ-006) | Completed | — | 20261112-221142 |  |
| 5 | Documentation and verification (REQ-007) | Completed | — | 20261112-224437 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261112-124203_01_tools_check_docs_content_policy.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261112-124203_02_tools__docs_content_policy_helpers.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261112-124203_03_tools_check_module_size_tools_baseline.txt.md | 1 | Procedure | Completed | — | — |
| implementations/20261112-124203_04_config_doc_quality_rules.json.md | 4 | Procedure | Completed | — | — |
| implementations/20261112-124203_05_tools_check_known_deviation_sync.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261112-124203_06_config_documentation_canonical_sources.toml.md | 4 | Procedure | Completed | — | — |
| implementations/20261112-124203_07_tests_tools_test_check_docs_content_policy.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261112-124203_10_docs_00_governance_governance_04_documentation-checks.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261112-124203_11_tools_TOOL_DESCRIPTIONS.md.md | 5 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-111505
- **Related target files**: `tools/check_docs_content_policy.py`, `tools/_docs_content_policy_helpers.py`, `tools/check_module_size_tools_baseline.txt`, `config/doc_quality_rules.json`, `tools/check_known_deviation_sync.py`, `config/documentation_canonical_sources.toml`, `tests/tools/test_check_docs_content_policy.py`, `tests/tools/test_check_docs_quality.py`, `tests/tools/test_check_known_deviation_sync.py`, `docs/00_governance/governance_04_documentation-checks.md`, `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: find why the `eventbus_08` table was missed and fix it | `tools/check_docs_content_policy.py` | Step 2 | AC-1 | `tests/tools/test_check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-001 | Constraints: respect the module size gates (baseline 33240 bytes) | `tools/_docs_content_policy_helpers.py` | Step 1 | AC-1 | `check_module_size.py --scripts-dir tools` | Derived from confirmed evidence |
| REQ-001 | Required Changes: add a fixture with that table shape | `tests/tools/test_check_docs_content_policy.py` | Step 2 | AC-1 | itself | Explicit in issue |
| REQ-002 | Required Changes: extend the forbidden-pattern list with history phrasings and plan IDs | `config/doc_quality_rules.json` | Step 4 | AC-2 | `tests/tools/test_check_docs_quality.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: claim coverage for posture, empty token, DLQ threshold, offsets (lexical signatures) | `config/doc_quality_rules.json` | Step 4 | AC-3 | `tests/tools/test_check_docs_quality.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes: Known Deviation sync fails when an entry has no ledger counterpart | `tools/check_known_deviation_sync.py` | Step 3 | AC-4 | `tests/tools/test_check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes: register the normative source of each topic | `config/documentation_canonical_sources.toml` | Step 4 | AC-5 | `check_canonical_source_registry.py` | Needs confirmation |
| REQ-006 | Required Changes: checker tests that re-introduce each resolved contradiction | `tests/tools/test_check_docs_quality.py` | Step 4 | AC-6 | itself | Explicit in issue |
| REQ-006 | Same; Known Deviation behaviors pinned | `tests/tools/test_check_known_deviation_sync.py` | Step 3 | AC-6 | itself | Explicit in issue |
| REQ-007 | Documentation Impact: `governance_04` describes the new checks | `docs/00_governance/governance_04_documentation-checks.md` | Step 5 | AC-7 | `check_docs_quality.py`, `check_docs_structure.py` | Explicit in issue |
| REQ-007 | Constraints: update `tools/TOOL_DESCRIPTIONS.md` in the same change | `tools/TOOL_DESCRIPTIONS.md` | Step 5 | AC-7 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-007 | Constraints: module size baseline records the reduced size | `tools/check_module_size_tools_baseline.txt` | Step 1 | AC-7 | `check_module_size.py --scripts-dir tools` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261112-124203 -->
