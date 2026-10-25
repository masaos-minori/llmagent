#!/usr/bin/env bash
#
# memo_rebase.sh — safely reconcile a diverged local branch with its upstream.
#
# Use when:
#   * local HEAD is ahead of upstream AND upstream has new commits (diverged)
#   * a rebase onto upstream would conflict and cannot be resolved automatically
#   * the local change is known to be a duplicate of upstream work
#
# Safety model (this script never silently destroys work):
#   * refuses to run on a dirty tree or a non-branch (detached HEAD)
#   * refuses when no upstream is configured
#   * classifies the divergence; fast-forward cases are handled with push/merge, not reset
#   * creates a backup ref of the pre-reset HEAD before any reset
#   * asks for an interactive y/N confirmation before touching anything
#   * verifies the post-state and prints how to undo
#
# This script does NOT perform a destructive git command until you confirm.
#
# Usage:
#   ./memo_rebase.sh [--soft] [--hard] [--dry-run]
#
#   --soft     git reset --soft @{u}   keep local changes staged/recoverable
#   --hard     git reset --hard  @{u}  (default) working tree matches upstream
#   --dry-run  print the plan and stop before changing anything
#
# Env override: UPSTREAM=origin/main   (default: @{u})
#
set -euo pipefail

# ---- argument parsing ------------------------------------------------------
DRY_RUN=0
RESET_MODE="hard"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --soft)      RESET_MODE="soft";  shift ;;
    --hard)      RESET_MODE="hard";  shift ;;
    --dry-run)   DRY_RUN=1;          shift ;;
    -h|--help)   sed -n '2,26p' "$0"; exit 0 ;;
    *)           echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

# ---- helpers ---------------------------------------------------------------
die() { echo "ERROR: $*" >&2; exit 1; }

# ---- preflight -------------------------------------------------------------
git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || die "detached HEAD — aborting"

UPSTREAM_REF="${UPSTREAM:-@{u}}"
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1 \
  || die "no upstream configured for '$BRANCH'. Set one with: git push --set-upstream origin <branch>"

# reset --hard only touches TRACKED files; untracked files survive. Fail on
# tracked modifications/staging, which are the ones at risk of loss.
if [[ -n "$(git diff --name-only)$(git diff --cached --name-only)" ]]; then
  die "tracked files have uncommitted changes. commit, commit-and-sync, or stash them first."
fi

# ---- classify the divergence ----------------------------------------------
LOCAL_SHA="$(git rev-parse HEAD)"
UPSTREAM_SHA="$(git rev-parse "$UPSTREAM_REF")"
MERGE_BASE="$(git merge-base HEAD "$UPSTREAM_REF")"

echo "branch        : $BRANCH"
echo "local HEAD    : $LOCAL_SHA"
echo "upstream      : $UPSTREAM_SHA ($UPSTREAM_REF)"
echo "merge-base    : $MERGE_BASE"
echo

if [[ "$LOCAL_SHA" == "$UPSTREAM_SHA" ]]; then
  echo "status        : up to date — nothing to do"; exit 0
fi
if [[ "$MERGE_BASE" == "$LOCAL_SHA" ]]; then
  echo "status        : local only ahead (fast-forwardable)"
  echo "                action: 'git push' (no reset required)"; exit 0
fi
if [[ "$MERGE_BASE" == "$UPSTREAM_SHA" ]]; then
  echo "status        : upstream only ahead (fast-forward)"
  echo "                action: 'git merge --ff-only $UPSTREAM_REF' (no reset required)"; exit 0
fi

AHEAD="$(git rev-list --count "$UPSTREAM_REF"..HEAD)"
BEHIND="$(git rev-list --count HEAD.."$UPSTREAM_REF")"
echo "status        : DIVERGED (both sides have unique commits)"
echo "ahead/behind  : $AHEAD / $BEHIND"
echo
echo "Plan: git reset -$RESET_MODE '$UPSTREAM_REF'"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] stopping before any change."; exit 0
fi

# ---- confirmation + backup -------------------------------------------------
BACKUP_REF="refs/backup/memo-rebase-$(date +%Y%m%d-%H%M%S)"
echo
echo "Backup ref (reversible): $BACKUP_REF  ->  $LOCAL_SHA"
read -r -p "Proceed with 'git reset -$RESET_MODE $UPSTREAM_REF'? [y/N] " answer
[[ "$answer" =~ ^[Yy]$ ]] || die "aborted by user"

git update-ref "$BACKUP_REF" "$LOCAL_SHA" || die "failed to create backup ref"
echo "backup saved -> $BACKUP_REF"

# ---- execute ---------------------------------------------------------------
git reset -$RESET_MODE "$UPSTREAM_REF"

# ---- verify ----------------------------------------------------------------
NEW_SHA="$(git rev-parse HEAD)"
[[ "$NEW_SHA" == "$UPSTREAM_SHA" ]] \
  || die "unexpected post-state: $NEW_SHA != $UPSTREAM_SHA"

if [[ -z "$(git status --porcelain)" ]]; then
  echo "post-state    : clean, HEAD == upstream ✓"
else
  echo "post-state    : HEAD==upstream but tree dirty — inspect manually"
fi

echo
echo "Done. Local branch '$BRANCH' now matches $UPSTREAM_REF."
echo "To undo this reset (recover original $LOCAL_SHA): git reset --hard $BACKUP_REF"
