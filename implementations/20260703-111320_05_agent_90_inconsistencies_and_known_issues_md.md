## Goal

Update DISC-03 in `docs/05_agent_90_inconsistencies_and_known_issues.md` to mark the branch-filter inconsistency as resolved and replace the inaccurate interpretation with the confirmed implementation facts.

## Scope

- In-Scope:
  - Replace the DISC-03 entry (lines 40–46) with a resolved entry that names the correct function, predicate, and module
- Out-of-Scope:
  - DISC-04 and all other entries in the file
  - Source code or test changes
  - `docs/05_agent_12_memory.md` (covered by the companion document `20260703-111319_05_agent_12_memory_md.md`)

## Assumptions

1. The DISC-03 entry occupies lines 40–46 of `05_agent_90_inconsistencies_and_known_issues.md`; its exact text is known from reading the file.
2. Marking a DISC entry "RESOLVED" via suffix appended to the heading is the correct convention for this file (consistent with how resolved items should be handled per the plan).
3. After Step 1 of the parent plan is applied, `05_agent_12_memory.md` will contain the corrected description, so the DISC-03 "Impact scope" note can reference the updated doc.
4. No other entry in the file depends on or cross-references DISC-03.

## Implementation

### Target file

`/home/masaos/llmagent/docs/05_agent_90_inconsistencies_and_known_issues.md`

### Procedure

1. Open `/home/masaos/llmagent/docs/05_agent_90_inconsistencies_and_known_issues.md`.
2. Locate the DISC-03 block (lines 40–46):

   ```markdown
   ### DISC-03: branch field in memory retrieval

   - **Type:** Undocumented behavior
   - **Impact scope:** `05_agent_12_memory.md` (line 190 — branch described only as "for context filtering")
   - **Statement A:** `branch` field is stored metadata for context filtering (implied by doc)
   - **Statement B:** `branch` is actively used in `FtsRetriever._context_boost()` as a relevance rescoring signal; records without matching branch are still returned but ranked lower
   - **Current safe interpretation:** Branch affects ranking, not filtering — it is an active retrieval parameter
   ```

3. Replace the entire DISC-03 block with the resolved entry:

   ```markdown
   ### DISC-03: branch field in memory retrieval -- RESOLVED

   - **Type:** Document inconsistency (resolved)
   - **Impact scope:** `05_agent_12_memory.md`
   - **Resolution:** Branch filtering is implemented as a hard SQL predicate
     `AND (? = '' OR m.branch = '' OR m.branch = ?)` in both `FtsRetriever` and
     `VectorRetriever`. Memories from non-matching branches are **excluded**, not merely
     ranked lower. Global memories (`branch = ''`) are always included. An additional scoring
     boost is applied by `scoring.context_boost()` when branch matches.
     `05_agent_12_memory.md` has been updated to reflect this behavior.
   - **Notes for AI reference:** `FtsRetriever._context_boost()` does not exist. Scoring is
     in `scoring.context_boost()` in `scripts/agent/memory/scoring.py`.
   ```

4. Save the file.

### Method

- Use the Edit tool with the exact `old_string` matching the current DISC-03 block (5-bullet list + heading) and `new_string` set to the replacement above.
- The blank line before `### DISC-04` must be preserved; do not include it in `old_string`.

### Details

- **Old string (exact, 7 lines including heading and blank line after it):**

  ```
  ### DISC-03: branch field in memory retrieval

  - **Type:** Undocumented behavior
  - **Impact scope:** `05_agent_12_memory.md` (line 190 — branch described only as "for context filtering")
  - **Statement A:** `branch` field is stored metadata for context filtering (implied by doc)
  - **Statement B:** `branch` is actively used in `FtsRetriever._context_boost()` as a relevance rescoring signal; records without matching branch are still returned but ranked lower
  - **Current safe interpretation:** Branch affects ranking, not filtering — it is an active retrieval parameter
  ```

- The predicate text `AND (? = '' OR m.branch = '' OR m.branch = ?)` is taken verbatim from `scripts/agent/memory/retriever.py` lines 111 and 174.
- `scoring.context_boost()` lives in `scripts/agent/memory/scoring.py` (confirmed from source).

## Validation plan

```bash
# 1. DISC-03 is marked RESOLVED
grep -n "RESOLVED" /home/masaos/llmagent/docs/05_agent_90_inconsistencies_and_known_issues.md
# Expected: >= 1 match containing DISC-03

# 2. No stale "Branch affects ranking, not filtering" claim
grep -n "Branch affects ranking" /home/masaos/llmagent/docs/05_agent_90_inconsistencies_and_known_issues.md
# Expected: 0 matches

# 3. Correct module reference present
grep -n "scoring.context_boost" /home/masaos/llmagent/docs/05_agent_90_inconsistencies_and_known_issues.md
# Expected: >= 1 match

# 4. Stale method reference removed
grep -n "FtsRetriever._context_boost" /home/masaos/llmagent/docs/05_agent_90_inconsistencies_and_known_issues.md
# Expected: 0 matches

# 5. Run all branch tests to confirm no regressions from doc-only changes
uv run pytest tests/test_regression_memory_branch.py tests/test_memory_retriever.py::TestBranchBoundary tests/test_memory_retriever.py::TestBranchIsolation -v
# Expected: all green
```
