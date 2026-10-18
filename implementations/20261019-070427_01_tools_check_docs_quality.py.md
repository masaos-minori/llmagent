## Goal

Extend `check_docs_quality.py`'s `check_stale_patterns` custom rule with a new entry that flags
Markdown references whose target is a **canonical document that is absent from the corpus**
(never created, removed, or renamed), emitted at `Warning` severity. This closes the documented
`Partial` gap for GV-011 without changing `check_docs_structure.py`'s `check_links`
link-reachability.

## Scope

- **In-Scope**:
  - Add a `stale_patterns` entry that flags references whose target canonical document is absent
    from the corpus.
  - Extend `check_stale_patterns` with per-pattern severity so the new pattern is `Warning` while
    existing patterns keep their `ERROR` behavior.
  - Bound the new pattern to canonical-language references so it does not duplicate
    `check_docs_structure.check_links`.
  - Update the GV-011 matrix row to `Existing` and clear its follow-up note.
- **Out-of-Scope**:
  - Changing `check_docs_structure.py` link-reachability behavior.
  - Other `stale_patterns` gaps beyond canonical-document references.

## Assumptions

- `Issue(severity: str)` accepts `"WARNING"` (it is used elsewhere in this module and counted at
  the reporting stage), so the new finding can be emitted at `Warning`.
- "Canonical document reference" can be scoped to references in canonical language ("the
  canonical source for", "authoritative source for", "normative reference for") pointing at a
  path that does not exist in the corpus — distinct from a generic internal link.
- The set of canonical document paths can be derived from the registry or from canonical-language
  mentions; used only to scope detection, not to validate the registry.

## Design decisions

- Extend (do not rewrite) `check_stale_patterns`. Add per-pattern severity to the currently-empty
  `default_patterns` mechanism (currently `dict[str, str]`) so each pattern carries its own
  severity; existing patterns (none currently configured) and any future ones keep their behavior.
- Detect Markdown link/reference syntax (`[text](path)` / `[text][ref]` resolved against the
  corpus) whose target path does NOT exist AND which appears in canonical language. This scopes
  detection to canonical references and avoids duplicating `check_links` for generic dangling
  links.
- Fail safe toward no false positive when the canonical scope cannot be determined.

## Alternatives considered

- Adding the pattern outside `check_stale_patterns` (a separate check) — rejected: the plan and
  GV-011's matrix route this through `stale_patterns`; a separate check would fragment the
  staleness logic.

## Implementation

### Target file

`tools/check_docs_quality.py`

### Procedure

1. Read `check_stale_patterns` (currently at line ~496): `default_patterns: dict[str, str] = {}`
   and a hardcoded `"ERROR"` severity in the emitted `Issue`.
2. Extend `default_patterns` to carry per-pattern severity, e.g. `dict[str, tuple[str, str]]`
   mapping `pattern_name -> (regex, severity)`. Keep iteration backward-compatible with any
   existing entries.
3. Add the absent-canonical-document pattern: a regex matching Markdown link/reference syntax
   whose target path is absent from the corpus, gated on canonical-language context. Emit it at
   `"WARNING"`.
4. Reconcile severity: the new pattern emits `"WARNING"`; existing patterns keep `"ERROR"`. Do
   not change the global severity handling.
5. Coordinate with `check_docs_structure.check_links` (line ~248): restrict the new pattern to
   canonical-language references so generic dangling links remain solely `check_links`'s
   responsibility (no double-reporting).

### Method

- **Pattern scope (UNK-02/03).** Match `[text](path)` / `[text][ref]` where `path` does not exist
  in the corpus AND the surrounding line contains a canonical-language marker. Identify the
  referenced path as canonical via canonical-language mention (self-contained); optionally
  intersect with registry paths from `config/documentation_canonical_sources.toml`. Fail safe
  (no match → no flag) when ambiguous.
- **Per-pattern severity (UNK-01).** Store `(regex, severity)` per entry; emit `"WARNING"` for
  the canonical-reference entry and `"ERROR"` for any other entry. Document the precedence.
- **Dedup (REQ-003).** Do not re-implement reachability; rely on `check_links` for generic
  dangling links. The new pattern fires only on canonical-language references.

### Details

- `REQ-001`: a Markdown reference whose target is an absent canonical document is flagged.
- `REQ-002`: the finding is emitted at `"WARNING"` (non-blocking).
- `REQ-003`: the pattern is scoped to canonical references; generic dangling links stay with
  `check_links` (no duplicate reporting).
- `REQ-004`: no false positives on the current `docs/` corpus for legitimate cross-domain or
  templated/placeholder references.
- **UNK-01:** extend `default_patterns` to per-pattern severity; the canonical-reference pattern
  is `Warning`, existing patterns unchanged.
- **UNK-02:** scope to canonical-language references pointing at a non-existent path; record the
  boundary in-code.
- **UNK-03:** prefer canonical-language mention scoping (self-contained); optionally intersect
  with registry paths.

## Compatibility considerations

Additive pattern only; existing `stale_patterns` findings and `check_links` behavior unchanged.
The new finding is `Warning` and does not affect the gate's blocking behavior.

## Security considerations

N/A: reads local `docs/`; applies read-only regexes; executes no user input.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_quality.py` | Format/lint | `uv run ruff format tools/ && uv run ruff check tools/` | Clean |
| `tools/check_docs_quality.py` | Type check | `uv run mypy --no-namespace-packages tools/` | Clean |
| `tools/check_docs_quality.py` | Security | `uv run bandit -r tools/ -c pyproject.toml -ll` | No high/medium |
| `tools/check_docs_quality.py` | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |
| `tools/check_docs_quality.py` | Unit + corpus | `uv run pytest tests/tools/test_check_docs_quality.py` then corpus run | Dangling canonical flagged at Warning; valid reference/corpus clean |
| Whole change | Full regression | `uv run pytest` + `uv run pre-commit run --all-files` | Existing `check_stale_patterns`/quality suites still pass |

## Completion criteria

- `check_stale_patterns` flags absent-canonical-document references at `Warning` with per-pattern
  severity; existing patterns unchanged.
- Unit tests cover the passing and failing path for REQ-001/002 plus a corpus run with zero false
  positives (REQ-004).
- The GV-011 matrix row reports automated detection with the follow-up note cleared.

## Out of scope

Changing `check_docs_structure.py` link-reachability behavior and other `stale_patterns` gaps.

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (extend `check_stale_patterns` with an absent-canonical-document pattern at `Warning`)
- **Source issue**: `issues/done/20261018-173143_gov011_extend-stale_patterns-config-to-cover-canonical-document-references.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-180921_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-070427
- **Related target files**: `tools/check_docs_quality.py`
