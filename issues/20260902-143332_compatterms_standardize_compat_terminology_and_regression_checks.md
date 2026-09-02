# Standardize compatibility terminology and document regression checks

## Priority
Low

## Summary
Documentation uses terms such as compatibility, fallback, default, migration, deprecated,
obsolete, and dead code in contexts that do not always share the same meaning. Removed names
and obsolete claims can also be copied back into current specifications after manual cleanup,
since no documented check currently distinguishes current specifications from legitimate
historical references when detecting removed compatibility names.

## Background
N/A: covered by Summary.

## Problem
Terminology ambiguity can cause active availability, recovery, validation, and
schema-migration mechanisms to be mistaken for removable compatibility shims. A terminology
update without a regression-check policy would also leave the same obsolete descriptions free
to reappear later.

## Reason for Change
Combining terminology and documentation-check guidance ensures that the vocabulary used to
classify compatibility behavior is the same vocabulary enforced during review.

## Implementation Intent
Define and consistently use these categories: Backward Compatibility (acceptance of an old
API, data format, configuration, or caller contract), Operational Fallback (an alternative
execution path after a runtime failure), Default (normal behavior when an optional setting is
omitted), Lenient Parsing (acceptance of incomplete/malformed input through substitute values),
Migration (conversion of persistent data or schemas to a newer contract), Deprecated (still
present but no longer recommended), Obsolete/Dead Code (present but no longer used). Document
checks must detect removed names and unsupported claims in current specifications while
allowing clearly marked historical references, with temporary exceptions owned, justified, and
time-limited.

## Target Files or Areas
- `docs/00_governance_02_documentation-metadata.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/00_governance_04_documentation-checks.md`
- `docs/03_rag_00_document-guide.md`
- `docs/03_rag_90_inconsistencies_and_known_issues.md`
- `docs/05_agent_00_document-guide.md`
- `docs/90_shared_00_document-guide.md`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Add definitions for Backward Compatibility, Operational Fallback, Default, Lenient Parsing, Migration, Obsolete, and Dead Code; clarify the existing definition of Deprecated; add one project-relevant example for each term.
- Stop describing RAG in-process recovery after remote-service failure, Memory FTS-only degradation, Workflow DB migrations, and static `ToolRegistry`'s routing role as backward compatibility.
- Search the documentation set and normalize inconsistent terminology.
- Define a rule for detecting removed names in current specifications (e.g. `read_json_file`, `_update_null_fill`, `ToolRouteResolver`+`server_configs` co-occurrence) once each is confirmed removed by its own issue.
- Apply different validation treatment to current specifications and historical sections; define an allowlist or annotation for legitimate Migration History references.
- Decide whether each finding is Blocking or Warning; define a temporary exception process requiring a reason, owner, and expiration date.
- Add the documentation compatibility check to the pull-request checklist; state that completion requires zero unexplained findings.

## Constraints
Documentation and governance only. This issue defines the check's rules and vocabulary; it
does not implement the check script (see Out of Scope).

## Acceptance Criteria
- Backward compatibility and operational fallback are consistently distinguished across the documentation set.
- Migration and compatibility shim are not used interchangeably.
- Active availability and validation mechanisms are not described as obsolete compatibility code.
- Glossary definitions and area documents use the same terminology.
- Reintroduction of removed names into current specifications is detectable by a documented rule.
- Legitimate historical references do not fail validation under that rule.
- Temporary exceptions are owned, justified, and time-limited.
- The validation command and pass/fail criteria are documented.

## Testing Expectations
Not required for this issue's own scope (terminology and rule definition). The check script's
own tests are covered by whichever follow-up issue implements it (see Out of Scope).

## Documentation Impact
Yes — this issue's entire scope is the governance/glossary documents listed above.

## Out of Scope
- Implementing the check script (a follow-up issue once this issue's rules are defined).
- Renaming source-code identifiers solely for terminology consistency.
- General spell-checking or Markdown linting.
- Redefining ADR lifecycle statuses.
- Changing runtime behavior.

## Dependencies
The removed-name detection rule references names confirmed removed by `ragcontract`
(`read_json_file`), `ragfreshness` (`_update_null_fill`), and `toolroutedoc`
(`ToolRouteResolver`+`server_configs`) — sequence this issue after those three, or after
confirming each removal independently if done earlier.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Define terminology and the detection rule in governance documents only; do not implement the
check script itself in this issue. Confirm each "removed name" example against current source
before citing it, since a name's removal status may change before this issue is implemented.
