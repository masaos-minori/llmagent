## Goal

Add two bearer-header secret shapes to `SECRET_PATTERNS` in `scripts/agent/secrets_masker.py` so that `_mask_secrets()` masks `Authorization: <scheme> <token>` headers (REQ-002, REQ-003) and standalone `Bearer <token>` tokens (REQ-004), while leaving the three existing `key=value` patterns byte-for-byte unchanged (REQ-001).

## Scope

**In:**
- Append exactly two `re.compile(...)` entries to the `SECRET_PATTERNS` list in `scripts/agent/secrets_masker.py`.
- Preserve the existing `(?i)` flag and the `group(1) + "***MASKED***"` replacement convention used by `_mask_secrets()`.

**Out:**
- No change to the three existing `key=value` patterns (their source must be identical before and after).
- No change to `_mask_secrets()` itself — the existing `for pattern in SECRET_PATTERNS` loop already iterates any appended patterns.
- No change to call sites (`http_lifecycle.py:420`, `startup_mcp_starter.py:100`) or the shared redaction registry (`scripts/shared/logger.py`).
- No masking of JSON `"key": "value"` or bare hex/base64 tokens (recorded out-of-scope in the Plan).
- Test authoring — owned by the paired doc `20261014-101041_02_tests_agent_test_secrets_masker.py.md`.
- Documentation — owned by the paired doc `20261014-101041_03_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md`.

## Assumptions

1. `_mask_secrets()` remains a pure string→string function applied to opaque subprocess output; appending patterns does not alter its signature or contract.
2. The `***MASKED***` sentinel is retained so the existing regression assertions (`"MASKED" in result`) continue to hold.
3. Both call sites pass opaque strings, so pattern extension (not the shared registry) is the correct resolution path — see the Plan's Implementation intent.
4. Standalone `Bearer <token>` matching is acceptable because bearer tokens are inherently sensitive; the `Bearer\s+` scheme token requirement avoids matching ordinary prose.

## Design decisions

- Append two patterns to `SECRET_PATTERNS`, keeping the list-based iteration in `_mask_secrets()` untouched:
  ```python
  SECRET_PATTERNS: list[re.Pattern[str]] = [
      re.compile(r"(?i)((?:password|passwd|pwd)\s*=\s*)(\S+)"),
      re.compile(r"(?i)((?:api[_-]?key|apikey)\s*=\s*)(\S+)"),
      re.compile(r"(?i)((?:secret|token)\s*=\s*)(\S+)"),
      re.compile(r"(?i)(Authorization:\s*\S+\s+)(\S+)"),   # NEW: Authorization: <scheme> <token>
      re.compile(r"(?i)(Bearer\s+)(\S+)"),                 # NEW: standalone Bearer <token>
  ]
  ```
- Each new pattern captures the preserved prefix in `group(1)` (the keyword/scheme token) and the maskable value in `group(2)`, so the replacement `m.group(1) + "***MASKED***"` keeps the `Authorization:`/`Bearer` keyword and replaces only the token.
- Both patterns use only non-nested `\S+`/`\s+` quantifiers separated by hard delimiters (`:`, whitespace), so there is no catastrophic-backtracking risk on adversarial log input.

## Alternatives considered

- **`Authorization:`-anchored only (drop standalone `Bearer`)**: Would miss bearer tokens appearing without an `Authorization:` prefix (e.g. inline in a URL or body). Rejected — REQ-004 requires the standalone shape.
- **Reuse the shared log-redaction registry (`scripts/shared/logger.py`)**: The registry redacts pre-known values via a `logging.Filter` and would require extracting the value before masking, incompatible with the pure string→string contract and risking call-site behavior change. Rejected — see the Plan's Design section.
- **Require a token charset (alphanumeric/hex) instead of `\S+`**: Tighter, but would under-mask tokens containing `-`, `_`, `.`, or `=` (e.g. JWTs, base64url). `\S+` matches the existing `key=value` patterns' value class and avoids partial masking. Rejected in favor of `\S+`.

## Implementation

### Target file

`scripts/agent/secrets_masker.py`

### Procedure

Append the two bearer-header patterns to the end of the `SECRET_PATTERNS` list, after the three existing `key=value` patterns. Do not touch the existing three entries or `_mask_secrets()`.

### Method

Keep the existing list literal and its `(?i)` flag; add two `re.compile(...)` entries. The existing loop `for pattern in SECRET_PATTERNS: masked = pattern.sub(lambda m: m.group(1) + "***MASKED***", masked)` automatically applies the new patterns — no change to `_mask_secrets()` is required.

### Details

Before:
```python
SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)((?:password|passwd|pwd)\s*=\s*)(\S+)"),
    re.compile(r"(?i)((?:api[_-]?key|apikey)\s*=\s*)(\S+)"),
    re.compile(r"(?i)((?:secret|token)\s*=\s*)(\S+)"),
]
```

