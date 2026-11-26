## Goal

Add URL query/fragment stripping and path redaction to the common secret masker so every
consumer can redact URL and path forms before truncation (REQ-001 — one redaction model).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- URL userinfo masking already exists in `SECRET_PATTERNS` (lines 39-43); only query/fragment
  stripping and path redaction are new. The Plan's earlier "keyed secrets only" claim was
  corrected in Step 3a.
- The change is additive: the 10 existing `_mask_secrets` consumers keep their behavior.

## Design decisions

- Helpers stay in `scripts/agent/secrets_masker.py` (Plan D1); no second redaction boundary.
- `redact_url` (new) and `redact_path` (new) are separate functions rather than a rewrite of
  `_mask_secrets`, so existing consumer output is unchanged.

## Alternatives considered

- New `agent/redaction.py` module — rejected by Plan D1 (would split the redaction model).

## Implementation
### Target file
`scripts/agent/secrets_masker.py`
### Procedure
- Add `redact_url` (new): strip userinfo, query, and fragment from a URL, keeping scheme, host,
  and path.
- Add `redact_path` (new): return a logical identifier for a filesystem path (basename or
  root-relative id), never the absolute path.
- Keep `SECRET_PATTERNS` and `_mask_secrets` unchanged.
### Method
- `redact_url` (new) parses the URL with `urllib.parse.urlsplit` and rebuilds it without
  `netloc` credentials, `query`, or `fragment`; falls back to the existing userinfo pattern when
  the value is not a parseable URL.
- `redact_path` (new) returns `Path(path).name` for the basename form and a root-relative id when
  the path is under a known root; it does not call `_mask_secrets`.
### Details
- Both helpers must be callable before truncation at consumer call sites; truncation stays in the
  consumers, so the helpers never truncate themselves.
- `detects_secrets` is not extended: it reports masking, not URL/path redaction.

### Companion test files
- `tests/agent/test_secrets_masker.py`
  - Procedure: add redaction-leak cases for URL userinfo/query/fragment and absolute-path forms,
    plus a redact-before-truncate case.
  - Validation: `uv run pytest tests/agent/test_secrets_masker.py`.

## Compatibility considerations

- Additive functions only; no existing call site changes in this document.

## Security considerations

- The helpers are the disclosure-control primitive for REQ-001; they must never return the
  original value for a credential-bearing URL or an absolute path.

## Rollback considerations

- N/A: revert the commit (additive helpers, no consumer change).

## Validation plan

- Unit: URL and path redaction, redact-before-truncate ordering —
  `uv run pytest tests/agent/test_secrets_masker.py`.
- Sequence: format → lint → type → arch → security (`uv run ruff format`, `uv run ruff check`,
  `uv run mypy`, `uv run lint-imports`, `uv run bandit`).

## Completion criteria

- URL query/fragment and absolute-path inputs are redacted by the new helpers; existing masker
  tests still pass unchanged.

## Out of Scope

- Changing `_mask_secrets` behavior for current consumers (Plan Out-of-Scope).
- Consumer call-site changes, covered by the other procedure documents of this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `tests/agent/test_secrets_masker.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (common redaction model with URL and path forms)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/secrets_masker.py`, `tests/agent/test_secrets_masker.py`
