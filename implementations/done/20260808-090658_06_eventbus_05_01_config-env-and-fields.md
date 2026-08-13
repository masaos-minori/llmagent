## Goal
- Restructure `docs/06_eventbus_05_01_config-env-and-fields.md` to remove implementation details like complete environment variable tables and field type/default value tables while explicitly preserving operationally critical configuration meaning, security startup constraints, and deprecated-key fail-startup policy.

## Scope
- **In-Scope**: `docs/06_eventbus_05_01_config-env-and-fields.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid via independent verification against source code
- Deprecated-key fail-startup policy must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete environment variable tables
- Remove complete field type/default value tables
- Remove EventBusConfig.__post_init__() explanation
- Remove internal names like _REMOVED_CONFIG_KEYS
- Preserve: config file role, required and operationally critical configuration meaning, host/allow_public_bind security meaning, max_retry DLQ operation impact, fail-startup-on-deprecated-config-key policy, intent of early config error detection

## Alternatives considered
- Keeping complete env var tables but adding a note pointing to config/eventbus.toml as canonical
- Converting field tables to prose descriptions instead of removing them
- Moving detailed configuration specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_05_01_config-env-and-fields.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where configuration design judgments are distributed
2. Identify all env var tables, field type/default value tables, and __post_init__ sections

#### Phase 2: Core Logic Implementation
1. Compress or remove complete environment variable tables
   - Replace with high-level description of configuration categories
2. Remove complete field type/default value tables
   - Delete field-by-field type/constraint/default-value listings
3. Remove EventBusConfig.__post_init__() explanation
   - Delete validation branching logic descriptions
4. Remove internal names like _REMOVED_CONFIG_KEYS
   - Delete internal constant references
5. Preserve configuration-critical information:
   - Config file role and purpose
   - Required and operationally critical configuration meaning
   - host/allow_public_bind security meaning
   - max_retry DLQ operation impact
   - Fail-startup-on-deprecated-config-key policy
   - Intent of early config error detection

#### Phase 3: Deployment & Verification
1. Confirm deprecated-key fail-startup policy was not weakened
2. Confirm cross-reference to config/eventbus.toml and config.py exists for all removed details
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve deprecated-key fail-startup policy during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Deprecated-key fail-startup policy is critical operational constraint — must survive unchanged
- Security-related configuration meanings (host/allow_public_bind) are critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Deprecated-key fail-startup policy must survive unchanged

## Security considerations
- Critical: Security-related configuration constraints must not be weakened during cleanup
- host/allow_public_bind security meaning must survive intact
- Fail-startup-on-deprecated-key policy is a security boundary statement

## Rollback considerations
- Preserve pre-edit backup of deprecated-key fail-startup policy section
- If security-related configuration statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Startup Policy | Manual | Fail-startup-on-deprecated-key preserved |
| Cross-references | Manual | All removed details point to config/eventbus.toml / config.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No complete env var tables or field type/default value tables remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-173844_require.md
- Source plan: plans/20260807-203844_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-090658
- Related target files: docs/06_eventbus_05_01_config-env-and-fields.md
