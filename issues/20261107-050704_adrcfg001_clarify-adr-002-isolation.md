# Clarify configuration isolation exceptions and security guarantees in ADR-002

## Priority
Medium

## Summary
Clarify `docs/10_adr/adr_02_01_002_platform-config-isolation.md` so the general `restrict_to()` rule and the EventBus exception are immediately identifiable, file isolation is separated from key validation, and security claims match the actual mechanisms.

## Background
Confirmed by reading the current file (Explicit in file):
- Decision item 81 states each process restricts itself to its own file via `ConfigLoader.restrict_to()`, and line 187 says the restriction is "otherwise unconditional", while the EventBus loads through the shared loader without `restrict_to()` and relies on a local invariant (`load_config()` accepts only the path from `get_config_path()`; Implementation Notes line 257).
- Rationale (line 114) says "access to other processes' Secrets is physically blocked."
- The Required Keys table mixes loader file restriction with key validation by `load_config()`/validators.

## Problem
A universal statement followed by an exception may lead implementers to remove a deliberate exception or add unnecessary mechanisms. File selection and key validation address different risks. Application-level loader restrictions do not prevent a process from reading arbitrary files, so "physically blocked" overstates the guarantee. This is a clarification need, not a confirmed inconsistency in the EventBus exception.

## Reason for Change
An inaccurate security assurance can mislead operators and reviewers. It is Medium because it is a wording and precision issue; the underlying mechanisms are not changed. Nothing makes it time-sensitive.

## Implementation Intent
Describe the existing configuration model with its limits. Distinguish permitted configuration files, schema and key validation, the shared loading mechanism, EventBus-local controls, and operating-system access restrictions. Replace unsupported physical-isolation claims with mechanism-specific guarantees and state which assumptions depend on deployment controls outside the loader.

## Target Files or Areas
- `docs/10_adr/adr_02_01_002_platform-config-isolation.md`

## Required Changes
- Reconcile the general `restrict_to()` wording with the EventBus exception.
- Separate file isolation from schema and key validation.
- Clarify the shared loader's role and the EventBus-local responsibilities.
- Distinguish application-level restrictions from operating-system controls.
- Replace unsupported physical-isolation claims with mechanism-specific guarantees.
- Identify security assumptions that depend on deployment controls outside the loader.

## Constraints
- Do not remove the EventBus exception merely to simplify the document.
- Do not claim loader restrictions prevent arbitrary filesystem access.
- Do not introduce new secret-management or operating-system mechanisms.
- If the actual mechanism cannot be established, report the required implementation evidence.
- Preserve invariant identifiers and anchors; write in English; follow `skills/DESIGN.md` Docs content policy.

## Acceptance Criteria
- The general rule and the EventBus exception are immediately identifiable.
- File restrictions and key/type validation have separate responsibilities.
- Security claims match the described mechanisms.
- External deployment assumptions are explicit where relevant.
- Existing configuration ownership remains unchanged.

## Testing Expectations
Not required (documentation-only). Review the document for universal claims that conflict with exceptions or exceed the stated controls. Run `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_adr_preservation.py`, `check_adr_structure.py`, and `check_docs_japanese.py`.

## Documentation Impact
Yes, this issue is the documentation change: boundaries, constraints, and security guarantees in ADR-002.

## Out of Scope
- Loader refactoring
- Secret-management redesign
- EventBus authentication changes

## Dependencies
- Blocks the final mapping step of `issues/20261107-050705_adrver001_align-invariant-verification-claims.md`.
- Sibling check: no open issue or in-flight plan targets this file.

## Unresolved Questions
- 不明: whether any operating-system or deployment control (file permissions, service users) is actually in place to restrict file access; the ADR must state only what is evidenced.

## AI Implementation Instruction
Edit only ADR-002. Keep changes minimal; do not alter decisions, invariants, or ownership. Report missing mechanism evidence instead of asserting a guarantee.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-050704
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`
