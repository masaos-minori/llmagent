## Goal

Clarify 0-vs-missing semantics for `browser_*` config fields in `web_search_models.py` — decide whether explicit `0` values should be honored as overrides or silently mapped to defaults.

## Scope

- **In-Scope**:
  - Phase 1: Investigate downstream behavior of `browser_max_response_kb=0`/`browser_timeout_sec=0` in `search_provider.py`
  - Phase 2: Decide Option A (honor `0`) or Option B (leave as-is) based on investigation findings
- **Out-of-Scope**:
  - Changes outside `scripts/mcp_servers/web_search/`
  - Modifying other `or default` patterns in `WebSearchConfig.from_dict` beyond the two affected fields

## Assumptions

- `0` is falsy in Python, so `d.get(key) or default` treats `0` the same as `None`
- The current behavior silently replaces `0` with the default value (e.g., 256 for `browser_max_response_kb`)
- Whether `0` is a meaningful override depends on downstream consumption in `search_provider.py`

## Design decisions

- If Option A (honor `0`), use `is not None` check instead of truthiness for the two browser fields
- If Option B (leave as-is), add a comment explaining why `0` maps to default

## Alternatives considered

- Honor `0` for all integer fields — rejected because scope limits to `browser_*` fields only
- Leave as-is — acceptable if downstream doesn't need `0` as a valid value

## Compatibility considerations

- Option A: Behavioral change for configs passing `browser_max_response_kb: 0` or `browser_timeout_sec: 0`
- Option B: No behavioral change

## Security considerations

- N/A — no security-relevant behavior change

## Rollback considerations

- Revert the diff; no data loss or service impact

## Implementation

### Target files

- `scripts/mcp_servers/web_search/web_search_models.py`
- Potentially: `scripts/mcp_servers/web_search/search_provider.py` (investigation only)

### Procedure

1. **Phase 1: Preparation / Investigation**
   - Read `scripts/mcp_servers/web_search/search_provider.py` to understand how `browser_max_response_kb=0`/`browser_timeout_sec=0` would behave downstream
   - Determine whether `timeout_sec=0` means "no timeout" or "instant timeout"
   - Scan all `or default` patterns in `WebSearchConfig.from_dict` to identify any other affected fields

2. **Phase 2: Core Logic Implementation**
   
   **If Option A (honor `0` recommended):**
   - Change `int(d.get(key) or default)` to `int(d.get(key)) if d.get(key) is not None else default` for the affected fields only
   - Add a characterization test asserting `browser_max_response_kb: 0` in the source dict produces `0` in the resulting config
   
   **If Option B (leave as-is):**
   - Add a comment above the relevant lines explaining why `0` is intentionally mapped to the default

3. **Phase 3: Deployment & Verification**
   - Run `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py -v` — verify existing tests pass
   - If Option A: verify new characterization test passes

### Method

Semantic clarification — distinguish between missing (`None`) and explicitly-zero (`0`) values in config parsing.

### Details

```python
# In scripts/mcp_servers/web_search/web_search_models.py, Option A (honor 0):

# BEFORE:
class WebSearchConfig(BaseModel):
    browser_max_response_kb: int = Field(default=256)
    browser_timeout_sec: int = Field(default=30)
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            browser_max_response_kb=int(d.get("browser_max_response_kb") or 256),
            browser_timeout_sec=int(d.get("browser_timeout_sec") or 30),
            ...
        )

# AFTER:
class WebSearchConfig(BaseModel):
    browser_max_response_kb: int = Field(default=256)
    browser_timeout_sec: int = Field(default=30)
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            browser_max_response_kb=(
                int(d["browser_max_response_kb"]) if d.get("browser_max_response_kb") is not None else 256
            ),
            browser_timeout_sec=(
                int(d["browser_timeout_sec"]) if d.get("browser_timeout_sec") is not None else 30
            ),
            ...
        )

# In scripts/mcp_servers/web_search/web_search_models.py, Option B (leave as-is):

# Add comment above the relevant lines:
# Note: browser_max_response_kb=0 and browser_timeout_sec=0 are treated as missing
# and fall back to defaults. This is intentional — 0 has no semantic meaning
# in these fields for the search provider.
```

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/web_search/test_web_search_models.py` | Regression + new characterization test | `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py -v` | All pass |

## Out of scope

- Runtime behavior changes (pure type annotation change)
- Changes outside `scripts/mcp_servers/web_search/`

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260817-150916_require.md
- Source plan: plans/20260817-163214_plan.md
- Source implementation procedure: N/A
- Generated at: 20260817-184918
- Related target files: scripts/mcp_servers/web_search/web_search_models.py
