## Goal
- Move `/health Degraded State Returns HTTP 503` item from Docs-Only to Resolved in eventbus inconsistencies docs — code and docs already aligned.

## Scope
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md`: move /health item to Resolved section

## Findings

### Code verification
`scripts/eventbus/app.py:L158-L159`:
```python
overall = "ok" if not degraded_reasons else "degraded"
status_code = 200 if overall == "ok" else 503
```
- Returns HTTP 200 for `ok`, HTTP 503 for `degraded` — correct ✓

### Docs verification
`docs/06_eventbus_02_http_api_and_runtime.md:L147`:
- "HTTP 200 for `ok`, HTTP 503 for `degraded`/`unhealthy`" — correct ✓

`docs/06_eventbus_05_configuration_deploy_and_operations.md:L94-L96`:
- "503 | `degraded`" table row — correct ✓

### "always HTTP 200" check
- No matches for "always.*HTTP" or "always.*200" in eventbus docs ✓

### Test coverage
- Plan item mentions checking `tests/test_eventbus_health.py` for 503 case coverage — not blocking since code/docs are already aligned

## Conclusion
Only change needed: move `/health Degraded State Returns HTTP 503` from Docs-Only Items to Resolved section in the inconsistencies doc.
