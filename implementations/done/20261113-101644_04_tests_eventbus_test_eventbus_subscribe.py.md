## Goal
- Make `test_multi_batch_replay_no_duplicates` finish in about 2 s or less instead of about 17 s by publishing far fewer events, while still asserting that every event is replayed exactly once across several pages (`REQ-005`; `REQ-001`: record that the cost is publish volume).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one test body of `test_multi_batch_replay_no_duplicates`.
- Not in scope: fixtures, other eventbus tests, `scripts/eventbus/`.

## Assumptions
- The cost is publish throughput: the test publishes `cfg.replay_batch_size + 5` events (default 1000, so 1005 posts through the HTTP client and SQLite). It does not wait on a clock. Falsifier: after the change it still takes seconds.
- `/replay` pages by its `limit` and `offset` query parameters; `replay_batch_size` is read only by `scripts/eventbus/subscribe_route.py`. So lowering it only reduces the publish count here, and the page size must be lowered too for the test to still read more than one page.
- The test's `cfg` is `eb_app.app.state.config`, which is the fixture's config object, so it can be adjusted with `object.__setattr__` like other eventbus tests do.

## Design decisions
- Lower `replay_batch_size` through the config (keeping the link between event count and batch size) and read events in pages of 10.
- Keep the final assertion `len(event_ids) == len(bodies)`.

## Alternatives considered
N/A: a literal event count would drop the link to the config; the config route is the Issue's stated mechanism.

## Implementation
### Target file
`tests/eventbus/test_eventbus_subscribe.py`

### Procedure
1. Measure first: `uv run pytest tests/eventbus/test_eventbus_subscribe.py::test_multi_batch_replay_no_duplicates --durations=3 -o addopts=""`.
2. In `test_multi_batch_replay_no_duplicates`, after `cfg = eb_app.app.state.config` and its `assert cfg is not None`, set `replay_batch_size` to 20 with `object.__setattr__(cfg, "replay_batch_size", 20)`; `batch_size` then gives 20 and `bodies` 25 events.
3. Introduce a local `page_size` (new) of 10 and use it in place of the literal 100 in the `/replay` query (`limit=`), in the `len(items) < ...` stop check, and in `offset += ...`.
4. Re-run the command and note the duration.

### Method
The existing loop pages `/replay?since_seq=0&format=json&limit=...&offset=...` until an empty or short page and collects `item["seq"]`; only the numeric page size changes, so the loop reads three pages for 25 events.

### Details
- Keep the `_pub_client(operator_client)` publishing and the `assert resp.status_code == 200` checks.
- Add a short comment that the count stays above one page so the pagination path is exercised.
- Do not edit the `operator_client` fixture.

## Compatibility considerations
N/A: test-only change; no production source or default changes.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_subscribe.py -o addopts=""` serially, then with `-n auto`, repeated a few times.
- `uv run ruff check tests/eventbus/test_eventbus_subscribe.py` and `uv run mypy --no-namespace-packages tests/eventbus`.

## Completion criteria
- The test finishes in about 2 s or less and still asserts exactly-once replay across more than one page (`AC-005`).
- No file outside the test file changed.

## Out of Scope
- Other eventbus tests (`UNK-01` of the Plan handles a slow one in an existing target file only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-111526 | 20261113-112606 | Changed tests/eventbus/test_eventbus_subscribe.py (test_multi_batch_replay_no_duplicates: replay_batch_size set to 20 through the config, page_size of 10 replaces the literal 100 in the /replay query, stop check, and offset step). Cost was publish volume (1005 posts), measured 5.71 s alone; now 0.32 s. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-112606 | 20261113-112606 | File: 25 passed serially and twice with -n auto; the exactly-once assertion over 3 pages is unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-112606 | 20261113-112606 | ruff clean; mypy on tests/eventbus clean (38 files). Full suite serial 12159 passed, 3 failed: the known mdq cases (unrelated, Plan testspeed004). diff-cover N/A: no source file changed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-112606 | 20261113-112606 | N/A: no docs/00_index.md task-scope mapping for tests/eventbus/test_eventbus_subscribe.py |

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
- **Requirement ID**: REQ-001 (record the cause), REQ-005 (cut the publish volume)
- **Source issue**: issues/20261112-183849_testspeed003_cut-timeout-test-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-092136_testspeed003_cut-timeout-test-waits.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101644
- **Related target files**: `tests/eventbus/test_eventbus_subscribe.py`
