import os


def check_path(path):
    if not path:
        return None

    # Clean up path
    path = path.strip()
    if path.startswith("/") or path.startswith("./"):
        path = path[1:]

    # Try exact match
    if os.path.exists(path):
        return path

    # Common prefixes used in this project
    prefixes = [
        "scripts/",
        "agent/",
        "docs/",
        "tests/",
        "requires/",
        "plans/",
        "rules/",
        "skills/",
    ]
    for prefix in prefixes:
        test_path = prefix + path
        if os.path.exists(test_path):
            return test_path

        # Also try replacing . with / for module notation
        test_path_mod = prefix + path.replace(".", "/")
        if os.path.exists(test_path_mod):
            return test_path_mod
        if not test_path_mod.endswith(".py"):
            test_path_mod += ".py"
        if os.path.exists(test_path_mod):
            return test_path_mod

    # Handle dotted notation specifically for modules
    for prefix in ["scripts/", "agent/"]:
        test_path = prefix + path.replace(".", "/")
        if os.path.exists(test_path):
            return test_path
        if not test_path.endswith(".py"):
            test_path += ".py"
        if os.path.exists(test_path):
            return test_path

    return None


def main():
    with open("potential_paths.txt") as f:
        lines = f.readlines()

    mismatches = []
    for line in lines:
        parts = line.split(":")
        if len(parts) < 3:
            continue
        doc_file = parts[0]
        line_num = parts[1]
        extracted = parts[2].strip()

        # Skip things that are clearly not file paths
        if (
            extracted.startswith("[")
            or extracted.startswith("{")
            or extracted.startswith('"')
            or extracted.startswith("'")
        ):
            continue

        is_mcp_module = "mcp_servers." in extracted
        is_py_file = extracted.endswith(".py")

        if not (is_mcp_module or is_py_file):
            continue

        actual_path = check_path(extracted)
        if not actual_path:
            mismatches.append((doc_file, line_num, extracted))
        elif (
            actual_path != extracted
            and not extracted.startswith(actual_path)
            and not actual_path.startswith(extracted)
        ):
            # It found something, but it's different. This might be a real mismatch or just a prefix issue.
            # If the difference is just a common prefix, we might consider it "found" but note it?
            # For simplicity, let's only report if it's truly NOT found by any reasonable means.
            pass

    print(f"Found {len(mismatches)} potential mismatches.")
    for m in mismatches:
        print(f"{m[0]}:{m[1]} -> {m[2]}")


if __name__ == "__main__":
    main()
