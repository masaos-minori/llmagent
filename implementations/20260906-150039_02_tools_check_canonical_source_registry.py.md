## Goal
Create `tools/check_canonical_source_registry.py`: dataclass schema definition,
registry parser, path-existence check, `source`/`sources` enforcement, ADR-status
check, and claim-type validation (REQ-002, REQ-004, REQ-005, REQ-006, REQ-007) —
built against the registry's **actual** existing schema, not this Plan's
originally-proposed one (see Assumptions and row 01's findings).

## Scope
- In scope: new file `tools/check_canonical_source_registry.py` only.
- Out of scope: `tools/check_canonical_source_conflicts.py` (pre-existing, imports
  from this new module but is not itself modified by this row — its broken fallback
  parser, confirmed in row 01, is a candidate follow-up for its own owning Plan);
  `config/documentation_canonical_sources.toml` (row 01, read-only from this row's
  perspective).

## Assumptions
- **Schema decision (informed by row 01's findings)**: build this tool's dataclass
  schema and parser against the registry file's **actual current fields**
  (`decision_target: str`, `claim_type: str`, `source_paths: list[str]`, `area: str`,
  `notes: str | None`, inside a top-level `canonical_sources` array-of-tables), not
  this Plan's originally-proposed nested `[targets."<target>".<claim-type>]`
  structure with separate `source`/`sources` fields — the actual file already exists
  and is already referenced by `docs/06_eventbus_00_document-guide.md`; building a
  validator against a schema the file doesn't use would make this tool permanently
  unable to validate the one registry file that exists.
- **REQ-005's `source` vs. `sources` requirement, reinterpreted against the actual
  schema**: since the real file always uses `source_paths` (a list, no singular
  variant), REQ-005's constraint ("a `source` field takes exactly one path... a
  `sources` list only for claim types whose canonical implementation spans multiple
  files") is re-expressed as: `source_paths` MUST contain exactly one path unless
  `claim_type == "runtime-behavior"` (or another claim type explicitly allow-listed),
  in which case more than one path is permitted. This preserves REQ-005's actual
  constraint (single normative source per claim type, with a narrow multi-file
  exception) without requiring the file to grow two differently-named fields for
  what is structurally the same list.
- **`source_kind`/`area`**: the actual file already has `area` (matching REQ-002's
  "owning area" field); it has no separate `source_kind` field — infer source kind
  from context (e.g. whether the claim type is `architecture-decision`, in which case
  REQ-006's ADR-status check applies) rather than requiring a new field the existing
  2 entries don't have.
- **`check_canonical_source_conflicts.py`'s expected `load_registry`/
  `validate_registry_schema` function names** (confirmed via row 01's read of that
  file) should be implemented with these exact names in this new module, so that
  tool's existing `try: from tools.check_canonical_source_registry import
  (load_registry, validate_registry_schema)` import succeeds — even though that
  tool's own internal `RegistryEntry` field names still won't match this schema
  (a residual gap outside this row's scope to fully close, per row 01's Out of
  Scope; flag it in this row's own completion report too).

## Design decisions
- Define `RegistryEntry` (or similarly-named) dataclass with fields matching the
  actual file: `decision_target: str`, `claim_type: str`, `source_paths: list[str]`,
  `area: str`, `notes: str | None = None`. Define `CanonicalSourceRegistry` as a
  `version: str` plus `list[RegistryEntry]`.
- Implement `load_registry(path: Path) -> CanonicalSourceRegistry` (parses the TOML,
  handles the `[[canonical_sources]]` array-of-tables) and
  `validate_registry_schema(registry: CanonicalSourceRegistry) -> list[str]` (returns
  a list of error strings; empty list means valid) — these two function names/shapes
  are what `check_canonical_source_conflicts.py` already expects to import.
- Implement the four validation checks as part of `validate_registry_schema()` or as
  separate composable functions it calls: path-existence (REQ-004, resolve each
  `source_paths` entry against repo root, fail with the missing path named), single-
  source-vs-multi enforcement (REQ-005, re-expressed per Assumptions), claim-type
  validation against `M-01-01`'s 13 types (REQ-007), and ADR-status check for
  `architecture-decision`-claim-type entries (REQ-006, parse the target's `## Status`
  section per row 01's confirmed format).

## Alternatives considered
- Build this tool against this Plan's originally-proposed nested-table schema and
  treat the existing flat-schema TOML file as needing a future migration: rejected —
  would leave this new tool unable to validate anything against the one registry file
  that currently exists, defeating REQ-004/AC11's own requirement that the tool
  "exits 0 against the registry's own illustrative entry."

## Implementation
### Target file
`tools/check_canonical_source_registry.py`

### Procedure
1. Re-confirm the registry file's current schema (row 01) immediately before writing
   this tool's dataclasses, in case a schema-unification decision landed between this
   row's authoring and its implementation.
2. Implement `RegistryEntry`/`CanonicalSourceRegistry` dataclasses per Design
   decisions.
3. Implement `load_registry()` using `tomllib` (stdlib, no new dependency).
4. Implement `validate_registry_schema()` covering: path-existence (REQ-004);
   `source_paths` length enforcement (REQ-005, `len > 1` allowed only for
   `claim_type in {"runtime-behavior", ...}`); claim-type membership in `M-01-01`'s 13
   types (REQ-007); ADR-status check when `claim_type == "architecture-decision"`
   (REQ-006) — resolve the referenced source path, confirm it matches
   `docs/adr/ADR-{NNN}-*.md`, read its `## Status` section, fail if not `Accepted`.
5. Add a CLI entry point (`main()`) that loads the registry, runs validation, prints
   errors, and exits 1 if any error was found, 0 otherwise — matching this Plan's
   AC11 ("`uv run python tools/check_canonical_source_registry.py` exits 0 against
   the registry's own illustrative entry").
6. In this row's own completion report, flag the residual gap: even after this row
   lands, `check_canonical_source_conflicts.py`'s own internal `RegistryEntry`
   dataclass (a different, hardcoded definition inside that file, not imported from
   here) still won't align field-for-field with this module's schema — that file's
   own fallback-loader bug (confirmed in row 01) is unaffected by this row alone.

### Method
Confirmed this cycle (2026-09-06) via direct read: registry file's actual 2 entries
(row 01); `check_canonical_source_conflicts.py`'s expected import names
`load_registry`/`validate_registry_schema` (that file's lines 44-47); `M-01-01`'s 13
claim types (`docs/00_governance_01_documentation-policy.md` lines 73-123, read
earlier this session for `M-01-02`'s procedure documents); ADR `## Status` section
format (`docs/adr/ADR-003-...md` line 17-19, read earlier this session).

### Details
No change to `check_canonical_source_conflicts.py` itself.

## Compatibility considerations
Once this tool exists, `check_canonical_source_conflicts.py`'s `HAS_REGISTRY_VALIDATOR`
import succeeds (previously `False`, silently falling back) — its behavior changes
from "always uses the broken fallback parser" to "uses this tool's `load_registry()`
then re-wraps results into ITS OWN incompatible `RegistryEntry` shape via its
`detect_all_conflicts()` (lines 683-697, confirmed this cycle) — that re-wrapping
code accesses `val.get("target", "")`/`val.get("authority", "")` etc. on this tool's
returned dict-like structure, which won't match this schema's actual field names
(`decision_target`, no `authority` field) either. This means completing this row
will likely change `check_canonical_source_conflicts.py`'s behavior from
"silently finds nothing" to "raises an AttributeError/KeyError or falls through to
`except (ValueError, KeyError, TypeError): entries = _load_registry_toml(registry_path)`"
(its own except clause, line 698) — re-confirm this at implementation time; it is
not a regression this row directly causes fixing, but it is a behavior change worth
flagging to whoever owns that other tool's Plan.

## Security considerations
Path-existence checks must resolve paths safely (no traversal outside repo root) —
reuse the same `Path` resolution pattern already used elsewhere in `tools/`.

## Rollback considerations
New file — revert via `git rm tools/check_canonical_source_registry.py` if seq 03's
tests find the schema decision needs revisiting.

## Validation plan
- `uv run pytest tests/tools/test_check_canonical_source_registry.py -v` (seq 03).
- `uv run python tools/check_canonical_source_registry.py` — exits 0 against the
  actual registry file's 2 entries.
- `uv run python tools/check_canonical_source_conflicts.py --registry
  config/documentation_canonical_sources.toml` — re-run and document any behavior
  change per Compatibility considerations (informational, not a pass/fail gate for
  this row).
- `uv run mypy tools/check_canonical_source_registry.py`.

## Completion criteria
- The tool validates the actual registry file's schema and exits 0 against it.
- `load_registry`/`validate_registry_schema` function names match what
  `check_canonical_source_conflicts.py` already expects to import.
- The residual `check_canonical_source_conflicts.py` field-shape mismatch is reported,
  not silently left for a future session to rediscover from scratch.

## Out of scope
- `tools/check_canonical_source_conflicts.py`'s own field-shape reconciliation — a
  candidate follow-up for its owning Plan.
- `config/documentation_canonical_sources.toml` — tracked in seq 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Building this tool will likely change (not fix) `check_canonical_source_conflicts.py`'s behavior from silent-pass to a raised exception, per Compatibility considerations — needs a human decision on whether to also patch that file's field-shape mismatch in the same change or file it separately | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260903-103027_m0104_introduce-machine-readable-canonical-source-registry.md
- **Source plan**: plans/20260905-165405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150039
- **Related target files**: tools/check_canonical_source_registry.py
