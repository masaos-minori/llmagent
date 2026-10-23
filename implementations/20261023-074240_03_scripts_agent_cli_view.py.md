## Goal

Route `scripts/agent/cli_view.py`'s multiline continuation read through the instance-owned `StdinReader`, and remove the private `ThreadPoolExecutor`, its `__del__` cleanup, and the `concurrent.futures` import that keep a joinable pool worker alive across process exit (`plans/20261022-040200_plan.md`, REQ-005, REQ-007, REQ-008, REQ-011; AC-2, AC-4, AC-5, AC-7).

## Scope

Modify only `scripts/agent/cli_view.py`: replace the private-pool read in `read_multiline`, delete the pool attribute, `__del__`, and the `concurrent.futures` import, and reword the docstring rationale. Keep the public signature, the `Reader` protocol, `_INPUT_TIMEOUT_S`, and the `raise KeyboardInterrupt` mapping byte-identical.

## Assumptions

- `CLIView` owns one `StdinReader` instance for its lifetime, used only from the loop that runs `read_multiline`.
- The `"... "` prompt and the continuation stop conditions (no trailing backslash, empty line, EOF, Ctrl-C) are preserved exactly.

## Design decisions

- The pool attribute (`self._input_executor`) and its lazy-creation branch are removed; the read becomes `cont = await asyncio.wait_for(self._stdin_reader.read(prompt="... "), timeout=_INPUT_TIMEOUT_S)`. The `asyncio.wait_for` bound is kept unchanged, so the 30 s `TimeoutError` → `KeyboardInterrupt` mapping is preserved (`AC-4`).
- `__del__` is deleted (nothing to shut down now); `import concurrent.futures` is deleted (no longer referenced).
- The docstring's stated rationale ("the default ThreadPoolExecutor is saturated") is corrected to describe what the code now bounds (a blocked daemon read that would otherwise delay exit).

## Alternatives considered

N/A: the Plan fixes the mechanism; this row performs the mechanical substitution and deletions.

## Implementation

### Target file

`scripts/agent/cli_view.py`

### Procedure

1. Delete `import concurrent.futures` (`:13`).
2. In `CLIView.__init__`, delete the `self._input_executor` attribute assignment (`:112`) and the `__del__` method (`:114-118`).
3. Import `StdinReader` from `scripts/agent/stdin_reader.py`.
4. In `read_multiline`, replace the lazy-pool block (`:285-289`) with a single call: `cont = await asyncio.wait_for(self._stdin_reader.read(prompt="... "), timeout=_INPUT_TIMEOUT_S)`.
5. Reword the `read_multiline` docstring rationale (`:277-280`) to describe the bounded daemon read.

### Method

- The three `except (EOFError, KeyboardInterrupt): break` (`:296-297`) and the `except TimeoutError` warning + `raise KeyboardInterrupt` (`:293-295`) stay as written; only the submission line changes.
- Keep `_INPUT_TIMEOUT_S = 30` (`:24`) untouched (`grep -n "_INPUT_TIMEOUT_S = 30" scripts/agent/cli_view.py` must still match, `AC-4`).

### Details

- Keep `read_multiline`'s signature (`:267-269`) and the `Reader` protocol (`:74-84`) byte-identical, including the currently-unused `loop` parameter (this Plan does not remove it).
- Verify dead-code and reference-table drift: `uv run vulture scripts/agent/cli_view.py --min-confidence 80` and `uv run python tools/generate_reference_table.py --check --type agent` report nothing (`AC-7`).

## Compatibility considerations

No public top-level symbol changes; `read_multiline` is a method and `Reader` is unchanged, so `docs/23_agent/agent_13_reference-api-generated.md` needs no regeneration (`AC-7`). This file is a shared Frozen target with repl001; this row touches only `read_multiline`'s body, not tab completion/history (`:100-160`).

## Security considerations

N/A: no new trust boundary or data path.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/cli_view.py` | Regression on the five continuation cases plus the new timeout case; dead-code and reference-table drift checks. | `uv run pytest tests/test_cli_view.py -q` ; `uv run vulture scripts/agent/cli_view.py --min-confidence 80` ; `uv run python tools/generate_reference_table.py --check --type agent` | Continuation behavior unchanged; timeout case asserts `KeyboardInterrupt`; no unused code; generated table unchanged (AC-4, AC-7). |

## Completion criteria

- `cli_view.py` contains no `concurrent.futures` reference and no `__del__`.
- `TestReadMultilineTimeout` passes (with `_INPUT_TIMEOUT_S` monkeypatched far from 30, blocking `input` stub → asserts `KeyboardInterrupt` and no non-daemon thread left behind).
- The five existing `TestReadMultiline` cases pass unchanged.

## Out of Scope

The primary prompt reads (`repl_input_loop.py`, row 2) and the approval prompt (`tool_approval.py`, row 4). Removing the unused `Reader` protocol or `read_multiline`'s `loop` parameter.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewire `scripts/agent/cli_view.py` and delete its pool, `__del__` and import | In Progress | 20261023-074240 | — | REQ-005, REQ-007, REQ-008, REQ-011; AC-2, AC-4, AC-5, AC-7 |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-007, REQ-008, REQ-011
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `scripts/agent/cli_view.py`
