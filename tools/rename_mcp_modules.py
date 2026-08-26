#!/usr/bin/env python3
"""Rename module references across the codebase after file renames."""

import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent

# Old -> new mappings for absolute module paths per server
SERVER_MODULE_RENAMES = {
    "cicd": [
        ("mcp_servers.cicd.service_business", "mcp_servers.cicd.cicd_service_business"),
        ("mcp_servers.cicd.service_defs", "mcp_servers.cicd.cicd_service_defs"),
        (
            "mcp_servers.cicd.service_github_actions",
            "mcp_servers.cicd.cicd_service_github_actions",
        ),
        (
            "mcp_servers.cicd.service_github_actions_composite",
            "mcp_servers.cicd.cicd_service_github_actions_composite",
        ),
        (
            "mcp_servers.cicd.service_github_actions_job",
            "mcp_servers.cicd.cicd_service_github_actions_job",
        ),
        ("mcp_servers.cicd.service_guards", "mcp_servers.cicd.cicd_service_guards"),
        ("mcp_servers.cicd.service_init", "mcp_servers.cicd.cicd_service_init"),
    ],
    "github": [
        ("mcp_servers.github.models_base", "mcp_servers.github.github_models_base"),
        ("mcp_servers.github.models_config", "mcp_servers.github.github_models_config"),
        ("mcp_servers.github.models_file", "mcp_servers.github.github_models_file"),
        ("mcp_servers.github.models_issues", "mcp_servers.github.github_models_issues"),
        (
            "mcp_servers.github.models_pull_requests",
            "mcp_servers.github.github_models_pull_requests",
        ),
        (
            "mcp_servers.github.models_repository",
            "mcp_servers.github.github_models_repository",
        ),
        ("mcp_servers.github.server_common", "mcp_servers.github.github_server_common"),
        ("mcp_servers.github.server_file", "mcp_servers.github.github_server_file"),
        ("mcp_servers.github.server_issues", "mcp_servers.github.github_server_issues"),
        (
            "mcp_servers.github.server_pull_requests",
            "mcp_servers.github.github_server_pull_requests",
        ),
        (
            "mcp_servers.github.server_repository",
            "mcp_servers.github.github_server_repository",
        ),
        (
            "mcp_servers.github.service_business",
            "mcp_servers.github.github_service_business",
        ),
        (
            "mcp_servers.github.service_dispatch",
            "mcp_servers.github.github_service_dispatch",
        ),
        ("mcp_servers.github.service_file", "mcp_servers.github.github_service_file"),
        ("mcp_servers.github.service_init", "mcp_servers.github.github_service_init"),
        (
            "mcp_servers.github.service_issues",
            "mcp_servers.github.github_service_issues",
        ),
        (
            "mcp_servers.github.service_pull_requests",
            "mcp_servers.github.github_service_pull_requests",
        ),
        (
            "mcp_servers.github.service_repository",
            "mcp_servers.github.github_service_repository",
        ),
        (
            "mcp_servers.github.service_security",
            "mcp_servers.github.github_service_security",
        ),
    ],
    "shell": [
        (
            "mcp_servers.shell.service_static_helpers",
            "mcp_servers.shell.shell_service_static_helpers",
        ),
    ],
}

