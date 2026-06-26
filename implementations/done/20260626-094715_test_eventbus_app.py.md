# Implementation: Add pagination tests to test_eventbus_app.py

Steps covered: Plan 20260626-094715 — Step 3-1

---

## Goal

Add integration tests for paginated `/replay` and `/dlq` endpoints.

---

## Scope

- **In scope**: `tests/test_eventbus_app.py` — add pagination tests
- **Out of scope**: production code changes (must be completed first)

---

## Implementation

### Target file
`tests/test_eventbus_app.py`

### Procedure
1. Read existing test patterns (async client setup, db fixture).
2. Add `test_replay_pagination`:
   ```python
   async def test_replay_pagination(client, seeded_events):
       # seed 20 events in stream "s1"
       r1 = await client.get("/replay?stream=s1&limit=10&offset=0")
       assert r1.status_code == 200
       data = r1.json()
       assert data["total"] == 20
       assert data["limit"] == 10
       assert data["offset"] == 0
       assert len(data["items"]) == 10
       
       r2 = await client.get("/replay?stream=s1&limit=10&offset=10")
       assert len(r2.json()["items"]) == 10
       # items are distinct
       ids1 = {e["id"] for e in r1.json()["items"]}
       ids2 = {e["id"] for e in r2.json()["items"]}
       assert ids1.isdisjoint(ids2)
   ```
3. Add `test_dlq_pagination` similarly.
4. Add boundary test: `limit=1000` (max) accepted; `limit=1001` → 422 validation error.

---

## Validation plan

- Run: `uv run pytest tests/test_eventbus_app.py -x -v` — all new tests pass.
- Run: `uv run pytest tests/ -x` — no regressions.
