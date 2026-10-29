## Goal

Align the `run_http()` docstring and the `# noqa: BLE001` justification with the actual
control flow — the posture gate runs before the `try` and its `SystemExit` is
intentionally uncaught — with zero runtime change (REQ-001, REQ-002, REQ-003).

## Scope

- `scripts/mcp_servers/server.py`: docstring lines 272-274 and the comment text after
  `# noqa: BLE001` at line 328. No executable line changes.

## Assumptions

- Verified control flow against current source: loopback check (`server.py:281-285`),
  config isolation (`server.py:287-297`), `self._enforce_startup_posture_gate()` at
  line 299, `uvicorn.Config` / server build at 319-325, `try` at line 326,
  `except SystemExit` at 328-332 (logging + re-raise), `except KeyboardInterrupt` at
  333-334, `if not server.started:` follow-up at 335-336.
- `test_failed_posture_exits_before_binding`
  (`tests/mcp_servers/test_posture_gate_start_path.py`) pins the uncaught propagation;
  the rewritten docstring must describe exactly that.

## Design decisions

- Documentation-only fix (Plan option (b)): the uncaught `SystemExit(1)` is the intended
  fail-closed outcome; moving the gate into the `try` is a behavior change out of scope.
- Keep the `# noqa: BLE001` token byte-identical and change only the justification text
  after it — removing or altering the token would re-trigger the ruff finding.

## Alternatives considered

- N/A: option (a) (moving the gate call into the `try`) rejected in the Plan's Design
  section as a behavior change.

## Implementation
### Target file

`scripts/mcp_servers/server.py`

### Procedure

Replace docstring lines 272-274 and the comment after the noqa token at line 328.

### Method

New docstring closing paragraph (replacing the "Catches ``SystemExit`` ... consistent
error output across all launch paths." sentences):

```
The loopback check, config isolation, and ``_enforce_startup_posture_gate()`` all run
before the ``try`` below, so a gate ``SystemExit`` intentionally propagates uncaught out
of ``run_http()`` (fail-fast: the process terminates via the uncaught ``SystemExit(1)``
before any socket is created).
```

New noqa justification (token unchanged, text after the dash replaced):

```python
        except SystemExit as e:  # noqa: BLE001 — SystemExit originating from server.run() itself; logged and re-raised
```

### Details

- Line 328 stays `except SystemExit as e:  # noqa: BLE001 — ...` with the code token and
  the handler body (log message string, `raise`) byte-identical (REQ-003).
- `git diff` must show only the docstring paragraph and this comment text.

## Compatibility considerations

- N/A: text-only change in a base class imported by every MCP server module; no call
  site, signature, or import changes.

## Security considerations

- The rewrite removes a false claim that gate failures are logged inside `run_http()`;
  fail-closed behavior is unchanged. The handler's gate-specific log message string
  stays as-is (report flag recorded in the Plan, not fixed here).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py -v` — both existing
  tests green, unchanged (T1).
- T2 consistency re-read of `server.py:266-336` after the edit.
- `uv run ruff check scripts/mcp_servers`; `uv run mypy --no-namespace-packages scripts/mcp_servers`;
  `git diff` review confirming a docstring/comment-only diff (T3).
- `PYTHONPATH=scripts uv run lint-imports` — unchanged imports.

## Completion criteria

- No docstring claim that `run_http()` catches the gate's `SystemExit` remains; the text
  states the before-`try` order and intentional propagation (AC-1).
- The noqa justification names only `SystemExit` from `server.run()` (logged, re-raised,
  with the `if not server.started: sys.exit(1)` follow-up) (AC-2).
- The diff touches only docstring/comment text and the posture-gate test file stays
  green (AC-3).

## Out of Scope

- Gate call placement, handler body, log message string, exit paths (frozen per the
  Issue); loopback-binding logic; other servers' posture gates.
- `tests/mcp_servers/test_posture_gate_start_path.py` — reference only.
- All `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite docstring + noqa justification per Method/Details | Pending | — | — | REQ-001, REQ-002 |
| 2 | Run the T1-T3 consistency/static gates (docs checkers, `rules/toolchain.md`) | Pending | — | — | REQ-003; no new tests in scope |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (docstring states true control flow), REQ-002 (noqa
  justification describes actual handler coverage), REQ-003 (zero runtime change)
- **Source issue**: issues/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-080042_ebrev003_serverbase-posture-gate-outside-try.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-140245
- **Related target files**: scripts/mcp_servers/server.py
