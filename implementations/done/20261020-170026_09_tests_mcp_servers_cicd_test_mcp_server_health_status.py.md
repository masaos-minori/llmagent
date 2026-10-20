## Goal

Keep the configured-and-reachable `rag-pipeline-mcp` `/health` case in the cicd health-status
tests network-free and asserting HTTP 200 once `/health` probes a configured `embed_url`
(REQ-003 — the unchanged response shape; AC-002 — reachable keeps the `200 ok` shape).

## Scope

Modify `tests/mcp_servers/cicd/test_mcp_server_health_status.py` only:

- Stub the probe in `TestRagPipelineServerHealth.test_ok_when_embed_url_configured`.

This file is an additional target file added to the plan by amendment 20261020 (discovered
when the full suite failed this test with `assert 503 == 200` after the `_check_health_deps`
change). The other cases in the class are unchanged.

## Assumptions

- The test patches `shared.config_loader.ConfigLoader.load` to return
  `{"embed_url": "http://localhost:11434/api/embeddings"}` (lines 268-269) and asserts
  200 with `ready`, `status == "ok"`, `liveness`, and the two flag fields.
- `_check_health_deps` imports the probe lazily (seq 01), so patching
  `probe_embed_reachable` on the probe module is observed on each `/health` call.
- `test_degraded_when_embed_url_not_configured` returns before any probe (absent key) and
  needs no stub.

## Design decisions

- **Stub inside the existing `with patch(...)` block.** Add a second `patch` of
  `mcp_servers.rag_pipeline.rag_pipeline_health_probe.probe_embed_reachable` with an async
  function returning `"reachable"`, keeping the file's existing `unittest.mock.patch` idiom
  and adding no import.
- **Assertions unchanged.** The 200 body assertions stay as they are: the test still locks
  the reachable-case response shape.

## Alternatives considered

N/A: a module-wide autouse stub would also hide the missing-key case from exercising the
no-probe path, so the stub is scoped to the one test that needs it.

## Implementation

### Target file

`tests/mcp_servers/cicd/test_mcp_server_health_status.py`

### Procedure

1. In `TestRagPipelineServerHealth.test_ok_when_embed_url_configured`, define an async stub
   returning `"reachable"` and patch it over `probe_embed_reachable` on the probe module for
   the duration of the request.
2. Leave every assertion as is.

### Method

- Shape:

  ```python
  async def _reachable(embed_url: str, **_kwargs: object) -> str:
      return "reachable"

  with (
      patch("shared.config_loader.ConfigLoader.load", return_value=cfg),
      patch(
          "mcp_servers.rag_pipeline.rag_pipeline_health_probe.probe_embed_reachable",
          new=_reachable,
      ),
  ):
      ...
  ```

### Details

- `tools/check_mock_patch_targets.py` flags a patch of an origin module only when the code
  under test imports the symbol at module level; seq 01 imports it inside a function, so
  patching the probe module attribute takes effect and is not flagged.

## Compatibility considerations

N/A: test-only change; the assertions are unchanged.

## Security considerations

N/A: the stub removes an outbound request from the test.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/cicd/test_mcp_server_health_status.py -v` passes, with
  `test_ok_when_embed_url_configured` collected and no outbound request.
- Full suite passes once seq 01 is applied.

## Completion criteria

- `test_ok_when_embed_url_configured` asserts 200 `ok` with the probe stubbed `"reachable"`.
- No other case in the file changes.

## Out of Scope

- The probe and `_check_health_deps` changes (seq 02, seq 01).
- A new unreachable-case test (seq 03 owns the endpoint cases).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Stub the probe in `test_ok_when_embed_url_configured` | Completed | 20261020-180905 | 20261020-180905 | REQ-003 changed: tests/mcp_servers/cicd/test_mcp_server_health_status.py; target added by plan amendment (user-approved) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-180905 | 20261020-180905 | ruff, mypy, mock-patch pass; targeted 13 passed; full suite 9652 passed, 14 skipped |

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
- **Generated at**: 20261020-170026
- **Related target files**: tests/mcp_servers/cicd/test_mcp_server_health_status.py