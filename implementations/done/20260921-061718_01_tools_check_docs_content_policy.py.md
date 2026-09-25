## Goal
Scope `check_error_handling_table()`'s and `check_config_file_inventory_table()`'s
heading-proximity checks to the same Markdown section (stopping at the first
different-topic heading encountered while scanning backward), replacing the current
fixed `_HEADINGS_WINDOW` (10-line) backward scan that can pull an unrelated,
cross-section table/bullet-list into scope after an edit shrinks line distances.

## Scope
In scope: add `_SECTION_BOUNDARY_HEADING_RE`; modify the backward-scan loops inside
`check_error_handling_table()` and `check_config_file_inventory_table()` (REQ-001,
REQ-002, REQ-003 of `plans/20260920-205406_plan.md`).
Out of scope: any other detection function in this file (`check_full_json_example`,
`check_literal_port_number`, etc.); the two already-applied doc workarounds
(`docs/agent_05_llm-and-streaming.md`, `docs/06_eventbus_05_configuration-and-operations.md`).

## Assumptions
- Markdown headings follow `^#{1,6}\s+` (CommonMark ATX-heading syntax) — the same
  assumption every other heading regex in this file already makes (confirmed: `rg -n
  "\^#\{1,6\}" tools/check_docs_content_policy.py` matches 5 other heading regexes
  using this exact prefix).
- `_ERROR_ACTION_TABLE_HEADER_RE`'s path in `check_error_handling_table()` (line 688,
  which flags a `| Case | ... | Action |`-shaped table unconditionally, with no
  heading-proximity check at all) is untouched by this change — it has its own
  `continue` before the heading-window logic is ever reached.

## Design decisions
- Add one new regex, `_SECTION_BOUNDARY_HEADING_RE = re.compile(r"^#{1,6}\s+")`,
  matching any Markdown heading regardless of topic. Inside each backward-scan loop,
  check `_SECTION_BOUNDARY_HEADING_RE` first: if a line is *any* heading but does not
  match the target heading regex (`_ERROR_HEADING_RE`/`_CONFIG_HEADING_RE`), stop
  scanning immediately (different section) rather than continuing to the window's
  line-count bound. This is a strictly stronger constraint than the existing window,
  not a replacement algorithm — the window bound (`_HEADINGS_WINDOW`) is kept as an
  outer bound in the `range()` call, so a matching heading beyond 10 lines still
  will not be found (unchanged from today), only a *closer* non-matching heading now
  additionally stops the scan.
- Scan order matters: both loops currently scan from `i - _HEADINGS_WINDOW` (oldest)
  forward *toward* the table (`for j in range(max(0, i - _HEADINGS_WINDOW), i)` /
  `..., idx)`), i.e. increasing `j`. Since the loop wants the section boundary check to
  fire on the *nearest* intervening heading (the one structurally between the table
  and any further-back matching heading), the boundary check must be evaluated in
  the same forward order the existing loop already uses — no loop-direction change is
  needed, only an added `break`-on-boundary check evaluated before the existing
  target-heading check, each iteration.

## Alternatives considered
- Reversing the scan direction (nearest-to-table first) to find "the nearest heading
  of any kind" more naturally: rejected — the existing forward-from-window-start
  order already visits every line in the window, and adding the boundary check in
  the same loop (evaluated each iteration, in the existing order) produces the
  identical semantics without restructuring the loop or its existing `break`
  behavior on a target-heading match.
- Counting `#` characters to detect "equal-or-higher level" instead of "any other
  heading": rejected in favor of the module's own simplified approach already
  recorded in the Plan's Design section — matching *any* heading that isn't the
  target regex is sufficient here because both `_ERROR_HEADING_RE` and
  `_CONFIG_HEADING_RE` are themselves anchored on `^#{1,6}`, so a same-or-different
  level heading of a different topic already signals a section change for this
  checker's purposes; no currently-passing test relies on a same-topic heading at a
  different level being treated differently (per Plan Unknowns UNK-01 resolution).

## Implementation
### Target file
`tools/check_docs_content_policy.py`

### Procedure
1. Add `_SECTION_BOUNDARY_HEADING_RE = re.compile(r"^#{1,6}\s+")` near the other
   heading regexes (after `_ERROR_HEADING_RE`, before `_ERROR_ACTION_TABLE_HEADER_RE`,
   i.e. around line 101-102).
2. In `check_config_file_inventory_table()`, replace the loop at lines 423-426:
   ```python
   for j in range(max(0, i - _HEADINGS_WINDOW), i):
       if _CONFIG_HEADING_RE.search(doc.lines[j]):
           has_config_heading = True
           break
   ```
   with a version that also breaks (without setting `has_config_heading`) when a
   non-matching heading is encountered.
3. In `check_error_handling_table()`, replace the loop at lines 706-709:
   ```python
   for j in range(max(0, i - _HEADINGS_WINDOW), idx):
       if _ERROR_HEADING_RE.search(doc.lines[j]):
           has_error_heading = True
           break
   ```
   with the same pattern.

