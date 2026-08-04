import os


def check_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    first_separator = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if i > 0:
                first_separator = i
                break

    if first_separator == -1:
        return False

    matches = []
    for i, line in enumerate(lines):
        if "01_overview.md" in line:
            matches.append(i)

    if not matches:
        return False

    found_in_frontmatter = False
    found_in_body = False

    for idx in matches:
        # Check if in frontmatter
        if idx < first_separator:
            # Check if it's under 'related:'
            for j in range(idx, 0, -1):
                if "related:" in lines[j]:
                    found_in_frontmatter = True
                    break
                if lines[j].strip() == "---":
                    break

        # Check if in body
        else:
            # Check if it's under '## Related Documents'
            # We search upwards from the match to find the nearest heading
            for j in range(idx, first_separator, -1):
                if "## Related Documents" in lines[j]:
                    found_in_body = True
                    break
                if lines[j].strip().startswith("#"):
                    break

            # Also check if it's under a 'Related Documents' section that might be AFTER it?
            # No, usually the link is IN the section.

            # Wait, what if the match IS the header? Unlikely.
            # What if the section is defined by '## Related Documents' and the match is below it?
            # The loop above does exactly that: searches upwards from idx to first_separator.

    return found_in_frontmatter and found_in_body


target_files = [
    "docs/01_overview-arch-01-process.md",
    "docs/01_overview-arch-02-pipelines.md",
    "docs/01_overview-arch-03-features.md",
    "docs/01_overview-files-01-build.md",
    "docs/01_overview-files-02-rag.md",
    "docs/01_overview-files-03-scripts-part1.md",
    "docs/01_overview-files-03-scripts-part2.md",
    "docs/01_overview-files-03-scripts-part3.md",
    "docs/01_overview-files-03-scripts-part4.md",
    "docs/01_overview-files-03-scripts-part5.md",
    "docs/01_overview-files-04-shared-part1.md",
    "docs/01_overview-files-04-shared-part2.md",
    "docs/01_overview-files-05-config.md",
    "docs/01_overview-files-06-misc.md",
]

for f in target_files:
    if os.path.exists(f):
        if check_file(f):
            print(f"{f}: DUPLICATED")
        else:
            print(f"{f}: OK")
