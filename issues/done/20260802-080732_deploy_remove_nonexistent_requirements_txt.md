# Remove nonexistent requirements.txt full-listing from docs/02_deployment-part1.md

## Priority
High

## Summary
`docs/02_deployment-part1.md` §1.2 (~lines 41-55) transcribes the full contents of a `requirements.txt` file, but no such file exists in the repository — dependency management is fully consolidated in `pyproject.toml`/`uv.lock`, and `deploy/deploy.sh` never references `requirements.txt`. The listing even includes `langdetect`, an unused package.

## Reason for Change
This is a confirmed factual error (verified via file search and `deploy.sh` inspection), not speculation — a reader following this section might attempt `pip install -r requirements.txt` or search for a file that doesn't exist, leading to a failed environment setup.

## Implementation Intent
Remove the full `requirements.txt` listing entirely, keeping only the existing, correct `uv sync --dev --system-certs` instruction that already completes the dependency-installation step.

## Target Files or Areas
`docs/02_deployment-part1.md` (§1.2, ~lines 41-55)

## Required Changes
- Remove the `requirements.txt` content listing.
- Replace with: "依存パッケージは `pyproject.toml`/`uv.lock` に一本化して管理する(`uv sync --dev --system-certs` で導入完結)。"
- If this reflects a genuinely deprecated past pip-based workflow, optionally add a one-line "deprecated" note to the Known Issues equivalent for this domain rather than keeping the content inline.

## Acceptance Criteria
No `requirements.txt` content is transcribed in this file; the dependency-installation instruction correctly points to `uv sync --dev --system-certs` only.

## Testing Expectations
Not required (documentation-only). Confirm via `find . -iname requirements.txt` (expect no results) and `grep -n requirements.txt deploy/deploy.sh` (expect no results) before finalizing.

## Documentation Impact
`docs/02_deployment-part1.md` corrected and shortened.

## Out of Scope
Do not change `pyproject.toml`/`uv.lock` or `deploy/deploy.sh` in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error — apply directly. Re-verify `requirements.txt`'s non-existence and `langdetect`'s unused status before finalizing, in case something has changed since this review.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §2 削除候補 item 1, §5 例1, §6 (requirements.txt全文列挙)
- Generated at: 2026-08-02