### Method
Direct file edit (`Edit` tool) — one new module-level regex constant, two modified
`for` loop bodies inside existing functions; no new function, no signature change.

### Details
Current `check_config_file_inventory_table()` loop (confirmed via Read, lines
420-428):
```python
            if not _CONFIG_BULLET_RE.match(line):
                continue
            has_config_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), i):
                if _CONFIG_HEADING_RE.search(doc.lines[j]):
                    has_config_heading = True
                    break
            if not has_config_heading:
                continue
```

Target replacement:
```python
            if not _CONFIG_BULLET_RE.match(line):
                continue
            has_config_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), i):
                if _CONFIG_HEADING_RE.search(doc.lines[j]):
                    has_config_heading = True
                    break
                if _SECTION_BOUNDARY_HEADING_RE.search(doc.lines[j]):
                    break
            if not has_config_heading:
                continue
```

Current `check_error_handling_table()` loop (confirmed via Read, lines 705-711):
```python
            has_error_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), idx):
                if _ERROR_HEADING_RE.search(doc.lines[j]):
                    has_error_heading = True
                    break
            if not has_error_heading:
                continue
```

Target replacement:
```python
            has_error_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), idx):
                if _ERROR_HEADING_RE.search(doc.lines[j]):
                    has_error_heading = True
                    break
                if _SECTION_BOUNDARY_HEADING_RE.search(doc.lines[j]):
                    break
            if not has_error_heading:
                continue
```
In both cases the added `if _SECTION_BOUNDARY_HEADING_RE.search(...): break` is
placed as the loop's second check (after the existing target-heading check), so a
line matching *both* (the target heading itself, which is also `#{1,6}`-prefixed)
still sets `has_config_heading`/`has_error_heading = True` and breaks via the first
branch, exactly as today — the new branch only fires when the target-heading check
already failed for that line.

## Compatibility considerations
No public API change — both functions keep their existing signature
(`files: list[DocFile]) -> list[Issue]`) and return type. The only behavioral change
is that fewer findings are produced (a strict narrowing: a table/bullet-list that was
previously flagged only because an unrelated heading fell within the fixed window is
no longer flagged) — no new finding type is introduced, and a table genuinely nested
under a matching heading with no intervening heading is unaffected (AC-2/REQ-003).

## Security considerations
N/A: this is a documentation-linting heuristic operating on already-trusted
repository `docs/*.md` content; no new input parsing, external call, or credential
handling.

## Rollback considerations
Trivially revertable: removing the new regex constant and the two added
`break`-on-boundary lines restores the exact prior window-only behavior.

## Validation plan
- `uv run ruff check tools/check_docs_content_policy.py` / `uv run mypy tools/check_docs_content_policy.py`.
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` — full file; the
  companion procedure (`implementations/20260921-061718_02_tests_tools_test_check_docs_content_policy.py.md`,
  this Plan's Row 2) adds the two new regression tests this change is written to
  satisfy — run once after both rows land, per the Plan's own Tests section.
- Re-run `uv run python tools/check_docs_content_policy.py` against the full `docs/`
  tree and confirm no new finding appears for `docs/agent_05_llm-and-streaming.md`
  or `docs/06_eventbus_05_configuration-and-operations.md` beyond what is already
  pre-existing/intentional (REQ-006, AC-6).

## Completion criteria
- Both loops contain the new `_SECTION_BOUNDARY_HEADING_RE`-based `break`, placed
  after the existing target-heading check.
- A table/bullet-list separated from its would-be matching heading by a different
  heading is no longer flagged (verified by Row 2's new tests).
- A table/bullet-list genuinely nested directly under a matching heading (no
  intervening heading) is still flagged (verified by the existing, unmodified tests).
- `uv run ruff check` / `uv run mypy` pass clean on this file.

## Out of scope
- Writing the new regression tests themselves — covered by this Plan's Row 2
  (`tests/tools/test_check_docs_content_policy.py`), a separate implementation
  procedure document.
- Any other detection function in this file.
- Reverting the two already-applied doc workarounds — explicitly out of scope per the
  Plan's own Assumptions (the `### LLMTransportError Kind Categories` rename and the
  expanded EventBus pointer paragraph remain valid after this fix).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_SECTION_BOUNDARY_HEADING_RE` and modify both loops | Completed | — | 20260921-194455 |  |
| 2 | Run `ruff check` / `mypy` on this file | Completed | — | 20260921-194455 |  |
| 3 | Run `tests/tools/test_check_docs_content_policy.py` and full `docs/` tree re-scan (after Row 2's tests also land) | Completed | — | 20260921-194455 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (section-scoped heading-proximity check for both functions)
- **Source issue**: issues/20260920-175121_dcpwin01_heading-window-heuristic-causes-false-positives-after-edits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-205406_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-061718
- **Related target files**: tools/check_docs_content_policy.py