## Goal
- Document non-monotonic offset advancement behavior in ack endpoint docs and add test for older-seq ack.

## Scope
- `docs/06_eventbus_02_http_api_and_runtime.md`: add monotonic offset note to ack section
- `tests/test_eventbus_ack_endpoint.py`: add older-seq ack test

## Findings

### Code verification
`scripts/eventbus/app.py:L418-L425` (canonical ack handler):
```python
if consumer_id and newly_acked:
    row = db.execute(
        "SELECT seq FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row:
        seq = int(row["seq"])
        write_offset(cfg.offsets_dir, consumer_id, seq)
```
- No monotonic guard — `write_offset` writes raw seq value ✓

`scripts/eventbus/offsets.py:L32-L38` (write_offset):
```python
def write_offset(offsets_dir: str, consumer_id: str, seq: int) -> None:
    safe_id = _sanitize_consumer_id(consumer_id)
    dir_path = Path(offsets_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / safe_id
    path.write_text(str(seq))
```
- No monotonic check — overwrites with raw seq ✓

### Docs verification
`docs/06_eventbus_02_http_api_and_runtime.md:L99-L120`:
- Canonical ack endpoint is well-documented ✓
- Missing monotonic offset note ✗
- Missing consumer_id optional behavior (offset not written without consumer_id) — already documented at L114 ✓

`docs/06_eventbus_06_reference_api.md:L83`:
- Canonical ack listed in reference API ✓

### "missing consumer_id" error handling
- No 400 error for missing consumer_id — code treats it as valid (ack without offset write) ✓

## Conclusion
Need to:
1. Add monotonic offset note to ack docs at `docs/06_eventbus_02_http_api_and_runtime.md:L114`
2. Add older-seq ack test to `tests/test_eventbus_ack_endpoint.py`
