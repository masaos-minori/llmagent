## Goal

Extend the GV-009 prose-scan checker `tools/check_canonical_document_prose.py` with
area-grouping so that any area for which two or more distinct documents are designated as the
primary/canonical source is flagged as a WARNING. This closes the documented `Partial` gap for
GV-010 without changing the registration process or the registry schema.

## Scope

- **In-Scope**:
  - Extend the shared GV-009 scanner (do NOT fork it) to assign each unregistered canonical
    claim to an area grouping key and flag areas with more than one designated primary source.
  - Add single-primary and multi-primary-per-area unit tests to
    `tests/tools/test_check_canonical_document_prose.py`.
  - Update the GV-010 matrix row to `Existing` and clear its follow-up note
    (`docs/00_governance/governance_04_documentation-checks.md`).
- **Out-of-Scope**:
  - Changing the Canonical Source Registry schema or `check_canonical_source_registry.py`
    (GV-019) behavior.
  - Creating a separate/forked scanner.
  - GV-009 (duplicate single-document specification) — already covered by the base scanner.

## Assumptions

- The base GV-009 scanner `tools/check_canonical_document_prose.py` exists (created by
  `plans/20261018-180319_plan.md`) and exposes a stable public hook returning parsed canonical
  claims (e.g. a function yielding per-match subject/context). If the final API differs, align
  here to it rather than refactoring the base scanner.
- The check remains warning-level and non-blocking, consistent with GV-010's existing gate.
- The area grouping key can be approximated from the claim's context (nearest area/subsystem
  token, or the containing document's area); when ambiguous, fail safe toward not grouping (no
  false positive).

## Design decisions

- Reuse the base scanner's claim-parsing function so the pattern set and subject extraction are
  defined once (UNK-03: do not re-derive the pattern scan).
- Derive an area key per claim: prefer an explicit area/subsystem token in the claim's context;
  otherwise fall back to the claim's `claim_type` or the containing document's area.
  Ungrouped/unextractable claims are left ungrouped (not flagged).
- Within each area group, collect the distinct designated documents; flag areas whose group
  contains two or more distinct documents as primary. Single-primary areas are not flagged.

## Alternatives considered

- Forking a dedicated GV-010 scanner — rejected: the plan forbids duplication; the shared
  scanner must be extended.

## Implementation

### Target file

`tools/check_canonical_document_prose.py`

### Procedure

1. Read the base GV-009 scanner to locate the public claim-parsing hook (the function that
   yields parsed canonical claims with their subject/context). Do not change the pattern scan.
2. Add an area-key derivation helper (UNK-01): given a parsed claim, return an area grouping key
   (explicit area/subsystem token if present, else `claim_type`, else the containing document's
   area); return `None` for unextractable claims (ungrouped).
3. Add multi-primary-per-area detection: after the base scan produces claims, group them by area
   key, collect the distinct designated documents per group, and emit a WARNING for any group
   with two or more distinct documents (REQ-002). Single-primary groups are not flagged (REQ-003).
4. Emit WARNING findings only; preserve the base scanner's severity/exit contract.
5. Wire the new grouping into the existing reporting path so multi-primary findings surface.

### Method

- **Reuse.** Import/call the base scanner's claim-parsing function directly; keep the pattern
  set and subject extraction untouched. If the base scanner does not yet expose a reusable hook,
  add a thin public accessor (do not refactor the pattern scan).
- **Area key (UNK-01).** Prefer an explicit area/subsystem token in the claim context; fall back
  to `claim_type`; fall back to the containing document's area. Document the precedence in-code.
- **Multi-primary (REQ-002).** For each area group, build the set of distinct designated
  documents; if `len(set) >= 2`, emit a WARNING listing the competing documents.
- **Reporting.** WARNING only; exit 0 for WARNING-only runs (non-blocking contract preserved).

### Details

- `REQ-001`: the area-grouping logic lives in the shared GV-009 scanner, not a fork.
- `REQ-002`: an area with two or more distinct designated documents is flagged as WARNING.
- `REQ-003`: a single-primary area is not flagged.
- `REQ-004`: no WARNING for benign mentions in the current `docs/` corpus.
- **UNK-01:** define the area grouping key up front (explicit area token → `claim_type` →
  document area); document the choice in-code; ungrouped claims are not flagged.
- **UNK-02:** same tool-name swap as GV-009 — the issue names `check_canonical_source_registry.py`
  as GV-019, but GV-019 is `check_canonical_source_conflicts.py`. Read-only reference to the
  registry; do not call either existing tool.
- **UNK-03:** restrict to the same conservative assertion patterns as GV-009; exclude
  secondary/supporting phrasings so "primary canonical source for an area" is distinguished from
  supporting references.

## Compatibility considerations

Extends an existing warning-level tool; no change to the registry schema or to
`check_canonical_source_registry.py` / `check_canonical_source_conflicts.py`. Non-blocking
(WARNING) findings preserve the CI exit contract.

## Security considerations

N/A: reads local `docs/` and a local TOML; applies read-only regexes; executes no user input.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_canonical_document_prose.py` | Format/lint | `uv run ruff format tools/ && uv run ruff check tools/` | Clean |
| `tools/check_canonical_document_prose.py` | Type check | `uv run mypy --no-namespace-packages tools/` | Clean |
| `tools/check_canonical_document_prose.py` | Security | `uv run bandit -r tools/ -c pyproject.toml -ll` | No high/medium |
| `tools/check_canonical_document_prose.py` | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |
| `tools/check_canonical_document_prose.py` | Unit + corpus | `uv run pytest tests/tools/test_check_canonical_document_prose.py` then corpus run | Multi-primary flagged; single-primary/corpus clean (REQ-002/003/004) |
| Whole change | Full regression | `uv run pytest` + `uv run pre-commit run --all-files` | Existing GV-009 suites still pass; no new failures |

## Completion criteria

- The shared GV-009 scanner groups unregistered canonical claims by area and flags areas with
  two or more distinct primary documents (WARNING).
- Unit tests cover single-primary (not flagged) and multi-primary (flagged) fixtures plus a
  corpus run with zero benign false positives.
- The GV-010 matrix row reports automated detection with the follow-up note cleared.

## Out of scope

Changing the registry schema, changing `check_canonical_source_registry.py` /
`check_canonical_source_conflicts.py`, and creating a forked scanner.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019-112938 | 20261019-112938 | REQ-001/002/003; UNK-01/02/03 |
| 2 | Add or update tests per Validation plan | Completed | 20261019-112938 | 20261019-112938 | REQ-001/002/003/004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-112938 | 20261019-112938 | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019-112938 | 20261019-112938 | REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (extend the shared GV-009 scanner with area-grouping and multi-primary-per-area flagging)
- **Source issue**: `issues/done/20261018-173100_gov010_detect-multiple-primary-canonical-sources-per-area-in-unregistered-prose.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-180620_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-065941
- **Related target files**: `tools/check_canonical_document_prose.py`
- **Dependency**: extends the base scanner created by `plans/20261018-180319_plan.md`; align to its actual API.