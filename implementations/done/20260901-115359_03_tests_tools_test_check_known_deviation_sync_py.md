## Goal
Add `tests/tools/test_check_known_deviation_sync.py` using fixture ADR and Known
Issues documents, covering an ID with matching Status (no report), an ID with
disagreeing Status (reported), and an ID referenced by an ADR but absent from
every canonical document (reported as dangling) (REQ-008).

## Scope
- In scope: fixture-based unit tests for the match/mismatch/dangling cases plus
  a regression case mirroring the false-positive-avoidance scenario
  (`ADR-004-D1-profile-config-model-still-present`-shaped slug) and a case
  mirroring "canonical document defines no ID headings at all".
- Out of scope: live-repository validation (AC-1, AC-2, AC-3, AC-4, AC-5 are
  exercised as a one-time manual/agent-run check per the source Plan's Tests
  section, not as `pytest` assertions, since the live tree's content can change
  independently of this tool's code).

## Assumptions
- `tools/check_known_deviation_sync.py` (seq 01 of this Plan) exposes its
  canonical-doc parser, ADR-side parser, and cross-check function as importable
  functions, matching `tests/tools/test_check_compat_shims.py`'s `tmp_path`/
  `monkeypatch` fixture-test pattern.
- Fixture documents are synthetic Markdown content written to `tmp_path`, not
  copies of the live `docs/` tree.

## Design decisions
- Each scenario builds its own minimal fixture pair (one canonical Known Issues
  document, one ADR document) rather than one large shared fixture, so a
  fixture change for one scenario cannot silently affect another's assertions.
- The false-positive regression test uses a bullet whose ID-shaped substring is
  immediately followed by another hyphen and alphanumeric characters (mirroring
  `ADR-004-D1-profile-config-model-still-present`'s shape), not a synthetic
  string invented independently of the real case that motivated REQ-002's
  anchoring rule.

## Alternatives considered
- Testing against the live `docs/` tree directly: rejected — the source Plan's
  Scope explicitly requires fixture documents, and the Tests section separates
  fixture-based `pytest` coverage from live-repository validation (the latter
  run manually, not as an automated test, since live content can drift
  independently).

## Implementation
### Target file
`tests/tools/test_check_known_deviation_sync.py`

### Procedure
1. **Matching case** (no report): fixture canonical document with `### ID-001`
   and `- **Status**: open`; fixture ADR with a `## Known Deviations` bullet
   `- **Known Issue**: ID-001 — ...` (open-like). Assert the cross-check
   produces no Status-mismatch or dangling finding for `ID-001`.
2. **Disagreeing-Status case** (reported): fixture canonical document with
   `### ID-002` and `- **Status**: resolved`; fixture ADR with a `## Known
   Deviations` bullet `- **Known Issue**: ID-002 — ...` (open-like, i.e. not
   `**Resolved**:`). Assert a Status-mismatch finding is produced for `ID-002`.
3. **Dangling case** (reported): fixture ADR references `- **Known Issue**:
   ID-003 — ...` in its `## Known Deviations` section, but no fixture canonical
   document defines a `### ID-003` heading anywhere in the discovered set.
   Assert a dangling-reference finding is produced for `ID-003`.
4. **False-positive-avoidance regression** (mirrors AC-7): fixture ADR
   `## Known Deviations` bullet `- **Known Issue**: ID-004-EXTRA-slug-suffix —
   ...` (an ID-shaped substring immediately followed by more hyphenated text,
   not whitespace/em-dash/end-of-line). Assert no finding is produced for a bare
   `ID-004` — the anchoring rule must not extract `ID-004` as a candidate ID
   from this bullet.
5. **No-ID-headings case** (mirrors AC-3): fixture canonical document defines
   zero `### <ID>` headings at all; a separate fixture ADR references an ID
   that would, in a normal fixture, belong to that document. Assert the
   reference is reported as dangling (the canonical document's emptiness is not
   treated as "the check does not apply here").

### Method
`pytest` test module using `tmp_path` for isolated fixture document directories;
imports `tools.check_known_deviation_sync`'s parsing/cross-check functions
directly (not via `subprocess`), matching
`tests/tools/test_check_compat_shims.py`'s direct-import pattern.

### Details
- Each fixture ADR file needs only a `## Known Deviations` section (and,
  where relevant to a scenario, a `## Related Documents` → `### Known Issues`
  subsection) — full ADR document bodies are not required.
- Each fixture canonical document needs only the `### <ID>: <title>` heading and
  its Status field (bullet-list form is sufficient for these tests; the
  inline-prose fallback format is this file's own scenario to add if REQ-001's
  dual-format parsing needs a dedicated regression case beyond what seq 01's own
  implementation already establishes).
- One test function per scenario at minimum, each building its own isolated
  `tmp_path` fixture tree.

## Compatibility considerations
New test file; no existing test module imports it. Adding it does not change any
existing test's behavior.

## Security considerations
Tests use `tmp_path` fixtures only — no writes outside pytest's managed temporary
directory, no network access.

## Rollback considerations
New file only; rollback is deleting
`tests/tools/test_check_known_deviation_sync.py`. No other test or module
depends on it.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_known_deviation_sync.py` | Unit (fixture-based) | `uv run pytest tests/tools/test_check_known_deviation_sync.py -v` | All fixture cases (match / mismatch / dangling / false-positive-avoidance / no-headings) pass |
| `tests/tools/test_check_known_deviation_sync.py` | Regression | `uv run pytest tests/tools/ -v` | No new failures (note: `tests/tools/test_check_agent_docs_consistency.py` has a pre-existing, unrelated collection error — not this file's responsibility) |

## Completion criteria
- `tests/tools/test_check_known_deviation_sync.py` exists and covers the
  matching, disagreeing-Status, dangling, false-positive-avoidance, and
  no-ID-headings scenarios against fixture documents.
- `uv run pytest tests/tools/test_check_known_deviation_sync.py -v` passes with
  no failures (requires `tools/check_known_deviation_sync.py` from seq 01 of
  this Plan to exist first).

## Out of scope
- Live-repository validation (AC-1, AC-2, AC-3, AC-4, AC-5) — run manually, not
  as a `pytest` assertion in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-161020 | 20260901-161020 | `tools/check_known_deviation_sync.py` (seq 01) exists and was read in full before writing the test file |
| 2 | Add or update tests per Validation plan | Completed | 20260901-161020 | 20260901-161020 | `tests/tools/test_check_known_deviation_sync.py` created; covers match/mismatch/dangling/false-positive-avoidance/no-ID-headings scenarios via tmp_path fixtures |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-161020 | 20260901-161020 | `ruff format`/`ruff check`/`mypy` clean; new tests 5/5 pass; `tests/tools/` full run 88 passed, 1 pre-existing unrelated collection error (`test_check_agent_docs_consistency.py`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-161020 | 20260901-161020 | N/A: no `docs/00_index.md` Document References by Task row matches `tests/tools/test_check_known_deviation_sync.py` |

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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20260831-194739_tool006_check_known_deviation_sync.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-112435_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-115359
- **Related target files**: `tests/tools/test_check_known_deviation_sync.py`