After:
```python
SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)((?:password|passwd|pwd)\s*=\s*)(\S+)"),
    re.compile(r"(?i)((?:api[_-]?key|apikey)\s*=\s*)(\S+)"),
    re.compile(r"(?i)((?:secret|token)\s*=\s*)(\S+)"),
    re.compile(r"(?i)(Authorization:\s*\S+\s+)(\S+)"),
    re.compile(r"(?i)(Bearer\s+)(\S+)"),
]
```

Behavior after the change:
- `Authorization: Bearer <token>` → `Authorization: Bearer ***MASKED***` (REQ-002).
- `Authorization: Basic/Digest/<scheme> <token>` → `<scheme>` keyword preserved, token masked (REQ-003).
- Standalone `Bearer <token>` (no `Authorization:` prefix) → `Bearer ***MASKED***` (REQ-004).
- Existing `key=value` forms → unchanged (REQ-001).
- Text without secrets / empty string / arbitrary text → unchanged / empty / never raises (REQ-005).

Sequential application is safe even if one pattern's output feeds the other: the token is always replaced by `***MASKED***` (a `\S+`), so neither pattern can re-expose a real token. E.g. `Authorization: Bearer abc123` → pattern 1 yields `Authorization: Bearer ***MASKED***`; pattern 2 then sees `Bearer ***MASKED***` and reproduces `Bearer ***MASKED***` (keyword kept in `group(1)`), so the final result is `Authorization: Bearer ***MASKED***`.

## Compatibility considerations

- No public-API change: `_mask_secrets()` signature, return contract, and the `***MASKED***` sentinel are unchanged.
- Output gains two additional masked shapes; callers that parse masked output by splitting on `=` are unaffected (bearer shapes have no `=`).
- The three existing `key=value` results are byte-for-byte identical, so all existing regression cases (including the secmask001 short-value cases) keep passing.
- `retry_helper._mask_secrets` delegates to this helper; its callers inherit the expanded recognition transitively.

## Security considerations

- This is a security-positive change: it closes the shape-recognition gap tracked by ledger entry `AGENT-006` — previously an `Authorization: Bearer ...` header or a bare bearer token was logged in clear text.
- Over-masking trade-off (documented as in-scope, not a defect): the standalone `Bearer\s+\S+` pattern will also match a benign occurrence of the word "Bearer" followed by a token-like word (e.g. "Bearer me later"). Mitigated by requiring the `Bearer` scheme token plus a following value; ordinary prose without "Bearer" is not matched. Acceptable per the confirmed scope.
- No new dependencies, network calls, or external surface introduced.

## Rollback considerations

- Additive only: removing the two appended lines restores the original three-pattern behavior exactly. The rollback is deleting two list entries (one logical commit).
- Because the change is additive, it cannot regress the secmask001 value-leak fix — the three `key=value` patterns and the replacement expression are untouched.

## Validation plan

- Run the validation sequence on `scripts/agent/secrets_masker.py`: `uv run ruff check scripts/agent/secrets_masker.py`, `uv run mypy scripts/agent/secrets_masker.py`, `uv run bandit -q -r scripts/agent/secrets_masker.py`.
- Run the paired test module after it is updated: `uv run pytest tests/agent/test_secrets_masker.py -v`.
- Confirm the existing `key=value` regression cases still assert identically (REQ-001).

## Completion criteria

- `SECRET_PATTERNS` contains exactly five patterns: the three original `key=value` patterns unchanged plus the two new bearer patterns.
- `_mask_secrets("Authorization: Bearer <token>")` returns the token masked (REQ-002); a generic scheme header is masked (REQ-003); a standalone `Bearer <token>` is masked (REQ-004).
- Existing `key=value` outputs are unchanged (REQ-001); empty string returns empty; arbitrary text never raises (REQ-005).
- `ruff`, `mypy`, `bandit` clean on `scripts/agent/secrets_masker.py`; paired tests pass.

## Out of scope

- Modifying the three existing `key=value` patterns or `_mask_secrets()`.
- Adding patterns for JSON `"key": "value"` or bare hex/base64 tokens (out-of-scope by Plan decision).
- Call-site or registry changes.
- Test and documentation updates — covered by the paired docs.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-002, REQ-003, REQ-004 |
| 2 | Add or update tests per Validation plan | N/A | — | — | Tests owned by paired doc `20261014-101041_02_tests_agent_test_secrets_masker.py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `ruff`, `mypy`, `bandit` | Pending | — | — | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Doc update owned by paired doc `20261014-101041_03_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md` |

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
- **Requirement ID**: `REQ-002` — `Authorization: Bearer <token>` masked; `REQ-003` — generic `Authorization: <scheme> <token>` masked; `REQ-004` — standalone `Bearer <token>` masked
- **Source issue**: issues/20261013-162325_agmask01_mask-alternate-secret-shapes-in-the-agent-secret-masker.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-093347_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-101041
- **Related target files**: scripts/agent/secrets_masker.py
