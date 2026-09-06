## Goal
Complete `tools/check_canonical_source_conflicts.py`'s remaining gap: REQ-001's
wrapping of `M-01-04`'s registry validator (`CANONICAL-002` through `-006`, `-009`)
— the file already exists and already implements REQ-002/003/005/006/007 in full.

## Scope
- In scope: the `try: from tools.check_canonical_source_registry import
  (load_registry, validate_registry_schema) ... except ImportError:
  HAS_REGISTRY_VALIDATOR = False` block and `detect_all_conflicts()`'s
  `HAS_REGISTRY_VALIDATOR` branch (currently lines 43-51, 679-701) — this is the only
  code path not yet functionally complete.
- Out of scope: `detect_duplicate_normative_sources` (CANONICAL-001),
  `detect_multiple_canonical_specifications` (CANONICAL-008),
  `detect_area_guide_contradiction` (CANONICAL-010),
  `detect_legacy_precedence_reintroduction` (CANONICAL-011), and all 5
  `detect_*` Warning functions (CANONICAL-W-01 through W-05) — already implemented,
  confirmed matching this Plan's Design section's rule-ID allocation exactly; no
  change needed.

## Assumptions
- **Major finding this cycle (2026-09-06) — this file already exists,
  substantially implemented**: `tools/check_canonical_source_conflicts.py` (832
  lines) already exists, created by a concurrent session, and already implements
  REQ-002 (`CANONICAL-001`), REQ-003 (`CANONICAL-008`), REQ-005 (`CANONICAL-010`),
  REQ-006 (`CANONICAL-011`), and REQ-007 (5 Warnings, `CANONICAL-W-01` through
  `-05`) — confirmed via direct read this cycle, function-by-function, matching this
  Plan's own Design section's rule-ID allocation almost exactly.
- **What remains (REQ-001)**: the file's `RegistryEntry` fallback dataclass (`id`,
  `target`, `claim_type`, `authority`, `precedence`, `status`, `effective_date`,
  `expiry_date`, `validation_ref`, `description`) does **not** match `M-01-04`'s
  actual registry schema (`decision_target`, `claim_type`, `source_paths`, `area`,
  `notes` — confirmed via `plans/done/20260905-165405_plan.md`'s own procedure
  documents, generated earlier this same session). Confirmed via live execution this
  cycle: `python3 tools/check_canonical_source_conflicts.py --registry
  config/documentation_canonical_sources.toml` exits 0 with zero output — its
  fallback `_load_registry_toml()` cannot parse the real file's `[[canonical_sources]]`
  array-of-tables structure at all (silently finds nothing), and
  `tools/check_canonical_source_registry.py` (`M-01-04`'s own row, which this file's
  `try/except ImportError` depends on) does not exist yet either — so
  `HAS_REGISTRY_VALIDATOR` is currently always `False`, and REQ-001's entire wrapping
  branch is dead code.
- **Execution order**: this row's REQ-001 work is blocked until `M-01-04`'s
  `tools/check_canonical_source_registry.py` (`plans/done/20260905-165405_plan.md`
  seq 02) actually lands, since REQ-001 wraps that tool's output — re-verify at
  implementation time, not from this cycle's snapshot.

## Design decisions
- Once `M-01-04`'s validator exists, update this file's `_load_registry_toml()`
  fallback AND the `HAS_REGISTRY_VALIDATOR` branch in `detect_all_conflicts()` to
  consume the actual schema (`decision_target`/`claim_type`/`source_paths`/`area`/
  `notes`), not the currently-hardcoded `RegistryEntry` field set — this requires
  changing `RegistryEntry`'s own field definitions (lines 290-333), which ripples
  into every `detect_*` function that reads `entry.target`/`entry.authority`/
  `entry.precedence`/`entry.status` (all 9 currently-working detection functions) —
  this is a larger, more invasive change than REQ-001's original framing ("thin
  orchestration layer... re-emits findings") suggested, because the schema mismatch
  means the existing 9 detection functions' field assumptions must also be
  reconciled, not just the wrapping block.
- Also fix the registry path mismatch: this file defaults to
  `config/canonical_source_registry.toml` (line 676); the actual file is
  `config/documentation_canonical_sources.toml` — update the default to match.

## Alternatives considered
- Leave `RegistryEntry`'s field set unchanged and only fix the wrapping block:
  rejected — every existing `detect_*` function already reads fields
  (`entry.target`, `entry.authority`, `entry.precedence`, `entry.status`) that don't
  exist on the actual registry's entries; leaving them unreconciled means all 9
  already-implemented detection functions would raise `AttributeError` or silently
  no-op against the real file once `HAS_REGISTRY_VALIDATOR` becomes `True` and stops
  falling back to the (currently silently-broken) `_load_registry_toml()`.

