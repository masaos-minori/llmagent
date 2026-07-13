#!/usr/bin/env python3
"""Fix remaining D205: add blank line after docstring summary lines."""

import os


def fix_d205(filepath):
    """Add blank line after docstring summary line if missing."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception:
        return False

    lines = content.split("\n")
    new_lines = []
    i = 0
    fixed = False

    while i < len(lines):
        new_lines.append(lines[i])

        # Check if this line starts a docstring
        stripped = lines[i].strip()
        if stripped.startswith('"""'):
            # Single-line docstring - no issue
            if '"""' in stripped and stripped.count('"""') >= 2:
                i += 1
                continue

            # Multi-line docstring - find closing
            j = i + 1
            while j < len(lines):
                if '"""' in lines[j]:
                    break
                j += 1

            if j >= len(lines):
                # Unclosed docstring - skip
                i += 1
                continue

            # Found closing on line j
            # Check if line right after opening has blank line before description
            # This handles both module-level and class/function docstrings
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next line is NOT blank AND doesn't start with """ (closing), add blank line
                if next_line.strip() and not next_line.strip().startswith('"""'):
                    # Need to insert blank line after opening line
                    new_lines.insert(i + 1, "")
                    fixed = True

            i = j + 1
            continue

        i += 1

    if fixed:
        new_content = "\n".join(new_lines)
        with open(filepath, "w") as f:
            f.write(new_content)

    return fixed


if __name__ == "__main__":
    count = 0
    for root, dirs, files in os.walk("scripts"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            if fix_d205(filepath):
                count += 1
    print(f"Fixed {count} files")
