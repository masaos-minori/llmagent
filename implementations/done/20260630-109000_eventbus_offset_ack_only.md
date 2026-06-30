## Goal
- Move "Offset Advancement Is Ack-Only" item from Docs-Only to Resolved — code and docs already aligned.

## Scope
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md`: move offset item to Resolved section

## Findings

### Code verification
`scripts/eventbus/app.py:L326-L333` (subscribe disconnect handler):
```python
except asyncio.CancelledError:
    logger.info("subscribe disconnected consumer=%s seq=%d", ...)
finally:
    broker.unsubscribe(sub)
```
- Only `broker.unsubscribe(sub)` — no offset write on disconnect ✓

`scripts/eventbus/app.py:L409-L425` (ack handler):
- `write_offset(cfg.offsets_dir, consumer_id, seq)` only called in `_ack_and_offset()` during `/events/{event_id}/ack` endpoint
- Offsets only advance via explicit ack ✓

### Docs verification
`docs/06_eventbus_02_http_api_and_runtime.md:L95`:
- "On disconnect, no offset is written" — correct ✓

`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md:L38`:
- "Offsets advance only when the consumer explicitly acknowledges" — correct ✓

### "disconnect 時に offset 書き込み" check
- No matches for "disconnect.*offset" or "offset.*disconnect" in eventbus docs (except the correct L95 description) ✓

### Test coverage
`tests/test_eventbus_crash_ack.py:L38-L48`:
- `test_unacked_event_replayed_on_reconnect` — verifies disconnect without ack → offset not written → replay on reconnect ✓

## Conclusion
Only change needed: move "Offset Advancement Is Ack-Only" from Docs-Only Items to Resolved section.
