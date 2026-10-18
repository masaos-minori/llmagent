## Goal

Create a new standalone checker `tools/check_canonical_document_prose.py` that scans
`docs/*.md` for prose asserting that a document is the canonical/normative source for a
topic or claim type, and flags such unregistered claims that overlap a registered source in
the Canonical Source Registry (`config/documentation_canonical_sources.toml`) or another
prose claim. This closes the documented `Partial` gap for GV-009 without changing the
registration process, and emits only non-blocking WARNING findings.

## Scope

- **In-Scope**:
  - A new `tools/check_canonical_document_prose.py` implementing pattern scan, subject
    extraction, registry-overlap matching, and duplicate-prose grouping, emitting WARNING
    findings.
  - Unit tests with positive (duplicate/unregistered) and negative (benign/incidental)
    fixtures plus a corpus run (`tests/tools/test_check_canonical_document_prose.py`).
  - Wiring the new warning-level check into the existing canonical-tool CI run
    (`.github/workflows/governance-docs-consistency.yml`).
  - Updating the GV-009 matrix row to `Existing` and clearing its follow-up note
    (`docs/00_governance/governance_04_documentation-checks.md`).
- **Out-of-Scope**:
  - Changing the Canonical Source Registry schema.
  - Changing `check_canonical_source_registry.py` (GV-020) or
    `check_canonical_source_conflicts.py` (GV-019) behavior.
  - GV-010 (multiple primary sources in the same area).

## Assumptions

- The new checker is warning-level and non-blocking, consistent with GV-009's existing gate.
- The registry lives at `config/documentation_canonical_sources.toml` and exposes
  `decision_target`, `claim_type`, `source_paths`, `area` per entry.
- The sibling canonical tools establish the CLI/severity/result convention to mirror.
- Subject of a prose claim is approximated by the nearest path-like token
  (`scripts/...`, `docs/...`, `<x>.py`) or `decision_target`-like token
  (`word.word(-word)*`) adjacent to the assertion; matching is token/substring based, not
  semantic.

## Design decisions

- Follow the `check_canonical_source_*.py` convention: `argparse` CLI, `--registry` option,
  `main() -> int` with `sys.exit(main())`, and result objects carrying a `Severity`
  (`HIGH`/`MEDIUM`/`LOW`) and `BlockingStatus` (`BLOCKING`/`NON_BLOCKING`/`WARNING`) — see
  `tools/check_canonical_source_conflicts.py` and `tools/check_canonical_source_registry.py`.
- Read the registry TOML directly with `tomllib` (as `check_canonical_source_registry.py`
  does) rather than calling either sibling tool — the issue's GV-019/GV-020 tool naming is
  swapped (UNK-01), and the checker must not depend on either tool's behavior.
- Keep the pattern set conservative and reviewed, excluding negations ("not"/"never"/"no")
  and incidental "canonical" usage, to avoid false positives (UNK-02).

## Alternatives considered

- Reusing `check_canonical_source_conflicts.py` directly — rejected: it only detects
  conflicts among *registered* entries and the tool naming in the issue is unreliable
  (UNK-01); the new checker must operate on unregistered prose, which GV-019 does not cover.

## Implementation

### Target file

`tools/check_canonical_document_prose.py`

### Procedure

1. Scaffold the module following the sibling canonical tools' shape (imports, constants,
   dataclasses, `main()`).
2. Define and document the conservative pattern set (UNK-02): phrases asserting canonical
   status such as "the canonical source for", "is the normative reference for",
   "authoritative source for", plus close variants, with negation exclusion.
3. Implement the `docs/*.md` scan + subject extraction (nearest path/`decision_target`
   token; unmatched subjects are skipped — fail safe toward no false positives, UNK-03).
4. Load the registry TOML via `tomllib`; implement registry-overlap matching
   (REQ-002) and duplicate-prose grouping by subject (REQ-003).
5. Emit WARNING findings only; preserve the sibling tools' non-blocking severity/exit
   contract.
6. Wire the check into `.github/workflows/governance-docs-consistency.yml` (REQ-001/002/003).

### Method

- **CLI.** Mirror `check_canonical_source_registry.py`: `argparse.ArgumentParser` with a
  `--registry` option defaulting to `config/documentation_canonical_sources.toml`
  (`tools/check_canonical_source_registry.py` line 51 sets this default path), optional
  `--docs`, and `def main(argv=None) -> int` ending in `sys.exit(main())`.
