# Implementation: Update `docs/05_agent_04_state-and-persistence.md`

## Goal

Update the diagnostic storage description in the state-and-persistence doc to reflect the new `DiagnosticStore` + `session_diagnostics` table design.

## Scope

- `docs/05_agent_04_state-and-persistence.md` — update diagnostic section

**Out of scope:** Other sections of the doc.

## Assumptions

1. The doc has an existing section about diagnostic storage that needs updating.

## Implementation

### Target file

`docs/05_agent_04_state-and-persistence.md`

### Procedure

1. Read the existing diagnostic storage section.
2. Replace/update it to describe the new model: diagnostic data lives in `session_diagnostics` table via `DiagnosticStore`, no longer mixed into `messages` table.

### Method

Edit the relevant section.

### Details

**Changes:**
- Replace description of `save_diagnostic()` → `SessionMessageRepository` path with the new `DiagnosticStore` → `session_diagnostics` path.
- Mention that `DiagnosticStore` has `save()`, `fetch()`, `fetch_all()` methods.
- Note that the `diagnostics.jsonl` file is still written by `repl.py` but may be deprecated in future.
- Note that `fetch_messages()` no longer filters out `diagnostic` role (because diagnostic data is no longer in `messages`).

## Validation Plan

| Check | Tool | Criterion |
|---|---|---|
| Doc review | Manual read | Description matches implementation |
| Pre-commit | `pre-commit run --all-files` | Pass (markdown lint) |
