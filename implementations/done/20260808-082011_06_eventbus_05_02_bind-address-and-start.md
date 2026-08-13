## Goal
- Restructure `docs/06_eventbus_05_02_bind-address-and-start.md` to remove implementation details like complete address classification tables and duplicate startup command examples while explicitly preserving the danger of public binding for unauthenticated Event Bus API, the recommendation for allow_public_bind=false, and the design judgment to use startup failure to prevent unsafe exposure.

## Scope
- **In-Scope**: `docs/06_eventbus_05_02_bind-address-and-start.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid through independent verification against source code
- Public bind warning and startup failure protection must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete address classification table (loopback, private IP, wildcard IPv4/IPv6, hostname)
- Remove duplicate startup command examples
- Remove complete TOML example
- Remove diff memo comparing actual deployment vs documented example
- Preserve: Event Bus API has no authentication so public bind is dangerous, should run within loopback or trusted network, allow_public_bind=true is generally not recommended, conditions requiring external auth boundary, design judgment to use startup failure to prevent unsafe exposure

## Alternatives considered
- Keeping complete address classification table but adding a note pointing to config/eventbus.toml as canonical
- Converting address classifications to prose descriptions instead of removing them
- Moving detailed configuration specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_05_02_bind-address-and-start.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where bind address design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove complete address classification table
   - Replace with brief description of address categories
2. Remove duplicate startup command examples
   - Delete redundant invocation patterns
3. Remove complete TOML example
   - Delete full configuration file listing
4. Remove diff memo comparing actual deployment vs documented example
   - Delete side-by-side comparison text
5. Preserve design-critical information:
   - Event Bus API has no authentication — public bind is dangerous
   - Should run within loopback or trusted network
   - allow_public_bind=true is generally not recommended
   - Conditions requiring external auth boundary
   - Design judgment to use startup failure to prevent unsafe exposure

#### Phase 3: Deployment & Verification
1. Confirm public bind warning and startup failure protection were not silently dropped or weakened
2. Confirm cross-reference to `config/eventbus.toml` and `config.py` exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve public bind warning and startup failure statements during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Public bind warning is critical security constraint — must survive unchanged
- Startup failure protection is critical safety mechanism — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Public bind warning and startup failure statements must survive unchanged

## Security considerations
- Critical: Public bind warning must not be weakened during cleanup
- Startup failure protection is critical safety mechanism — must survive unchanged
- These are the single most important security constraints in this chapter

## Rollback considerations
- Preserve pre-edit backup of public bind warning and startup failure sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Public Bind Warning | Manual | Explicitly preserved |
| Startup Failure Protection | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to config/eventbus.toml / config.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-174328_require.md
- Source plan: plans/20260807-203947_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-082011
- Related target files: docs/06_eventbus_05_02_bind-address-and-start.md
