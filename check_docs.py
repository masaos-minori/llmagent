import os
import re


def check_docs():
    docs_dir = "docs"
    # Match scripts/mcp_servers/.../*.py
    path_pattern = re.compile(r"scripts/mcp_servers/[^ \)\(\`]+\.py")
    errors = []

    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                with open(filepath, encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        matches = path_pattern.findall(line)
                        for match in matches:
                            # Clean up trailing punctuation often found in sentences
                            clean_match = match.rstrip(".,;)]}")
                            if not os.path.exists(clean_match):
                                # Ignore templates
                                if "<" not in clean_match and "*" not in clean_match:
                                    errors.append((filepath, i + 1, clean_match))
    return errors


if __name__ == "__main__":
    errs = check_docs()
    if errs:
        print("Mismatched files found:")
        for doc, line_no, target in errs:
            print(f"{doc}:{line_no}: {target}")
    else:
        print("No mismatches found.")
