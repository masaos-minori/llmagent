Analyze all Python files under `./scripts/agent/` and produce a Markdown refactoring plan.

Your task is to read the codebase and generate a concrete, file-by-file refactoring plan.

## Output requirements
- Output a single Markdown document.
- Organize the document with exactly these sections:
  1. Overall Policy
  2. Implementation Rules
  3. File-by-File Changes
  4. Work Steps
  5. Definition of Done
- In the "File-by-File Changes" section, describe improvements for each file individually.
- For each file, assign priorities to improvement items using:
  - High
  - Medium
  - Low
- Be concrete and implementation-oriented. Do not give vague recommendations.

## Mandatory refactoring constraints
- Do not preserve backward compatibility. Remove backward-compatibility code instead of keeping it.
- Do not use `assert` in business logic. Replace all precondition checks with explicit exceptions.
- Do not use `except Exception`. Replace it with exception handling for specific exception types only.
- Do not use `dict[str, Any]` outside external boundaries. Convert data into typed structures immediately after crossing a boundary.
- Do not allow unconditional string conversion such as `str(args.get(...))`. Validate input types first, and raise an exception for unexpected types.
- Apply strict typing and strict conversion throughout the codebase.
- Do not treat `None`, empty strings, and unset values as equivalent.
- Define dedicated DTOs for:
  - audit logs
  - approval decisions
  - execution results
- Validate all LLM-derived JSON immediately after decoding. If the schema does not match, fail immediately.
