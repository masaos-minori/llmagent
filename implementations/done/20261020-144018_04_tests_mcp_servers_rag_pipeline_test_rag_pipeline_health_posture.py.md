## Goal

Keep the posture tests deterministic and network-free once `/health` probes a configured
`embed_url`, and lock in that an unreachable embedding service does not affect startup
posture validation (REQ-003, AC-006).

## Scope

Modify `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` only:

- Stub the probe for every test in the module so `GET /health` reads a deterministic body
  without an outbound request.
- Add a case that startup succeeds with the embedding service unreachable while
  `server.embed_url_configured` still passes.

The probe module (seq 02) and the `_check_health_deps` change (seq 01) are separate target
files; this file only exercises them.

## Assumptions

- The shipped `config/rag_pipeline_mcp_server.toml:10` sets a configured `embed_url`
  (`http://192.168.11.238:8081`), copied into the test isolation root, so an un-stubbed
  probe would hit an unreachable address and add `{"embed_url": "unreachable"}` to
  `dependencies`.
- `_check_health_deps` imports the probe lazily (seq 01), so patching the attribute on the
  probe module is observed on each `/health` call.
- `test_health_returns_503_when_the_posture_is_not_validated` asserts
  `body["dependencies"] == {}` (lines 203-215) and is the existing test that breaks without
  the stub.

## Design decisions

- **One autouse stub for the module.** `_stub_embed_probe` (new) is an autouse fixture that
  replaces `probe_embed_reachable` on `mcp_servers.rag_pipeline.rag_pipeline_health_probe`
  with an async function returning `"reachable"`, so no posture test depends on the
  network or the probe cache.
- **Unreachable case overrides the stub inside the new test.** The new test sets the stub to
  return `"unreachable"` and asserts both the posture and the `/health` body, instead of
  adding a second fixture.

## Alternatives considered

N/A: stubbing at the module attribute is the single stub target defined by seq 01's lazy-import design.

## Implementation

### Target file

`tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py`

### Procedure

1. Add the autouse fixture `_stub_embed_probe` (new) that patches `probe_embed_reachable` to
   return `"reachable"`.
2. Add `TestEmbedOutageDoesNotBlockStartup` (new) with one test: with the probe returning
   `"unreachable"`, the posture is still validated, `server.embed_url_configured` is not a
   failed check, `_enforce_posture_gate()` does not exit, and `/health` still publishes
   `security.validated is True`. The `dependencies == {"embed_url": "unreachable"}` body is
   asserted by the seq 03 endpoint tests, so this document does not depend on seq 01 being
   applied first.

### Method

- Fixture shape (monkeypatch target is the probe module attribute, not a binding on
  `rag_pipeline_server`):

  ```python
  @pytest.fixture(autouse=True)
  def _stub_embed_probe(monkeypatch: pytest.MonkeyPatch) -> None:
      async def _reachable(embed_url: str, **_kwargs: object) -> str:
          return "reachable"

      monkeypatch.setattr(
          "mcp_servers.rag_pipeline.rag_pipeline_health_probe.probe_embed_reachable",
          _reachable,
      )
  ```

- The new test re-patches the same attribute with a function returning `"unreachable"`,
  calls `rag_pipeline_server._enforce_posture_gate()` (expects no `SystemExit`), reads
  `rag_pipeline_server._security_posture`, and reads the published `security` block with
  the existing `_security_block(client)` helper.

### Details

- `_failed_checks(posture)` already maps failed check ids to reason codes; assert
  `"server.embed_url_configured" not in _failed_checks(posture)`.
- Assert `_security_block(client)["validated"] is True`. Do not assert the HTTP status or
  `dependencies` here: they change when seq 01 lands and are covered by seq 03.
- No existing test is edited besides gaining the autouse stub.

## Compatibility considerations

N/A: test-only change; existing assertions are unchanged.

## Security considerations

N/A: the stub removes an outbound request from the posture tests; no credential is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py -v`
  collects the new test and passes, with no outbound request.
- `test_health_returns_503_when_the_posture_is_not_validated` still sees
  `dependencies == {}` once seq 01 is applied.
- Full suite passes; `ruff`, `mypy` (tests are covered by pre-commit's mypy run) pass.

## Completion criteria

- Every `/health` call in the module is network-free.
- Startup posture is validated with the embedding service unreachable, and
  `server.embed_url_configured` does not fail.

## Out of Scope

- The probe and `_check_health_deps` changes (seq 02, seq 01).
- Endpoint tests in `test_rag_pipeline_server_endpoints.py` (seq 03).
- Any change to the posture contract or `rag_pipeline_security.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the autouse probe stub fixture to the posture test module | Completed | 20261020-163600 | 20261020-163600 | REQ-003 changed: tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py; procedure regenerated from plan (user-approved) and decoupled from seq 01 |
| 2 | Add the embedding-unreachable startup case | Completed | 20261020-163600 | 20261020-163600 | REQ-003, AC-006 TestEmbedOutageDoesNotBlockStartup added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-163600 | 20261020-163600 | ruff, mypy, mock-patch, suppression pass; targeted 15 passed; full suite 9652 passed, 14 skipped |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261019-214637_ragobs003_rag_pipeline_health_misses_embed_outage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261020-132416_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-161847
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py