# Old -> new mappings for local path docstrings per server
SERVER_DOCSTRING_PATH_RENAMES = {
    "cicd": [
        (
            "scripts/mcp_servers/cicd/service_business.py",
            "scripts/mcp_servers/cicd/cicd_service_business.py",
        ),
        (
            "scripts/mcp_servers/cicd/service_defs.py",
            "scripts/mcp_servers/cicd/cicd_service_defs.py",
        ),
        (
            "scripts/mcp_servers/cicd/service_github_actions.py",
            "scripts/mcp_servers/cicd/cicd_service_github_actions.py",
        ),
        (
            "scripts/mcp_servers/cicd/service_github_actions_composite.py",
            "scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py",
        ),
        (
            "scripts/mcp_servers/cicd/service_github_actions_job.py",
            "scripts/mcp_servers/cicd/cicd_service_github_actions_job.py",
        ),
        (
            "scripts/mcp_servers/cicd/service_guards.py",
            "scripts/mcp_servers/cicd/cicd_service_guards.py",
        ),
        (
            "scripts/mcp_servers/cicd/service_init.py",
            "scripts/mcp_servers/cicd/cicd_service_init.py",
        ),
    ],
    "github": [
        (
            "scripts/mcp_servers/github/models_base.py",
            "scripts/mcp_servers/github/github_models_base.py",
        ),
        (
            "scripts/mcp_servers/github/models_config.py",
            "scripts/mcp_servers/github/github_models_config.py",
        ),
        (
            "scripts/mcp_servers/github/models_file.py",
            "scripts/mcp_servers/github/github_models_file.py",
        ),
        (
            "scripts/mcp_servers/github/models_issues.py",
            "scripts/mcp_servers/github/github_models_issues.py",
        ),
        (
            "scripts/mcp_servers/github/models_pull_requests.py",
            "scripts/mcp_servers/github/github_models_pull_requests.py",
        ),
        (
            "scripts/mcp_servers/github/models_repository.py",
            "scripts/mcp_servers/github/github_models_repository.py",
        ),
        (
            "scripts/mcp_servers/github/server_common.py",
            "scripts/mcp_servers/github/github_server_common.py",
        ),
        (
            "scripts/mcp_servers/github/server_file.py",
            "scripts/mcp_servers/github/github_server_file.py",
        ),
        (
            "scripts/mcp_servers/github/server_issues.py",
            "scripts/mcp_servers/github/github_server_issues.py",
        ),
        (
            "scripts/mcp_servers/github/server_pull_requests.py",
            "scripts/mcp_servers/github/github_server_pull_requests.py",
        ),
        (
            "scripts/mcp_servers/github/server_repository.py",
            "scripts/mcp_servers/github/github_server_repository.py",
        ),
        (
            "scripts/mcp_servers/github/service_business.py",
            "scripts/mcp_servers/github/github_service_business.py",
        ),
        (
            "scripts/mcp_servers/github/service_dispatch.py",
            "scripts/mcp_servers/github/github_service_dispatch.py",
        ),
        (
            "scripts/mcp_servers/github/service_file.py",
            "scripts/mcp_servers/github/github_service_file.py",
        ),
        (
            "scripts/mcp_servers/github/service_init.py",
            "scripts/mcp_servers/github/github_service_init.py",
        ),
        (
            "scripts/mcp_servers/github/service_issues.py",
            "scripts/mcp_servers/github/github_service_issues.py",
        ),
        (
            "scripts/mcp_servers/github/service_pull_requests.py",
            "scripts/mcp_servers/github/github_service_pull_requests.py",
        ),
        (
            "scripts/mcp_servers/github/service_repository.py",
            "scripts/mcp_servers/github/github_service_repository.py",
        ),
        (
            "scripts/mcp_servers/github/service_security.py",
            "scripts/mcp_servers/github/github_service_security.py",
        ),
    ],
    "shell": [
        (
            "scripts/mcp_servers/shell/service_static_helpers.py",
            "scripts/mcp_servers/shell/shell_service_static_helpers.py",
        ),
    ],
}

