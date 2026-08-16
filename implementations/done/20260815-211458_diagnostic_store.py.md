# Implementation Procedure: Make sensitive field filtering configurable in DiagnosticStore

## Goal

Make the list of sensitive fields configurable via DiagnosticsConfig, ensuring sensitive field filtering keeps pace with the evolving set of diagnostic fields without requiring manual code changes.

## Scope

- `scripts/agent/config_dataclasses.py`: Add `sensitive_fields` field to DiagnosticsConfig
- `scripts/agent/diagnostic_store.py`: Load and merge configured sensitive fields in `_filter_sensitive_fields()`

## Assumptions

1. DiagnosticsConfig can accept a new field without breaking existing configurations
2. The hardcoded list `("artifacts", "rag_stage_outcomes")` should remain as default values
3. Merging configured fields with hardcoded list ensures backward compatibility

## Design decisions

- Add `sensitive_fields: frozenset[str]` to DiagnosticsConfig with default `frozenset(("artifacts", "rag_stage_outcomes"))`
- In `_filter_sensitive_fields()`, load DiagnosticsConfig and merge configured fields with hardcoded defaults (union operation)
- Configured fields augment, not replace, the hardcoded defaults — operators cannot remove default fields unless they explicitly override the entire set

## Alternatives considered

- Allowing operators to remove fields from the default list via a separate `remove_fields` config — rejected because it adds complexity and the risk of accidentally exposing sensitive data
- Making the entire list configurable (replace instead of merge) — rejected because it breaks backward compatibility for operators who don't specify the field

## Implementation

### Target file

`scripts/agent/diagnostic_store.py`

### Procedure

1. Read `scripts/agent/config_dataclasses.py` and identify the DiagnosticsConfig class (line 380)
2. Add a new field `sensitive_fields: frozenset[str] = frozenset(("artifacts", "rag_stage_outcomes"))` to DiagnosticsConfig
3. Read `scripts/agent/diagnostic_store.py` and identify the exact location of `_filter_sensitive_fields()` (line 61)
4. Modify `_filter_sensitive_fields()` to load DiagnosticsConfig via `_load_diagnostics_config()`
5. Merge configured sensitive fields with the hardcoded list (`_SENSITIVE_FIELDS`)
6. Apply filtering to all merged fields
7. Update the docstring of `_filter_sensitive_fields()` to reflect that the field list is now configurable
8. Update the module-level comment above `_SENSITIVE_FIELDS` to note that the list is augmented by DiagnosticsConfig
9. Run tests to ensure no regressions

### Method

Two-file change: add field to dataclass, modify filter logic in store.

### Details

**config_dataclasses.py:**
```python
@dataclass
class DiagnosticsConfig:
    """Diagnostic storage encryption and retention settings."""

    encryption_key: str = ""
    retention_days: int = 30
    sensitive_fields: frozenset[str] = frozenset(("artifacts", "rag_stage_outcomes"))
```

**diagnostic_store.py — _filter_sensitive_fields():**
```python
def _filter_sensitive_fields(self, content: str) -> str:
    """Redact sensitive fields from a JSON diagnostic payload.

    Replaces sensitive field list values with
    {"_redacted": True, "count": <len>} so downstream readers can tell
    "filtered" apart from "field never populated", without leaking the
    raw artifact URIs or RAG stage outcome contents. Content that is not
    valid JSON, or not a JSON object, is returned unchanged.

    The set of sensitive fields is loaded from DiagnosticsConfig and merged
    with the hardcoded defaults (_SENSITIVE_FIELDS).
    """
    try:
        payload = orjson.loads(content)
    except orjson.JSONDecodeError:
        return content
    if not isinstance(payload, dict):
        return content
    redacted = False
    # Merge configured fields with hardcoded defaults
    effective_fields = _SENSITIVE_FIELDS | frozenset(
        self._load_diagnostics_config().sensitive_fields
    )
    for field_name in effective_fields:
        value = payload.get(field_name)
        if isinstance(value, list):
            payload[field_name] = {"_redacted": True, "count": len(value)}
            redacted = True
    if not redacted:
        return content
    return dumps(payload)
```

## Compatibility considerations

- Existing configurations without `sensitive_fields` will use the hardcoded defaults (backward compatible)
- Operators specifying their own `sensitive_fields` will have those merged with defaults (union), not replacing them

## Security considerations

- `_SENSITIVE_PATTERNS` raises an exception when encryption is disabled — adding new patterns could affect error handling paths (documented in Risks section of plan)
- This change does not weaken security; it only extends the set of fields that can be filtered

## Rollback considerations

Reverting requires two steps: removing the `sensitive_fields` field from DiagnosticsConfig and restoring the original `_filter_sensitive_fields()` logic.

## Validation plan

- Unit test: `_filter_sensitive_fields()` with various field combinations including newly added sensitive fields
- Integration test: verifying diagnostic output during startup/shutdown shows filtered values
- Test: verifying that DiagnosticsConfig.sensitive_fields defaults to the original hardcoded list when not specified

## Out of scope

- Changes to `_SENSITIVE_PATTERNS` behavior (exception-on-unencrypted remains unchanged)
- Changes to the redaction format (`{"_redacted": True, "count": ...}`)
- Changes to any caller of `_filter_sensitive_fields()` beyond what is necessary for this semantic change

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260815-160626_require.md
- Source plan: plans/20260815-174220_plan.md
- Source implementation procedure: N/A
- Generated at: 20260815-211458
- Related target files: scripts/agent/diagnostic_store.py, scripts/agent/config_dataclasses.py
