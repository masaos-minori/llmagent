## Goal

Align the `HttpAugment.run` docstring in `scripts/rag/http_augment.py` with the actual
terminal-empty behavior by rewriting only the `""` bullet to state that an empty-string result is a
valid empty remote response returned as the final augment result with **no** in-process fallback.
This removes a docstring contradiction that both the implementation and the other two RAG
docstrings (`pipeline_service.py`, `pipeline.py`) already treat as terminal, without changing any
runtime behavior.

## Scope

- **In-Scope**:
  - Rewrite the `""` bullet of the `HttpAugment.run` docstring to describe the actual terminal
    behavior (returns `""`; no in-process fallback), preserving the identity-vs-truthiness
    distinction (`""` vs `None`).
- **Out-of-Scope**:
  - Any change to runtime behavior, the `augment()` try/finally control flow, or the
    `call_rag_service` empty/transient classification.
  - The `None`-means-fallback contract, auth fail-closed behavior.
  - The `None`/`in_process_fallback` and `None`/`auth_error` docstring bullets.
  - `pipeline_service.py` or `pipeline.py` docstrings (already terminal).
  - `docs/*.md`, or any test file.

## Assumptions

- The change is a pure docstring rewrite with zero runtime effect; `ruff`/`mypy` see no semantic
  change.
- The empty-remote contract is already locked by the CI-blocking
  `tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process`, which asserts
  `RagPipeline.augment()` returns `""` for an HTTP 200 empty remote result and never invokes the
  in-process pipeline (ADR-010 INV-03). No new test is required.
- The intended product policy is that an empty remote answer is authoritative ("nothing relevant"),
  i.e. terminal — a judgment call supported by repository evidence, not a new requirement.

## Design decisions

- Scope the edit strictly to the `""` bullet; leave all other bullets and the identity-vs-truthiness
  note untouched.
- Keep the wording consistent with `pipeline_service.py` ("Not a failure") and `pipeline.py`
  (`str/"" (final)`), and with ADR-010 INV-03 ("An empty result is treated as a valid result").
- Preserve the `is not None` vs truthiness note so the subtle contract is not lost.

## Alternatives considered

- "Correcting" the code to fall back on an empty remote result — rejected: it would change user-facing
  behavior contrary to ADR-010 INV-03 and the CI-blocking test; the docstring is the only thing that
  disagrees with the code.
- Adding a new test at the `augment()` level — rejected: the contract is already pinned by
  `test_remote_empty_does_not_trigger_in_process`.

## Implementation

### Target file

`scripts/rag/http_augment.py`

### Procedure

1. Read `scripts/rag/pipeline_service.py`, `scripts/rag/pipeline.py`, and `scripts/rag/augment.py`
   to confirm the terminal-empty contract and the identity-vs-truthiness distinction before editing
   (REQ-001).
2. Locate the `HttpAugment.run` docstring (the `""` bullet is currently at
   `scripts/rag/http_augment.py:105-106`):
   ```
             - ``""`` (empty string): valid but empty result; caller should fall back
               to in-process search
   ```
3. Replace that single bullet with terminal-empty wording, e.g.:
   ```
             - ``""`` (empty string): valid empty remote response; returned as the final
               augment result with no in-process fallback
   ```
   Keep the same indentation and list style as the surrounding bullets.
4. Leave the `None`/`in_process_fallback` and `None`/`auth_error` bullets and the
   identity-vs-truthiness note (lines 112-115) exactly as they are.
5. Run `ruff` and `mypy` on `scripts/rag/http_augment.py`, then run
   `tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process` (and the
   affected RAG augment tests) to confirm no regression (REQ-002, AC3).

### Method

- **Edit only the `""` bullet.** Use an exact-match replacement of the two-line bullet so no other
  text changes. Do not reflow the surrounding bullets or the identity-vs-truthiness note.
- **State the terminal contract.** The rewritten bullet must convey that `""` is a valid empty remote
  response that terminates the augment call (no in-process fallback), matching `pipeline.py`'s
  `"" (final)` and `pipeline_service.py`'s `"empty"` = "Not a failure".
- **Preserve the `is not None` distinction.** The identity-vs-truthiness note already distinguishes
  `""` (valid empty remote response) from `None` (remote could not produce a response); keep it
  intact so the contract is not muddied.

### Details

- `REQ-001`: the `HttpAugment.run` docstring `""` bullet describes the actual terminal behavior
  (returns `""`; no in-process fallback), consistent with `pipeline_service.py` and `pipeline.py`.
- `REQ-002`: no runtime behavior changes; the existing empty-remote contract remains locked by
  `test_remote_empty_does_not_trigger_in_process`.
- **UNK-01:** returning `""` for an empty remote answer is the intended terminal policy, per
  ADR-010 INV-03, `pipeline_service.py`, `pipeline.py`, and the CI-blocking test. Not blocking.
- **UNK-02:** how two-stage fetch callers (e.g. REPLAgent) treat a `""` augment result is out of
  scope for this docstring-alignment issue; the terminal-empty contract is already locked.

## Compatibility considerations

Docstring-only change; zero runtime effect. The empty-remote contract is unchanged and remains
locked by the existing CI-blocking test. No `docs/*.md` change.

## Security considerations

N/A: documentation alignment only; no security-relevant behavior change. The auth fail-closed
behavior (`None` / `auth_error` bullet) is untouched.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/rag/http_augment.py` | Static: docstring-only change, no runtime effect | `uv run ruff check scripts/rag/http_augment.py`, `uv run mypy scripts/rag/http_augment.py` | Clean (no new lint/type findings) |
| `tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process` | Existing regression locking the empty-remote contract | `uv run pytest tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process` | Passes (behavior unchanged) |

## Completion criteria

- The `HttpAugment.run` docstring no longer claims that `""` triggers in-process fallback (AC1).
- The three docstrings (`http_augment.py`, `pipeline_service.py`, `pipeline.py`) agree on the
  empty-result contract being terminal (AC2).
- No runtime behavior changes; `test_remote_empty_does_not_trigger_in_process` still passes
  (AC3).

## Out of scope

Any change to runtime behavior, the `augment()` try/finally control flow, or the
`call_rag_service` empty/transient classification; the `None`-means-fallback contract, auth
fail-closed behavior, the `None`/`in_process_fallback` and `None`/`auth_error` bullets;
`pipeline_service.py` or `pipeline.py` docstrings; `docs/*.md`; or any test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read reference files to confirm terminal-empty contract | Pending | — | — | REQ-001 |
| 2 | Rewrite `HttpAugment.run` docstring `""` bullet in `scripts/rag/http_augment.py` | Pending | — | — | REQ-001 |
| 3 | Run ruff/mypy and affected tests to confirm no regression | Pending | — | — | REQ-002; AC3 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: issues/20261018-193523_rag002_rag-augment-treats-an-empty-remote-result-as-terminal-which-contradicts-the-httpaugment-docstring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-224545_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-075047
- **Related target files**: scripts/rag/http_augment.py