# Relative import renames per server (file must be under that server's dir)
SERVER_RELATIVE_IMPORT_RENAMES = {
    "cicd": [
        (".service_business", ".cicd_service_business"),
        (".service_defs", ".cicd_service_defs"),
        (".service_github_actions", ".cicd_service_github_actions"),
        (".service_github_actions_composite", ".cicd_service_github_actions_composite"),
        (".service_github_actions_job", ".cicd_service_github_actions_job"),
        (".service_guards", ".cicd_service_guards"),
        (".service_init", ".cicd_service_init"),
    ],
    "github": [
        (".models_base", ".github_models_base"),
        (".models_config", ".github_models_config"),
        (".models_file", ".github_models_file"),
        (".models_issues", ".github_models_issues"),
        (".models_pull_requests", ".github_models_pull_requests"),
        (".models_repository", ".github_models_repository"),
        (".server_common", ".github_server_common"),
        (".server_file", ".github_server_file"),
        (".server_issues", ".github_server_issues"),
        (".server_pull_requests", ".github_server_pull_requests"),
        (".server_repository", ".github_server_repository"),
        (".service_business", ".github_service_business"),
        (".service_dispatch", ".github_service_dispatch"),
        (".service_file", ".github_service_file"),
        (".service_init", ".github_service_init"),
        (".service_issues", ".github_service_issues"),
        (".service_pull_requests", ".github_service_pull_requests"),
        (".service_repository", ".github_service_repository"),
        (".service_security", ".github_service_security"),
    ],
    "shell": [
        (".service_static_helpers", ".shell_service_static_helpers"),
    ],
}

# patch() target string replacements (module path inside strings)
PATCH_TARGET_RENAMES = [
    # cicd
    ("mcp_servers.cicd.service_business", "mcp_servers.cicd.cicd_service_business"),
    ("mcp_servers.cicd.service_defs", "mcp_servers.cicd.cicd_service_defs"),
    (
        "mcp_servers.cicd.service_github_actions",
        "mcp_servers.cicd.cicd_service_github_actions",
    ),
    (
        "mcp_servers.cicd.service_github_actions_composite",
        "mcp_servers.cicd.cicd_service_github_actions_composite",
    ),
    (
        "mcp_servers.cicd.service_github_actions_job",
        "mcp_servers.cicd.cicd_service_github_actions_job",
    ),
    ("mcp_servers.cicd.service_guards", "mcp_servers.cicd.cicd_service_guards"),
    ("mcp_servers.cicd.service_init", "mcp_servers.cicd.cicd_service_init"),
    # github
    ("mcp_servers.github.models_base", "mcp_servers.github.github_models_base"),
    ("mcp_servers.github.models_config", "mcp_servers.github.github_models_config"),
    ("mcp_servers.github.models_file", "mcp_servers.github.github_models_file"),
    ("mcp_servers.github.models_issues", "mcp_servers.github.github_models_issues"),
    (
        "mcp_servers.github.models_pull_requests",
        "mcp_servers.github.github_models_pull_requests",
    ),
    (
        "mcp_servers.github.models_repository",
        "mcp_servers.github.github_models_repository",
    ),
    ("mcp_servers.github.server_common", "mcp_servers.github.github_server_common"),
    ("mcp_servers.github.server_file", "mcp_servers.github.github_server_file"),
    ("mcp_servers.github.server_issues", "mcp_servers.github.github_server_issues"),
    (
        "mcp_servers.github.server_pull_requests",
        "mcp_servers.github.github_server_pull_requests",
    ),
    (
        "mcp_servers.github.server_repository",
        "mcp_servers.github.github_server_repository",
    ),
    (
        "mcp_servers.github.service_business",
        "mcp_servers.github.github_service_business",
    ),
    (
        "mcp_servers.github.service_dispatch",
        "mcp_servers.github.github_service_dispatch",
    ),
    ("mcp_servers.github.service_file", "mcp_servers.github.github_service_file"),
    ("mcp_servers.github.service_init", "mcp_servers.github.github_service_init"),
    ("mcp_servers.github.service_issues", "mcp_servers.github.github_service_issues"),
    (
        "mcp_servers.github.service_pull_requests",
        "mcp_servers.github.github_service_pull_requests",
    ),
    (
        "mcp_servers.github.service_repository",
        "mcp_servers.github.github_service_repository",
    ),
    (
        "mcp_servers.github.service_security",
        "mcp_servers.github.github_service_security",
    ),
    # shell
    (
        "mcp_servers.shell.service_static_helpers",
        "mcp_servers.shell.shell_service_static_helpers",
    ),
]