## Implementation
### Target file
`tools/check_canonical_source_conflicts.py`

### Procedure
1. Confirm `tools/check_canonical_source_registry.py` (`M-01-04`) has actually landed
   before starting this row's work (Phase 0 gate).
2. Update `RegistryEntry`'s field definitions to match the actual registry schema:
   `decision_target: str`, `claim_type: str`, `source_paths: list[str]`,
   `area: str`, `notes: str | None = None` — remove `authority`/`precedence`/
   `status`/`effective_date`/`expiry_date`/`validation_ref`/`description` fields that
   don't exist on real entries, or keep them as `Optional` compatibility fields
   defaulted to sentinel values if any existing `detect_*` function's logic
   genuinely needs a concept the actual schema doesn't have (e.g. "precedence"/
   "status" — reconcile case-by-case; do not silently drop a check's actual
   semantic meaning).
3. Update the default registry path (line 676) to
   `config/documentation_canonical_sources.toml`.
4. Fix `_load_registry_toml()` to parse the actual `[[canonical_sources]]`
   array-of-tables structure (a list under one key, not one table per key).
5. Update `detect_all_conflicts()`'s `HAS_REGISTRY_VALIDATOR` branch (lines 679-701)
   to convert `M-01-04`'s `load_registry()` return value into the (now-reconciled)
   `RegistryEntry` shape without referencing removed fields.
6. Re-run every existing `detect_*` function's own logic against the reconciled
   field set — confirm each still expresses its original intent (e.g.
   `detect_duplicate_normative_sources` currently filters on
   `entry.precedence != "normative"`; if `precedence` no longer exists, decide
   whether "normative" now means "any entry" given the actual schema has no
   precedence concept, or whether a new inference rule is needed — this is a design
   decision for the implementer, not pre-decided here, since it depends on how
   `M-01-04`'s actual schema categorizes normative-vs-non-normative sources, which
   this cycle's evidence does not fully resolve).
7. Implement REQ-001's `CANONICAL-002` through `-006`, `-009` codes, wrapping
   `M-01-04`'s `validate_registry_schema()` error strings.

### Method
Confirmed this cycle (2026-09-06) via direct read (full file, 832 lines) and live
execution (`python3 tools/check_canonical_source_conflicts.py --registry
config/documentation_canonical_sources.toml`, exit 0, zero output).

### Details
No change to the 9 already-implemented `detect_*` functions' rule-ID codes or
routing logic (`classify_finding()`) — only their field-access assumptions need
reconciling per Procedure step 6.

## Compatibility considerations
This is a breaking internal change to `RegistryEntry`'s shape — no external caller
of this module was found via `rg "from tools.check_canonical_source_conflicts
import" scripts/ tests/` (confirm at implementation time) beyond its own CLI
entry point and this Plan's own test file (seq 03).

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if the schema reconciliation (step 6)
finds a `detect_*` function's original intent cannot be preserved without a genuine
new registry field — escalate rather than silently weakening the check.

## Validation plan
- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py -v` (seq 03).
- `python3 tools/check_canonical_source_conflicts.py` — exits 0 against the real
  registry (no false positives on its 2 legitimate entries), and no longer silently
  finds nothing due to a parsing failure.

## Completion criteria
- `RegistryEntry`'s fields match `M-01-04`'s actual registry schema.
- `HAS_REGISTRY_VALIDATOR` becomes `True` when `tools/check_canonical_source_registry.py`
  exists, and REQ-001's wrapped codes (`CANONICAL-002` through `-006`, `-009`) are
  emitted from its findings.
- All 9 pre-existing `detect_*` functions still express their original semantic
  intent against the reconciled field set.

## Out of scope
- `tools/check_canonical_source_registry.py` itself — `M-01-04`'s scope,
  `plans/done/20260905-165405_plan.md`.
- `config/documentation_canonical_sources.toml`'s own content — read-only from this
  row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked on M-01-04 landing — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `tools/check_canonical_source_registry.py` (M-01-04) not yet implemented as of 2026-09-06; this row's REQ-001 work cannot complete until it lands, and the schema-reconciliation work (step 6) is larger than REQ-001's original "thin wrapper" framing anticipated | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260903-103028_m0105_implement-canonical-source-validation-and-ci-enforcement.md
- **Source plan**: plans/20260905-165817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150421
- **Related target files**: tools/check_canonical_source_conflicts.py
