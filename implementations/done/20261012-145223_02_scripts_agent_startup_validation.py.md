## Goal
- Record an unexpected failure of the drift check as FATAL when routing_drift_strict is true and as a WARNING outcome when it is false; treat unreadable strictness as strict (`REQ-002`, `REQ-003`).

## Scope
- Block 5 (routing drift) of check_services and one small module-level helper in `scripts/agent/startup_validation.py`. Block 5b (safety tiers) and every other block are untouched.

## Assumptions
- After procedure 01 an unexpected failure propagates out of check_routing_drift to this block.
- The pipeline result object offers add_fatal and add_warning taking a source label and a message, as used by the neighbouring blocks.
- check_services is already at radon grade D (26); the new branch must live in the helper so its score does not grow.

## Design decisions
- Read the strictness into a variable that starts as true before the try, then assign the configured value inside it, so a failure while reading the setting is classified as strict (fail-closed).
- Keep the RuntimeError handler as it is; only the generic handler changes, delegating to the helper.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. Apply procedures 03 and 04 first and confirm their new-policy tests fail against the current code.
2. Add a module-level helper that takes the pipeline result object, the caught exception, and a keyword-only strict flag; it builds the message Routing drift check failed followed by the exception text, and records it with add_fatal for the routing_drift source when strict and with add_warning otherwise.
3. In block 5 set the strictness variable to true before the try; inside the try assign it from the tool configuration setting routing_drift_strict and pass that variable to check_routing_drift instead of reading the configuration a second time.
4. Keep the except RuntimeError handler calling add_fatal.
5. Replace the body of the generic handler with a call to the helper, and rewrite its explanatory noqa comment to state the rule: an unexpected failure of the drift check follows routing_drift_strict, because an unknown result is not a clean result.
6. Leave block 5b and all other blocks unchanged.

### Method
- Edit block 5 and add the helper above the class or next to the other module-level helpers; keep imports and type annotations consistent with the module.

### Details
- Drift warnings from check_routing_drift still go to add_warning exactly as before.
- The helper needs no new import: the pipeline result class is already imported in this module.
- Do not wrap the strictness read in its own handler; the default-to-strict variable covers it.

## Compatibility considerations
- Behavior change by design: in a strict deployment (required in production) a broken drift check now aborts startup; in a non-strict deployment it now yields a recorded WARNING instead of a log line. A running production agent picks this up only after redeploy; deployment is outside this procedure.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- The tests from procedures 03 and 04 pass; the existing pipeline tests pass unchanged: `uv run pytest tests/agent/test_startup_severity_classification.py tests/agent/test_startup_validation.py tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup.py -v`.
- `uv run ruff format --check scripts/`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/agent -c pyproject.toml`; radon grade of check_services stays D with a score of 26 or lower.
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05, 06 and 07 (docs); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- Block 5 classifies an unexpected failure by strictness through the helper, with strict as the fallback when the setting is unreadable; the RuntimeError mapping and block 5b are unchanged; the new pipeline tests pass; radon score of check_services is not higher.

## Out of scope
- The safety-tier block, the RAG-consistency and readiness blocks, and the drift findings.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the helper and reclassify the generic handler of block 5 by strictness | Completed | 20261012-145715 | 20261012-145743 | stale_detector clean; tests 03/04 seen failing first changed: scripts/agent/startup_validation.py (helper + block 5); block 5b untouched; check_services radon stays D (26) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-145743 | 20261012-145743 | ruff, mypy, lint-imports, bandit pass; 93 tests pass; 5 new pipeline tests pass |

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
- **Requirement ID**: `REQ-002`, `REQ-003` (severity follows routing_drift_strict; RuntimeError mapping and safety-tier block unchanged)
- **Source issue**: issues/20261012-124829_start003_startup-routing-drift-check-downgrades-failures-to-warnings-while-safety-tier-check-stays-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-144923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-145223
- **Related target files**: scripts/agent/startup_validation.py