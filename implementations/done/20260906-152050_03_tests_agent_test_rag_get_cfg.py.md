## Goal
Rewrite `TestRagPipelineGetCfg.test_get_cfg_error_path` (REQ-004) so it exercises
`resolve_rag_config`'s injectable `config_loader` fallback path instead of directly
patching the now-to-be-removed `_ModuleConfig.get()`.

## Scope
- In scope: `TestRagPipelineGetCfg.test_get_cfg_error_path` only (lines 53-62).
- Out of scope: every other test in this file (`TestRagLlmExceptions`,
  `TestAgentConfigGetCfg`, `TestDeleteModelsGetCfg`, the removal-guard tests) —
  unrelated to `_ModuleConfig`/`resolve_rag_config`, confirmed unaffected by this row.

## Assumptions
- Confirmed via direct read (2026-09-06) that this test currently reads (lines 54-62):
  ```python
  def test_get_cfg_error_path(self, monkeypatch) -> None:
      """_ModuleConfig.get() returns {} when ConfigLoader raises."""
      import rag.pipeline as pipeline_mod

      monkeypatch.setattr(pipeline_mod._ModuleConfig, "_cache", None)
      with patch.object(ConfigLoader, "load_all", side_effect=ValueError("no file")):
          result = pipeline_mod._ModuleConfig.get()
      assert result == {}
      monkeypatch.setattr(pipeline_mod._ModuleConfig, "_cache", None)
  ```
  This matches the Plan's citation closely (Plan cites "lines 56-65"; actual block is
  lines 54-62 — a minor line-number drift, not a content discrepancy; no Plan
  correction needed since the described behavior is accurate).
- This is the one test (per the Plan's own Design section) that meaningfully exercises
  the `ConfigLoader`-failure fallback at runtime (the other 3 target test files'
  patches are confirmed inert/defensive there).
- `resolve_rag_config` (REQ-001, implemented in `scripts/rag/pipeline.py` by a prior
  row in this same Plan) accepts a `config_loader` keyword parameter; this row assumes
  that function exists by the time this test runs — sequencing dependency on REQ-001's
  own implementation, not a blocker for writing this procedure document.

## Design decisions
- Replace the `_ModuleConfig`-specific patch/call with a direct call to
  `resolve_rag_config(cfg=None, config_loader=failing_loader)`, where
  `failing_loader` is a zero-arg callable raising `ValueError("no file")` — mirrors
  the current test's use of `patch.object(ConfigLoader, "load_all", side_effect=...)`
  but injects the failure via the new parameter instead of monkeypatching a removed
  class attribute.
- Keep the `assert result == {}`-equivalent assertion, adapted to whatever
  `resolve_rag_config` returns for this path (per REQ-001, defaulting/validating a
  `RagConfigImpl` from an empty dict) — assert on the same underlying behavior
  (ConfigLoader failure treated as empty config, not a raised exception), not on the
  literal `{}` return type change.
- Remove the two `monkeypatch.setattr(pipeline_mod._ModuleConfig, "_cache", None)`
  lines (before/after) — no longer applicable once `_ModuleConfig` is removed.

## Alternatives considered
- Keep patching `ConfigLoader.load_all` directly and call `resolve_rag_config` with no
  `config_loader` override (letting it fall through to the default
  `ConfigLoader().load_all()`): rejected — less explicit than passing a
  `config_loader` callable directly, and duplicates coverage of the default-path
  behavior already covered elsewhere; the Plan's Design section specifies rewriting
  to target `resolve_rag_config`'s `config_loader` fallback specifically.

## Implementation
### Target file
`tests/agent/test_rag_get_cfg.py`

### Procedure
1. Confirm `resolve_rag_config` (REQ-001) has landed in `scripts/rag/pipeline.py`
   before implementing this row.
2. Replace `test_get_cfg_error_path`'s body: remove both
   `monkeypatch.setattr(pipeline_mod._ModuleConfig, "_cache", None)` lines and the
   `pipeline_mod._ModuleConfig.get()` call.
3. Define a local failing `config_loader` callable
   (`lambda: (_ for _ in ()).throw(ValueError("no file"))` or a small nested function)
   and call `pipeline_mod.resolve_rag_config(None, config_loader=failing_loader)`.
4. Assert the result matches the expected `{}`-then-defaults behavior (e.g. a
   `RagConfigImpl` populated entirely from the 14 hardcoded defaults, per REQ-001's
   preserved defaulting logic) rather than the raw `{}` dict the old test asserted.
5. Update the docstring to describe the new behavior under test (e.g.
   "`resolve_rag_config` falls back to empty config when `config_loader` raises").

### Method
Confirmed via direct read of `tests/agent/test_rag_get_cfg.py` lines 1-62 (imports,
`_RAG_CFG_BASE` fixture, and the target test) that no other test in this file
references `_ModuleConfig`, and that `TestDeleteModelsGetCfg.test_get_cfg_error_path`
(line 142, a same-named test in a different class, unrelated `FileDeleteConfig`
subject) is out of scope and unaffected.

### Details
No change to any other test in this file.

## Compatibility considerations
This test's rewritten assertion only affects this one test method; no other test in
this file references `_ModuleConfig` or `resolve_rag_config`.

## Security considerations
N/A: test-only change, no security-relevant logic.

## Rollback considerations
Revert via `git checkout` on this file alone if the rewritten test fails after
`resolve_rag_config` lands with a different actual defaulting shape than assumed here.

## Validation plan
- `uv run pytest tests/agent/test_rag_get_cfg.py -v` — full file, confirm no
  regression to the other tests in this module.
- `uv run pytest tests/agent/test_rag_get_cfg.py::TestRagPipelineGetCfg::test_get_cfg_error_path -v` —
  targeted pass on the rewritten test.

## Completion criteria
- `test_get_cfg_error_path` no longer references `_ModuleConfig` in any form.
- The test calls `resolve_rag_config` with a failing `config_loader` and asserts the
  equivalent empty-then-defaults behavior.
- `uv run pytest tests/agent/test_rag_get_cfg.py -v` passes in full.

## Out of scope
- `scripts/rag/pipeline.py`'s `resolve_rag_config` implementation itself — tracked as
  this Plan's row 1 (seq 01).
- Every other test in this file.

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
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260905-192946_refactor_ragpipeline_responsibility_boundaries.md
- **Source plan**: plans/20260906-115512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-152050
- **Related target files**: tests/agent/test_rag_get_cfg.py
