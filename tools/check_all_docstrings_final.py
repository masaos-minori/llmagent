import os
import re

scripts_dir = "/home/sugimoto/llmagent/scripts"
em_dash = "\u2014"  # —
issues = []

for root, dirs, files in os.walk(scripts_dir):
    for fname in files:
        if not fname.endswith(".py"):
            continue

        fpath = os.path.join(root, fname)
        relpath = os.path.relpath(fpath, scripts_dir)
        expected_prefix = f"scripts/{relpath}"

        try:
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            issues.append((fpath, "read error"))
            continue

        # Skip shebang line before looking for docstring
        search_content = content
        if search_content.startswith("#!"):
            search_content = search_content[search_content.find("\n") + 1 :]

        # Also skip 'from __future__' imports
        future_pattern = r"^\s*from\s+__future__\s+import\s+.+\n"
        while re.match(future_pattern, search_content):
            search_content = re.sub(future_pattern, "", search_content, count=1)

        # Find the module-level docstring (first triple-quote string)
        match = re.match(r'\s*"""(.*?)"""', search_content, re.DOTALL)
        if not match:
            issues.append((fpath, "no docstring"))
            continue

        docstring = match.group(1).strip()

        # Check format: should be "scripts/<path> — <description>"
        if em_dash not in docstring:
            issues.append((fpath, f"missing separator: '{docstring[:80]}'"))
            continue

        # Check path prefix
        if not docstring.startswith(expected_prefix):
            issues.append(
                (
                    fpath,
                    f"path mismatch: expected '{expected_prefix}', got '{docstring[:80]}'",
                )
            )
            continue

        # Check description is not empty after separator
        parts = docstring.split(em_dash)
        if len(parts) != 2 or not parts[1].strip():
            issues.append((fpath, f"empty description: '{docstring[:80]}'"))
            continue

        # Check description is reasonable length (> 3 chars)
        desc = parts[1].strip()
        if len(desc) < 4:
            issues.append((fpath, f"description too short: '{desc}'"))
            continue

if issues:
    print(f"ISSUES FOUND ({len(issues)}):")
    for fpath, issue in issues:
        print(f"  {fpath}: {issue}")
else:
    print("ALL OK - All docstrings follow the correct format.")
