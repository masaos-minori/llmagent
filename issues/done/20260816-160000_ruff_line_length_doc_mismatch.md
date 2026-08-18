# `rules/coding.md` documents ruff line-length as 120, but `pyproject.toml` sets it to 88

## Priority
Medium

## Summary
`rules/coding.md`'s "Mandatory conventions" table and "Tool configuration" section both state
`ruff: line-length = 120`. The actual `pyproject.toml` `[tool.ruff]` section sets
`line-length = 88`. This is a live documentation/code mismatch in a rules file that is loaded
("always load alongside the skill") for every Python task in this repo, including every refactor
cycle.

## Reason for Change
Per `rules/coding.md`'s own "Documentation notes — Current behavior classification" table, a
mismatch between documented and actual tool config is classified as "Documentation fix required"
(the doc is wrong; fix the doc directly) rather than "Implementation fix required" — the actual
88-char limit is presumably intentional (it's what `ruff format` enforces across the codebase
today), so the doc should be corrected to match, not the config changed.

## Implementation Intent
Update `rules/coding.md`'s two mentions of line-length (the "Mandatory conventions" table and the
"Tool configuration (pyproject.toml)" section) from 120 to 88, matching `pyproject.toml`. Do not
change `pyproject.toml` — confirm with a maintainer first if 88 seems like the wrong value,
since it affects every file's formatting repo-wide.

## Target Files or Areas
- `rules/coding.md` (lines documenting `line-length`)

## Required Changes
- Change "Line length | max 120 chars — enforced by `ruff format`" to "max 88 chars."
- Change "`line-length = 120`" (under "Tool configuration") to "`line-length = 88`."

## Acceptance Criteria
- `rules/coding.md`'s stated line-length matches `pyproject.toml`'s `[tool.ruff] line-length`
  value exactly.
- No other content in `rules/coding.md` is altered.

## Testing Expectations
Not required — documentation-only change with no code/behavior impact.

## Documentation Impact
This issue *is* the documentation fix. No further doc impact beyond the file itself.

## Out of Scope
- Do not change `pyproject.toml`'s `line-length` value.
- Do not audit other tool-config values in `rules/coding.md` for accuracy as part of this issue
  (file separately if further drift is found).

## AI Implementation Instruction
Re-confirm `pyproject.toml`'s current `line-length` value at implementation time (it may have
changed since this issue was filed) before editing `rules/coding.md`, and match the doc to
whatever the config actually says at that point — do not assume 88 is still current.
