## Goal
Add a `version` field to the already-existing `config/documentation_canonical_sources.toml`
registry file (REQ-001, REQ-003) — the file itself already exists; this row's actual
remaining work is narrower than the Plan's authoring-time snapshot assumed.

## Scope
- In scope: adding one top-level `version` field to the existing file.
- Out of scope: restructuring the file's existing 2 entries' schema (see Assumptions
  — a schema change here is a cross-cutting decision, not this row's to make
  unilaterally); adding further entries beyond the existing 2 (Out-of-Scope per the
  Plan: "one illustrative entry only... complete migration is M-01-06's scope" — the
  file already has 2, exceeding that intent, but removing legitimate existing content
  is not this row's job either).

## Assumptions
- **Major drift found this cycle (2026-09-06) — this is a blocking discovery,
  reconcile before implementing further rows**: `config/documentation_canonical_sources.toml`
  already exists (created by a concurrent session), with 2 entries
  (`eventbus.core-behavior`, `eventbus.persistence-schema`), using the schema:
  `decision_target`, `claim_type`, `source_paths` (always plural, a list), `area`,
  `notes` — inside a `[[canonical_sources]]` array-of-tables. This does **not** match
  this Plan's REQ-002 schema proposal (nested `[targets."<target>".<claim-type>]`
  tables; separate singular `source` vs. plural `sources` fields per REQ-005; a
  `source_kind` field; an `optional validation reference` field). No `version` field
  exists in the current file.
- **A third, independently-different schema already exists in code**:
  `tools/check_canonical_source_conflicts.py` (already present, NOT one of this
  Plan's target files) explicitly imports `load_registry`/`validate_registry_schema`
  from `tools.check_canonical_source_registry` (this Plan's row 02 — which does not
  exist yet) and, in its `RegistryEntry` fallback dataclass, expects entirely
  different fields again: `id`, `target`, `claim_type`, `authority`, `precedence`,
  `status`, `effective_date`, `expiry_date`, `validation_ref`, `description`, keyed
  as one `[entry_id]` table per entry (not `[[canonical_sources]]` array-of-tables),
  at a **different default path** (`config/canonical_source_registry.toml`, singular
  "canonical_source_registry", not "documentation_canonical_sources"). Confirmed this
  cycle via direct execution: `python3 tools/check_canonical_source_conflicts.py
  --registry config/documentation_canonical_sources.toml` exits 0 with zero output —
  its fallback TOML loader cannot parse the actual file's `[[array-of-tables]]`
  structure (it only recognizes top-level `[key]` tables whose value is a dict, not
  a list), so it silently detects nothing against the real registry.
- Given three mutually-incompatible schema designs already exist in the repository
  (this Plan's own proposal; the actual TOML file; `check_canonical_source_conflicts.py`'s
  expectation) — likely from three different M-01-0X sessions working concurrently
  without full coordination — this row does **not** attempt to unilaterally pick a
  winner. It makes the smallest change that keeps the existing file valid and
  versioned (adding `version`), and defers the schema-unification decision to row 02
  (the validator), which must be built against whichever schema is decided as
  canonical — see row 02's own Assumptions for the recommended resolution.

## Design decisions
- Add `version = "1"` (or `1`, matching whatever type convention the eventual
  validator expects) as the first line of the file, above the existing
  `[[canonical_sources]]` entries — the minimal, additive change that does not
  disturb the 2 existing entries other sessions/documents (the eventbus doc-guide)
  already reference by their current field names.
- Do not rename `decision_target`/`claim_type`/`source_paths`/`area`/`notes` to match
  this Plan's REQ-002 proposal (`source`/`sources`, `source_kind`) — doing so would
  break the eventbus doc-guide's existing reference to this exact file (confirmed via
  `docs/06_eventbus_00_document-guide.md` lines 40-41, read this session) without a
  corresponding update to that file (out of this row's scope, and not this Plan's
  Implementation Target Files either).

## Alternatives considered
- Rewrite the file to match this Plan's originally-proposed nested-table schema:
  rejected — would break the eventbus doc-guide's already-landed reference to the
  current flat schema, a real regression to already-working cross-referenced content
  this Plan must not introduce (per `AGENTS.md` Global Rule 5, no unrelated breakage).
- Rewrite the file to match `check_canonical_source_conflicts.py`'s expected schema
  instead: rejected for the same reason, and additionally because
  `check_canonical_source_conflicts.py` is not this Plan's target file — coordinating
  a rename affecting a file outside this Plan's frozen scope would be an additional
  target file discovery requiring its own Plan amendment, not a unilateral decision
  inside this row.

## Implementation
### Target file
`config/documentation_canonical_sources.toml`

### Procedure
1. Re-read the file's current content immediately before editing (per Assumptions,
   a fourth concurrent session could plausibly still be active on this file).
2. Add `version = "1"` as the first line, before the existing `[[canonical_sources]]`
   entries.
3. Do not modify the 2 existing entries' field names or values.
4. Report the three-way schema mismatch (Assumptions above) prominently in this
   row's completion report — this is a cross-cutting M-01-series coordination gap
   that the implementer cannot fully resolve from this row alone; flag as a candidate
   Known Issue if not already tracked elsewhere by the time this row executes.

### Method
Confirmed this cycle (2026-09-06) via direct read of the file (12 lines, 2 entries)
and of `tools/check_canonical_source_conflicts.py` (832 lines, full read) and a live
execution of the latter against the former (exit 0, zero findings — confirmed
parsing failure due to array-of-tables incompatibility with its fallback loader).

### Details
No change to the file's existing 2 entries.

## Compatibility considerations
Adding a `version` field is additive; `check_canonical_source_conflicts.py`'s
fallback loader already ignores this file's actual structure entirely (confirmed
via the exit-0/zero-output test), so adding one more top-level key does not change
its current (already-broken) behavior either way.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if a future schema-unification
decision supersedes this row's minimal `version`-field addition.

## Validation plan
- Confirm the file remains valid TOML: `python3 -c "import tomllib; tomllib.load(open('config/documentation_canonical_sources.toml','rb'))"`.
- Re-run `python3 tools/check_canonical_source_conflicts.py --registry config/documentation_canonical_sources.toml` — document its exit code/output as a known baseline (expected: unchanged, exit 0, zero output, per the confirmed parsing gap — not a regression this row introduces).

## Completion criteria
- The file has a `version` field.
- The file remains valid TOML with its 2 existing entries unchanged.
- The three-way schema mismatch is reported (Assumptions) for cross-Plan
  coordination, not silently absorbed into this row alone.

## Out of scope
- `tools/check_canonical_source_registry.py` — tracked in seq 02 (must resolve the
  schema question, informed by this row's findings).
- `tools/check_canonical_source_conflicts.py` — not this Plan's target file; its
  parsing gap is a candidate follow-up for whoever owns that tool's Plan.
- Renaming any existing field or restructuring the array-of-tables layout.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-06 | 2026-09-06 | Added `version = "1"` as first line of TOML registry |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-06 | 2026-09-06 | N/A: TOML change validated via tomllib round-trip |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-06 | 2026-09-06 | TOML validity confirmed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-06 | 2026-09-06 | N/A: no docs/00_index.md task-scope mapping for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Three mutually-incompatible schema designs exist for this registry across this Plan's proposal, the actual file, and `check_canonical_source_conflicts.py` — no single owning session has reconciled them | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260903-103027_m0104_introduce-machine-readable-canonical-source-registry.md
- **Source plan**: plans/20260905-165405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150039
- **Related target files**: config/documentation_canonical_sources.toml