- **Results.** Return findings using the sibling `Severity` (`HIGH`/`MEDIUM`/`LOW`) and
  `BlockingStatus` (`BLOCKING`/`NON_BLOCKING`/`WARNING`) enums
  (`tools/check_canonical_source_conflicts.py` lines 72-90, 183-188). For a non-blocking
  WARNING-level gate, use the sibling's non-blocking severity/blocking-status convention
  (e.g. `Severity.MEDIUM` with a non-blocking `BlockingStatus`) — confirm the exact pairing
  against the sibling tools rather than assuming; the plan's "WARNING/ERROR" wording maps to
  this non-blocking convention. Do NOT introduce a `Severity.WARNING` member (it does not
  exist).
- **Pattern scan.** Compile a reviewed regex set; skip matches preceded by a negation
  ("not"/"never"/"no"). Document the final set in-code (UNK-02).
- **Subject extraction.** For each match, capture the nearest candidate subject: a
  path-like token (`\w[\w./-]+\.py`, `scripts/...`, `docs/...`) or a
  `decision_target`-like token (`word.word(-word)*`). If none, skip the claim (UNK-03).
- **Registry overlap (REQ-002).** Flag a claim whose subject matches any registered
  `source_paths` entry or `decision_target`.
- **Duplicate prose (REQ-003).** Group claims by extracted subject across all of `docs/`;
  flag subjects shared by two or more claims.
- **Reporting.** Collect findings and print them in the sibling tools' format; exit 0 for
  WARNING-only runs (preserve the non-blocking contract).

### Details

- `REQ-001`: the pattern set is reviewed, documented in-code, and excludes negations and
  incidental "canonical" usage.
- `REQ-002`: a prose canonical claim whose subject matches a registered `source_paths`/
  `decision_target` yields a WARNING.
- `REQ-003`: two or more prose canonical claims sharing the same subject yield WARNING(s).
- `REQ-004`: no WARNING for benign/incidental mentions in the current `docs/` corpus (e.g.
  the negation in `governance_01_documentation-policy.md`).
- **UNK-01 correction:** the issue names `check_canonical_source_registry.py` as the
  GV-019 tool, but the matrix maps GV-019 to `check_canonical_source_conflicts.py` and
  GV-020 to `check_canonical_source_registry.py`. Implement against the registry TOML
  directly (read-only); do NOT call either existing tool.
- **UNK-02:** define the conservative pattern set up front and tune against the current
  corpus with negative fixtures.
- **UNK-03:** scope overlap detection to literal subject matches; unmatched subjects are
  not flagged (fail safe toward no false positives).

## Compatibility considerations

New CLI entry point only; no external callers and no change to existing tools or the
registry schema. Non-blocking (WARNING) findings preserve the CI exit contract.

## Security considerations

N/A: reads local `docs/` and a local TOML; applies read-only regexes; executes no user
input and handles no secrets.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_canonical_document_prose.py` | Format/lint | `uv run ruff format tools/ && uv run ruff check tools/` | Clean |
| `tools/check_canonical_document_prose.py` | Type check | `uv run mypy --no-namespace-packages tools/` | Clean |
| `tools/check_canonical_document_prose.py` | Security | `uv run bandit -r tools/ -c pyproject.toml -ll` | No high/medium |
| `tools/check_canonical_document_prose.py` | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |
| `tools/check_canonical_document_prose.py` | Unit + corpus | `uv run pytest tests/tools/test_check_canonical_document_prose.py` then corpus run | Positive flagged; corpus clean (REQ-004) |
| Whole change | Full regression | `uv run pytest` + `uv run pre-commit run --all-files` | No new failures |

## Completion criteria

- The checker scans `docs/*.md`, extracts subjects, matches the registry, groups duplicates,
  and emits WARNING findings with the sibling's non-blocking severity/exit convention.
- Unit tests cover REQ-001/002/003/004 (positive, duplicate, negation/negative, corpus).
- The CI workflow runs the new check.
- The GV-009 matrix row reports automated detection with the follow-up note cleared.

## Out of scope

Changing the registry schema, changing `check_canonical_source_registry.py` /
`check_canonical_source_conflicts.py`, and GV-010.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001/002/003; UNK-01/02/03 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-001/002/003/004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | REQ-005 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (new checker: pattern scan, subject extraction, registry-overlap matching, WARNING reporting)
- **Source issue**: `issues/20261018-173010_gov009_detect-duplicate-canonical-document-specification-in-unregistered-prose.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-180319_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-064745
- **Related target files**: `tools/check_canonical_document_prose.py`
