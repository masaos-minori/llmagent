## Goal
- Confirm workflow definition validation is already implemented and add retry stage description to docs

## Findings
- `workflow_loader.py`: Validation already implemented — duplicate stage ID, required stages (plan/execute/verify), retry policy (max_attempts >= 1, backoff in {fixed, exponential}, backoff_sec >= 0) ✓
- `test_workflow_loader.py`: 5 tests already implemented — all 18 tests pass ✓
- Docs: Missing retry stage description in `05_agent_03_turn-processing-flow.md` — added

## Changes Made
- Added workflow stages section to `docs/05_agent_03_turn-processing-flow.md:L191-L197`:
  - `plan` — LLM generates initial plan; required
  - `execute` — LLM executes the plan; required  
  - `verify` — LLM verifies execution results; required
  - `retry` — optional transport error retry gate after execute; retryable: false

## Conclusion
Code changes already complete. Documentation update applied.
