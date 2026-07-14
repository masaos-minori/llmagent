#!/usr/bin/env python3
"""Fix D205: insert blank line after summary in triple-quoted strings/docstrings."""

from pathlib import Path


def fix_d205(content: str) -> tuple[str, list[int]]:
    """Insert blank line after the first line of triple-quoted docstrings."""
    lines = content.split("\n")
    fixed_lines = []
    changed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line starts a triple-quoted string (module-level docstring)
        # Pattern: starts with """ or ''' (possibly preceded by whitespace)
        stripped = line.lstrip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            quote_type = '"""' if stripped.startswith('"""') else "'''"

            # Find where the closing quotes end
            close_idx = stripped.find(quote_type, len(quote_type))

            if close_idx != -1:
                # Single-line triple-quoted string like """short doc"""
                # No blank line needed for single-line docstrings
                fixed_lines.append(line)
                i += 1
                continue

            # Multi-line docstring - find the closing quotes
            j = i + 1
            found_close = False
            while j < len(lines):
                next_line = lines[j].lstrip()
                if quote_type in next_line:
                    found_close = True
                    break
                j += 1

            if found_close:
                # Check if there's already a blank line after the opening
                # The opening line is lines[i], so we check lines[i+1]
                if i + 1 < len(lines) and lines[i + 1].strip() == "":
                    # Already has blank line, skip
                    for k in range(i, j + 1):
                        fixed_lines.append(lines[k])
                    i = j + 1
                    continue

                # Need to insert blank line after the opening line
                # But only if the next line is not already blank AND not part of SQL
                # Check if this looks like a SQL string literal (contains CREATE, INSERT, SELECT, etc.)
                sql_keywords = [
                    "CREATE ",
                    "INSERT ",
                    "SELECT ",
                    "DROP ",
                    "UPDATE ",
                    "DELETE ",
                ]
                is_sql = any(kw.upper() in line.upper() for kw in sql_keywords)

                if not is_sql:
                    fixed_lines.append(line)
                    fixed_lines.append("")  # Insert blank line
                    changed_lines.append(i + 1)  # Report as 1-indexed

                    # Now add the remaining lines of the docstring
                    for k in range(i + 1, j + 1):
                        fixed_lines.append(lines[k])
                    i = j + 1
                    continue
                else:
                    # Skip SQL string literals
                    for k in range(i, j + 1):
                        fixed_lines.append(lines[k])
                    i = j + 1
                    continue
            else:
                # No closing found, just append
                fixed_lines.append(line)
                i += 1
        else:
            fixed_lines.append(line)
            i += 1

    return "\n".join(fixed_lines), changed_lines


def main():
    scripts_dir = Path("/home/sugimoto/llmagent/scripts")
    total_fixed = 0

    for py_file in sorted(scripts_dir.rglob("*.py")):
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        new_content, changed = fix_d205(content)

        if changed:
            py_file.write_text(new_content, encoding="utf-8")
            total_fixed += len(changed)
            print(f"{py_file}: {len(changed)} fixes")

    print(f"\nTotal files modified: {total_fixed}")


if __name__ == "__main__":
    main()
