# Rotation archives, drill outputs and failed-restore leftovers have no retention, and timestamp names can collide

## Priority
Medium

## Summary
Only `*_corrupt_*` archives for rag and session are purged. Rotation archives, drill outputs and the quarantine directories and temp files of failed restores accumulate without bound, and second-granularity names allow overwrites.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-008). Evidence label: `Explicit in code` plus `Verified by test` (leftover quarantine directories observed in the reproduction), confidence Medium for the disk-exhaustion impact (not measured).

## Problem
- `purge_corrupt_archives` matches only `<stem>_corrupt_*<suffix>` for rag and session. Files from `rotation._archive_db_file` (`<stem>_<ts><suffix>` under `sqlite_archive_dir`) are never pruned, including workflow archives.
- `recovery_drill._drill_one_domain` creates a verified archive and a full copy (`*_restored.sqlite`) plus a JSON artifact under `<archive>/drills` on every run; nothing removes them.
- `_restore_from_backup` creates `<stem>_sidecar_quarantine_<ts>` even when no sidecar exists and removes it only on success; failure paths leave it, and `.tmp_` candidates survive when cleanup itself fails.
- `format_timestamp` has one-second resolution. Two restores or rotations of the same database within a second reuse the same names; `shutil.copy2` and the backup API then overwrite the earlier corrupt archive or archive.

## Reason for Change
Each leftover is a full or partial database copy. Unbounded growth eventually exhausts the disk that hosts the live databases, and an overwritten corrupt archive destroys forensic evidence.

## Implementation Intent
Extend the retention policy to every artifact class this package creates, create quarantine directories lazily, and make names unique.

## Target Files or Areas
- `scripts/db/maintenance.py` (`purge_corrupt_archives`)
- `scripts/db/rotation.py` (`_archive_db_file`)
- `scripts/db/recovery_drill.py` (`_drill_one_domain`, `_persist_artifact`)
- `scripts/db/recovery_restore.py` (`_stage_restore`)
- `scripts/db/config.py` (`format_timestamp`)
- `config/agent.toml` and its config reference, if new keys are added
- `tests/db/test_db_maintenance.py`, `tests/db/test_recovery_drill.py`

## Required Changes
- Define retention for rotation archives, drill outputs and quarantine directories (count and age), reusing the existing config pattern.
- Create the quarantine directory only when a sidecar is moved.
- Add sub-second or counter uniqueness to generated names, or fail instead of overwriting.
- Add tests for retention and for same-second collisions.

## Constraints
- Never delete the most recent verified archive per database.
- Adding config keys requires the generated reference tables to be refreshed (`tools/generate_reference_table.py --check`).
- No recursive deletion outside temporary directories while testing.

## Acceptance Criteria
- Repeated rotations and drills keep the archive directory within the configured bounds.
- Two operations within one second never overwrite each other's files.
- A failed restore leaves no empty quarantine directory.

## Testing Expectations
Unit tests with temporary directories and a patched clock. Run `uv run pytest tests/db` and `uv run python tools/generate_reference_table.py --check`.

## Documentation Impact
Document the new retention keys and the artifact lifecycle in the deployment/DB operations docs; run `tools/check_docs_consistency.py --domain db`.

## Out of Scope
- Offsite or remote backup.
- Changes to the restore verification logic.

## Dependencies
- `issues/20261114-092850_dbreview003_restore-sidecar-handling.md` decides whether the quarantine copy is retained after success.

## Unresolved Questions
- Desired retention numbers for archives and drill outputs are unknown (不明); needs an operator decision.

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`, then run the documentation checkers listed in `routing.md` for the docs touched. English comments and logs.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092857
- **Related target files**: scripts/db/maintenance.py, scripts/db/rotation.py, scripts/db/recovery_drill.py, scripts/db/recovery_restore.py, scripts/db/config.py, tests/db/test_db_maintenance.py, tests/db/test_recovery_drill.py
