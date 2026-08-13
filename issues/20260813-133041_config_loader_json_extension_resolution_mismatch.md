# ConfigLoader `_resolve_path` does not fall back from an explicit `.json` name to an existing `.toml` file, contradicting a test's expectation

## Priority
Medium

## Summary
`tests/shared/test_config_loader.py::TestExtensionResolution::test_missing_json_extension_appended`
fails: it writes `test.toml` to disk, then calls `loader.load("test.json")` expecting the loader
to fall back and find `test.toml`, but `ConfigLoader._resolve_path` treats an explicit
`.json`-suffixed name as final (no substitution), so it correctly raises `ConfigMissingError`
for a genuinely-missing `test.json`.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/config_loader.py`
(2026-08-13). This test fails identically before and after that refactor, confirming it
predates this session (Evidence label: Explicit in code — confirmed by direct inspection of
`_resolve_path` and the test body). It represents either a real gap in `ConfigLoader`'s
extension-resolution contract, or an incorrect test — this needs a decision, not a silent
patch, per `rules/coding.md`'s "Current behavior" classification guidance (defaults to
"Implementation fix required" when ambiguous).

## Implementation Intent
Decide the intended contract:
- **Option A**: `_resolve_path` should also try `.toml` when a bare or `.json`-suffixed name is
  requested but not found, matching the test's expectation.
- **Option B**: the test itself is wrong (should write `test.json`, not `test.toml`) and should
  be corrected to match the documented/intended behavior.

Do not choose implicitly — review the ~10 call sites that pass bare config names (e.g.
`"agent.toml"`, `"crawler.toml"`) to confirm which option preserves their existing behavior
before changing `_resolve_path`.

## Target Files or Areas
- `scripts/shared/config_loader.py` (`ConfigLoader._resolve_path`)
- `tests/shared/test_config_loader.py`

## Required Changes
- Audit all callers of `ConfigLoader.load`/`load_all` for whether they rely on bare-name or
  explicit-extension resolution.
- Either extend `_resolve_path`'s fallback logic (Option A) or correct the test (Option B).
- Add characterization tests pinning the chosen contract explicitly (both the found-via-fallback
  and not-found cases).

## Acceptance Criteria
- `test_missing_json_extension_appended` (or its corrected replacement) passes.
- All existing `ConfigLoader` callers continue to resolve the same files they did before.
- The intended `.json`/`.toml` fallback contract is explicit in a test, not just implied.

## Testing Expectations
Full `tests/shared/test_config_loader.py` suite must pass. Add a test for the corrected/expanded
contract if Option A is chosen; update the existing test's fixture setup if Option B is chosen.

## Documentation Impact
If `ConfigLoader`'s extension-resolution behavior is documented anywhere under `docs/`, update it
to match whichever option is chosen.

## Out of Scope
- Do not change `ConfigLoader.load`/`load_all`'s public signatures.
- Do not touch permission/restriction (`restrict_to`) logic — unrelated to this issue.

## AI Implementation Instruction
Read `scripts/shared/config_loader.py::ConfigLoader._resolve_path` and
`tests/shared/test_config_loader.py::TestExtensionResolution` in full first. Grep all
`ConfigLoader().load(` / `.load_all(` call sites across `scripts/` before deciding Option A vs
B — if any caller's behavior would change under Option A, prefer Option B (fix the test) unless
explicitly told otherwise. Stop and report back if the two options are equally plausible.
