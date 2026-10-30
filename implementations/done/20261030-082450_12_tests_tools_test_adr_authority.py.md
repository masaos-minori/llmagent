## Goal
Create `tests/tools/test_adr_authority.py` (new): unit tests for the validator core and CLI — duplicate primaries, dangling IDs, authority cycles, assumption drift, unknown edge types, and front-matter divergence each fail; a conforming model passes (REQ-004 tests).

## Scope
- In scope: this test module.
- Out of scope: generator tests (row 13), tool implementations (rows 03–05), fixtures beyond tmp sandbox files.

## Current shape (facts)
- `tests/tools/` exists with per-tool precedents verified on disk: `test_check_adr_invariant_matrix.py`, `test_check_adr_reference.py`, `test_check_adr_structure.py`, `test_check_auto_check_inventory.py`, `test_check_canonical_source_registry.py` family — sandbox-fixture style (tmp_path model files) is the pattern to copy.
- The validator design and finding codes are defined in `implementations/20261030-082450_04_tools_check_adr_authority.py.md` (`DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, `ASSUMPTION_DRIFT`, `EDGE_UNKNOWN_TYPE`, `FRONTMATTER_DIVERGENCE`).

### Verified 20261030 (adversarial pass)
- Confirmed precedent files on disk: `tests/tools/test_check_adr_reference.py`, `test_check_adr_invariant_matrix.py`, `test_check_adr_structure.py`, `test_check_auto_check_inventory.py`, `test_check_adr_preservation.py`, and `test_generate_reference_table.py` (row 13's precedent lives in `tests/tools/` after all — the procedure's "may be under another tests subtree" hedge resolved).
- Confirmed idiom (docstring of `test_check_adr_reference.py`): direct function calls against tmp_path fixture files, no subprocess; live-repo validation is explicitly NOT duplicated as a unit test there. The CLI exit-code lock planned here (runpy/subprocess) must be re-confirmed against these precedents when writing — if no precedent calls subprocess, use `main()`-return-value assertions instead of subprocess spawning.

## Assumptions
- Test-first contract: these tests are written to fail before row 04 lands and pass after it; if executed out of `seq` order they must error at import (`tools/_adr_authority_core`) — no skip-if-missing softening (import failure is the contract lock).
- Fixture strategy: a minimal conforming model fixture (3–4 authorities, a few typed edges incl. one intentional `Reference` cycle, four assumptions with one `config-check`) plus one mutation per finding code; the `config-check` drift fixture writes a sandbox `config/agent.toml`-shaped file, not the live one.
- Front-matter divergence fixtures use sandbox ADR-shaped markdown files (front matter only) — not `docs/10_adr/` contents.

## Design decisions
- Test the core module's functions directly (deterministic, no CLI subprocess) plus one CLI-surface test via `runpy`/subprocess on the conforming fixture to lock exit codes (0 clean, 1 on any finding) and `--format json` shape — same approach as `test_check_adr_reference.py` precedent (confirm exact precedent mechanism at implementation by reading that file).
- One test per finding code + one "all clean" test + one "multiple findings aggregate" test; names encode the finding code for mutation-test traceability.

## Alternatives considered
- Extending `test_check_adr_reference.py` — rejected: the plan names a dedicated module; the two tools' test surfaces diverge (model fixtures vs source-token fixtures).

## Implementation
### Target file
- `tests/tools/test_adr_authority.py` (new)

### Procedure
1. Read `tests/tools/test_check_adr_reference.py` and `test_check_adr_invariant_matrix.py` for fixture/import idioms before writing.
2. Author conforming fixture + six finding-code mutation tests + CLI exit-code/json tests + config-check drift test.
3. Run `uv run pytest tests/tools/test_adr_authority.py` after rows 02–05 land; keep green thereafter.

### Method
New pytest module under `tests/tools/`; deterministic (tmp_path only, no network, no live config mutation).

### Details
- `AUTHORITY_CYCLE` fixture: `A --Requires--> B --Governs--> A` fails; the same pair as `Reference` with `intentional = true` passes — proving the graph split (REQ-001) is enforced, not incidental.

## Compatibility considerations
- `.github/run_cited_adr_tests.py` and the invariant matrix are unaffected (no ADR cites these tests initially; if ADR-016 rows later cite them, that is row 01/06 coordination — out of scope here).

## Security considerations
- None.

## Rollback considerations
- Test module reverts with row 04 (its import target).

## Validation plan
- `uv run pytest tests/tools/test_adr_authority.py` green post-implementation; red (import/behavior) before rows 02–04 land.
- Mutation spot-check: flipping a fixture authority to a second primary must fail exactly `DUP_PRIMARY` (finding-code assertion, not just nonzero).

## Completion criteria
- All six finding codes have failing fixtures; conforming fixture clean; exit codes locked.

## Out of Scope
- Generator tests (row 13), live-docs integration (row 11's CI run covers it).

## Execution Status

### Execution Status
| Status | Started | Completed | Notes |
|---|---|---|---|
| Completed | 20261030-193223 | 20261030-193223 | Adversarial verification complete 20261030: precedents confirmed in tests/tools/; direct-call idiom documented, CLI-lock mechanism to be finalized against precedent at writing. Lands after rows 04/05. |

### Blocker Log
| Date | Blocker | Impact | Resolution |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Type | Status | Notes |
|---|---|---|---|
| — | — | — | — |

## Traceability
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 12, REQ-004 (Tests section bullet 1).