def get_server(path: pathlib.Path) -> str | None:
    """Determine which server a file belongs to based on its path."""
    parts = path.parts
    # Look for mcp_servers/<server>/ pattern
    for i, part in enumerate(parts):
        if part == "mcp_servers" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def update_docstring_path(content: str, server: str) -> tuple[str, bool]:
    """Update file path references in docstrings for a specific server."""
    changed = False
    renames = SERVER_DOCSTRING_PATH_RENAMES.get(server, [])
    for old, new in renames:
        if old in content and new not in content:
            content = content.replace(old, new)
            changed = True
    return content, changed


def update_imports(content: str, server: str) -> tuple[str, bool]:
    """Update import statements for a specific server."""
    changed = False

    # Update absolute imports: from mcp_servers.xxx.yyy import ...
    # Also handles: import mcp_servers.xxx.yyy as alias
    renames = SERVER_MODULE_RENAMES.get(server, [])
    for old_mod, new_mod in renames:
        escaped_old = re.escape(old_mod)

        # Pattern: from <module> import ...
        pattern_from = rf"(from\s+){escaped_old}(\s+import)"
        if re.search(pattern_from, content):
            content = re.sub(pattern_from, r"\1" + new_mod + r"\2", content)
            changed = True

        # Pattern: import <module> [as alias]
        pattern_import = rf"(^|\s|,)import\s+{escaped_old}\b(\s+as\b|$)"
        if re.search(pattern_import, content):
            content = re.sub(pattern_import, r"\1import " + new_mod + r"\2", content)
            changed = True

    # Update relative imports: from .xxx import ...
    rel_renames = SERVER_RELATIVE_IMPORT_RENAMES.get(server, [])
    for old_rel, new_rel in rel_renames:
        # Match 'from .old_module' but not 'from .old_module_something_else'
        pattern = rf"(from\s+){re.escape(old_rel)}(\s+import|\b)"
        if re.search(pattern, content):
            content = re.sub(pattern, r"\1" + new_rel + r"\2", content)
            changed = True

    return content, changed


def update_patch_targets(content: str) -> tuple[str, bool]:
    """Update module paths inside patch() targets and logger names."""
    changed = False
    for old, new in PATCH_TARGET_RENAMES:
        if old in content:
            content = content.replace(old, new)
            changed = True
    return content, changed


def main() -> None:
    if not BASE.is_dir():
        print(f"ERROR: repository root not found: {BASE}", file=sys.stderr)
        sys.exit(1)

    dirs_to_process = [
        BASE / "scripts",
        BASE / "tests",
        BASE / "mutants",
        BASE / "implementations",
        BASE / "plans",
        BASE / "requires",
    ]

    total_files = 0
    updated_files = 0

    for d in dirs_to_process:
        if not d.exists():
            print(f"ERROR: expected directory not found: {d}", file=sys.stderr)
            sys.exit(1)

        py_files = sorted(d.rglob("*.py"))
        for f in py_files:
            total_files += 1
            old_content = f.read_text(encoding="utf-8")

            server = get_server(f)
            content = old_content

            # Update docstring paths and imports for files under mcp_servers/<server>/
            if server is not None and server in SERVER_MODULE_RENAMES:
                content, ds_changed = update_docstring_path(content, server)
                content, imp_changed = update_imports(content, server)
            else:
                ds_changed = False
                imp_changed = False

            # Always update patch targets for all files
            content, patch_changed = update_patch_targets(content)

            if content != old_content:
                f.write_text(content, encoding="utf-8")
                updated_files += 1
                changes = []
                if ds_changed:
                    changes.append("docstring")
                if imp_changed:
                    changes.append("imports")
                if patch_changed:
                    changes.append("patch")
                rel = f.relative_to(BASE)
                print(f"  UPDATED {rel} ({', '.join(changes)})")

    print(f"\nDone. Updated {updated_files}/{total_files} files.")


if __name__ == "__main__":
    main()
