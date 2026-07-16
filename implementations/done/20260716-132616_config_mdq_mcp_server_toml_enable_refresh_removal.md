# Implementation: config/mdq_mcp_server.toml (remove `enable_refresh` key, add removal note)

Source plan: `plans/20260716-131759_plan.md`

Note: a third distinct change targeting this config file, alongside the
plan-04 and plan-05 docs
(`implementations/20260716-131850_config_mdq_mcp_server_toml.md`,
`implementations/20260716-132321_config_mdq_mcp_server_toml_summary_removal.md`).
All three touch different, non-overlapping keys — apply all three.

## Goal

Remove `enable_refresh` from `config/mdq_mcp_server.toml`, add a removal
note matching the existing `audit_log_path`/`concurrency_limit` style, and
add a clarifying line distinguishing it from `enable_grep` (which remains,
since it is actually enforced).

## Scope

**In:**
- Delete the "Enable refresh_index tool" comment and `enable_refresh = true`
  key (`config/mdq_mcp_server.toml:50-51`).
- Add a new `# NOTE:` block documenting this removal.
- Adjust the `enable_grep` comment (line 54) to add a clarifying phrase
  distinguishing it from the removed `enable_refresh` (both looked similar
  in config, but only `enable_grep` is wired to real enforced behavior).

**Out:**
- `enable_grep = true` (line 54) itself — the key/value stays; only its
  comment gains a clarifying note. Do not remove or change its value.
- Every other key in the file.

## Assumptions

1. `enable_refresh` becomes fully dead config once the companion
   `service.py` doc lands (removes `self.enable_refresh`) — no code reads
   this key at all after that change.
2. This file's established convention for documenting removed keys (the
   `audit_log_path`/`concurrency_limit` NOTE block) should be followed:
   state what was removed, the date, why (read but never enforced), and
   where to look for more detail.
3. `enable_grep` **is** enforced — `grep_docs()` raises
   `MdqValidationError` when `not self.enable_grep`
   (`service.py:393-394` per the source plan's Assumption 3) — the
   clarifying comment should state this explicitly so a future reader does
   not assume both flags are equally inert.

## Implementation

### Target file

`config/mdq_mcp_server.toml`

### Procedure

1. Open `config/mdq_mcp_server.toml`.
2. Delete lines 50-51:
   ```toml
   # Enable refresh_index tool (controls whether manual index refresh is allowed)
   enable_refresh = true
   ```
3. Update the `enable_grep` comment (current line 53, immediately above
   `enable_grep = true`):
   ```toml
   # Enable grep_docs tool (when false, grep_docs returns MdqValidationError)
   enable_grep = true
   ```
   to:
   ```toml
   # Enable grep_docs tool (when false, grep_docs returns MdqValidationError).
   # Unlike the removed enable_refresh, this flag is actually enforced in
   # MdqService.grep_docs() -- see docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md.
   enable_grep = true
   ```
4. Add a new NOTE block (placed adjacently with the other removal notes in
   this file; adjust the date to the actual implementation date):
   ```toml
   # NOTE: enable_refresh was removed ([implementation date]). It was parsed
   # but never enforced -- refresh_index() had no gate check on it and always
   # ran regardless of this flag's value. Index/refresh serialization (a
   # separate concern) is achieved via MdqService._index_lock, independent of
   # any config value. See docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md.
   # Re-add only alongside an implementation that actually reads and enforces it.
   ```

### Method

Direct deletion of one key (plus its comment), one comment-text
clarification on an adjacent unrelated key, and addition of one new NOTE
block.

### Details

- Do not change `enable_grep`'s value or remove it — only its comment
  gains clarifying text.
- Validate TOML syntax after editing via a TOML parser.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| TOML syntax valid | `python -c "import tomllib; tomllib.load(open('config/mdq_mcp_server.toml','rb'))"` | no exception |
| Key removed | `grep -n "^enable_refresh" config/mdq_mcp_server.toml` | 0 matches |
| `enable_grep` intact | `grep -n "^enable_grep = true" config/mdq_mcp_server.toml` | 1 match, unchanged value |
| Doc consistency | `uv run check-mcp-docs` | passes |
| Grep gate unaffected | `uv run pytest tests/test_mdq_service.py -k grep -v` | still passes unchanged |
