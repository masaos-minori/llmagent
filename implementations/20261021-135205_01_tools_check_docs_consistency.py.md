## Goal
Extend `tools/check_docs_consistency.py` with report-only (Warning) detection for the identifier-matching gap: bare snake_case variable references (backtick names with no trailing `()`) and/or non-`_db_path` config-key names that no current mechanism verifies against `scripts/` / `config/`.

## Scope
- Modify exactly `tools/check_docs_consistency.py`: add report-only (Warning) detection for the uncovered reference forms selected in Phase 1 (UNK-02).
- Introduce no blocking gate; the check must pass (no failures) on the current corpus.
- If a shared matcher is warranted, add it to `tools/_docs_consistency_lib.py` (separate row) and import it here.
- Keep `tools/TOOL_DESCRIPTIONS.md` in sync if the documented capability changes (separate row).

## Assumptions
- The owner's decision is recorded before this executes (Plan REQ-001); this procedure documents the "mechanical" branch so it can be applied once decided.
- The routing policy ("extend the existing tool, do not write a new one-off script") and `AGENTS.md` Global Rule 7 hold; if they do not, this row is out of scope until the Plan is amended.
- Bare-variable checking uses an allowlist mechanism (`# ...-ok` style, as other tools do) to control false positives on prose words in backticks (UNK-02).

## Design decisions
- Extend `check_docs_consistency.py` via `_docs_consistency_lib.py` rather than adding a new one-off script (routing.md "When to run which tool"; AGENTS.md Global Rule 7).
- Start report-only (Warning) and require passing on the current corpus (Constraints).
- Use the canonical config model or `config/*.toml` as the source of truth for config-key checks, not a hardcoded list (Implementation Intent).

## Alternatives considered
- Recording an accepted limit instead: out of scope for this row — that is the `docs/00_governance/governance_04_documentation-checks.md` row (REQ-003/REQ-004).
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`tools/check_docs_consistency.py`

### Procedure
1. Confirm the owner's decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. Phase 1 selection (UNK-02): measure which snake_case-only / config-key references `check_docs_consistency.py` already verifies on the live `docs/`; define the minimal uncovered forms and their canonical source; record the false-positive rate on a real diff. Select the exact forms to implement.
3. Add report-only (Warning) detection for the uncovered forms to the appropriate generic (`funcrefs`) or domain (`configkey`) check.
4. Add fixture tests to `tests/tools/test_check_agent_docs_consistency.py` (this row).
5. Add an allowlist mechanism for bare variables if chosen; pass lint, type check, bandit; update `tools/TOOL_DESCRIPTIONS.md` if the capability changed.

### Method
- Locate the generic `funcrefs` check (`check_function_references`, imported into `check_docs_consistency.py`) and the deployment-domain `configkey` check (`check_config_key_presence`). The bare-variable check fits the `funcrefs` generic path; config-key coverage fits `check_config_key_presence`.
- Implement: extract backtick-quoted identifiers with no trailing `()` and compare against defined names under `scripts/`; extract `[section].key` config forms and compare against the canonical config model / `config/*.toml`. Emit mismatches at Warning level with an allowlist hook (`# ...-ok`).
- Do not introduce a blocking gate; the check must pass on the current corpus.

### Details
- Verified at planning time: `check_function_references` already matches any `[a-zA-Z_][a-zA-Z0-9_]{3,}` identifier followed by `()` (snake_case `name()` forms are covered); `check_config_key_presence` only flags `*_db_path` keys; zero non-`_db_path` config-ish references exist on the live corpus. The only genuine gap is bare snake_case variable references, which is high-false-positive risk and requires the allowlist.
- The exact uncovered forms and whether a shared matcher in `_docs_consistency_lib.py` is warranted are decided in Phase 1 (UNK-02); until then this names the concrete target file above. If implementing requires a file not listed in `Implementation Target Files`, that is an additional-target-file discovery — stop and report `Blocked`.

## Compatibility considerations
- The tool is used by CI/pre-commit; `tools/TOOL_DESCRIPTIONS.md` must stay in sync, and the check must not fail on the existing corpus.

## Security considerations
Report-only (Warning) detection over local docs/scripts/config; no secrets, network, or access changes.

## Rollback considerations
Revert the commit that edits the tool and its tests; revert the `TOOL_DESCRIPTIONS.md` update if present.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Extended docs checker | Live baseline + fixture diff | `uv run python tools/check_docs_consistency.py --domain <each>`; unit test with a stale bare snake_case / non-`_db_path` config fixture | Report-only (Warning); passes on current corpus |
| Changed tool | Lint / type / security | `uv run ruff check`, `uv run mypy tools/<file>.py`, `uv run bandit tools/<file>.py` | Pass |
| `tools/TOOL_DESCRIPTIONS.md` | Tool-description sync | `uv run python tools/check_tool_descriptions_sync.py` | Pass |
| Existing suite | Regression | `uv run pytest tests/tools/test_check_agent_docs_consistency.py` | Green |

## Completion criteria
- `check_docs_consistency.py` reports (Warning) the uncovered bare snake_case / non-`_db_path` config-key references.
- Fixture tests cover a valid and a stale uncovered reference; live runs pass on the current corpus; existing suite green.
- `ruff`, `mypy`, `bandit` pass; `check_tool_descriptions_sync.py` passes if the tool description changed.
- No blocking gate introduced.

## Out of Scope
- Adding a new one-off script against the routing policy.
- Introducing a blocking gate.
- Fixing every stale reference found (triage and file follow-ups instead).
- Enumerate-generalization detection (separate `compressverify` issue).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Select uncovered reference forms + canonical source via live-docs measurement (UNK-02) | Pending | — | — | Added to Plan Implementation Target Files before implementing this row |
| 2 | Add report-only (Warning) detection to the appropriate check + allowlist | Pending | — | — | Branch selected by owner decision (REQ-001) |
| 3 | Run lint/type/bandit, `check_tool_descriptions_sync.py`, and existing suite | Pending | — | — | Depends on step 2 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / accept-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (define uncovered forms + canonical source; measure FP rate) and `REQ-003` (extend the existing tool with report-only detection) — add bare-snake_case / non-`_db_path` config-key detection to `check_docs_consistency.py`
- **Source issue**: `issues/20261021-100351_identmatch_extend-identifier-matching-to-snake_case-names-and-config-keys-in-docs-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-125149_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-135205
- **Related target files**: `tools/check_docs_consistency.py`
