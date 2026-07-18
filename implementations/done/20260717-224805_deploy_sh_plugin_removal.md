# Implementation: deploy/deploy.sh (remove plugins/ deployment block)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 8)

Gap-filling note: fills the missing doc for plan Implementation step 8, which
had no `implementations/` doc despite being explicitly listed as its own
numbered step. Should land no earlier than the existing, already-completed
`plugins_directory_removal` doc (step 5), which deletes `plugins/` from the
repo — this doc removes deploy.sh's now-pointless attempt to copy that
now-nonexistent directory.

**Important, repo-specific correction vs. a sibling plan's finding**: an
unrelated implementation task earlier today (the "RuntimeToolRegistry
migration" chain) found `deploy/deploy.sh` copies `scripts/` via a single
`rsync -av --delete` directory-level sync with NO per-file copy list — so
new/deleted files under `scripts/` need no deploy.sh edit at all. That finding
does NOT apply here unchanged: `scripts/`'s deleted plugin files (`plugin_registry.py`
etc., step 2) indeed need no deploy.sh edit for that reason. BUT `plugins/`
(the top-level directory, singular vs. `scripts/`) has its OWN SEPARATE,
dedicated deployment block in `deploy/deploy.sh` — confirmed by direct read,
lines 74-79 — which is NOT part of the `scripts/` rsync and DOES need editing.

## Goal

`deploy/deploy.sh` no longer has a dedicated block attempting to deploy the
now-deleted `plugins/` directory.

## Scope

**In scope**: `deploy/deploy.sh` — delete the "プラグイン" (Plugin) section
(lines 74-79):
```bash
# ── プラグイン ────────────────────────────────────────────────────────────────
echo "--- plugins/ → /opt/llm/plugins/ ---"
mkdir -p /opt/llm/plugins
# 既存ファイルを上書きしない (プロダクション固有プラグインを保護)
cp -n "${REPO_ROOT}/plugins/"*.py /opt/llm/plugins/ 2>/dev/null || true
```

**Out of scope**: the `scripts/` rsync block immediately above it (unaffected
— `scripts/`'s deleted plugin files are automatically excluded from the next
rsync run once they no longer exist in the source tree, no deploy.sh edit
needed for those, matching the sibling chain's finding); any other deploy.sh
section (pyproject.toml/uv.lock copy, deadletter dir, etc.).

## Assumptions

1. Confirmed by direct read (2026-07-17): this is the ONLY `plugin`-mentioning
   block in `deploy/deploy.sh` (`grep -n "plugin" deploy/deploy.sh` returns
   exactly these 3 lines: the section header comment, the `echo`, and the `cp -n`).
2. The block uses `cp -n` (no-clobber) specifically to protect
   "プロダクション固有プラグイン" (production-specific plugins) that might have
   been manually placed in `/opt/llm/plugins/` outside of version control —
   this doc does NOT delete `/opt/llm/plugins/` on the production host itself
   (out of scope — this is a repo/deploy-script change, not a live-host
   cleanup action); it only stops the deploy script from re-creating/writing
   to that directory on future deploys. Any existing `/opt/llm/plugins/`
   contents on a real production host are left untouched by this change.
3. Once `plugins/` is deleted from the repo (already done per the
   `plugins_directory_removal` doc), `"${REPO_ROOT}/plugins/"*.py` would glob
   to nothing and `cp -n` would fail silently (already guarded by `|| true`)
   — so leaving this block in place is not a hard failure, but it is dead,
   confusing code that should be removed for cleanliness (matches the plan's
   step 8 intent and its Design section's subtractive-completeness principle).

## Implementation

### Target file

`deploy/deploy.sh`

### Procedure

1. Delete lines 74-79 in full:
   ```bash
   # ── プラグイン ────────────────────────────────────────────────────────────────
   echo "--- plugins/ → /opt/llm/plugins/ ---"
   mkdir -p /opt/llm/plugins
   # 既存ファイルを上書きしない (プロダクション固有プラグインを保護)
   cp -n "${REPO_ROOT}/plugins/"*.py /opt/llm/plugins/ 2>/dev/null || true
   ```
2. Confirm the file still reads cleanly around the removed block (no orphaned blank-line/comment artifacts) — check the section immediately following this block in the current file and ensure spacing/section separators remain consistent with the rest of the script's style.

### Method

Direct deletion of one self-contained script section — no other line in the file references this block or depends on it running.

### Details

- Do not delete `/opt/llm/plugins/` itself or its contents on any live host — this is a repo-only change to stop future deploys from touching that path; any operational cleanup of an existing production `/opt/llm/plugins/` directory is a separate, human operational decision outside this plan's scope.
- Do not touch the `scripts/` rsync block or any other section.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain | `grep -n "plugin" deploy/deploy.sh` | 0 matches |
| Syntax check | `bash -n deploy/deploy.sh` | no syntax errors |
| Manual review | read the diff | only the 6-line plugin block removed, nothing else changed |
