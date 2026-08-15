file_path = "tests/rag/ingestion/test_rag_ingester.py"

replacements = {
    879: "(123, False, True)",
    935: "(None, False, False)",
    987: "(123, False, True)",
    1049: "(123, True, False)",
    1084: "(None, False, False)",
    1133: "(None, False, False)",
}

with open(file_path) as f:
    lines = f.readlines()

for line_num, new_val in replacements.items():
    idx = line_num - 1
    if idx < len(lines):
        # We want to replace only the part after '='
        line = lines[idx]
        if "=" in line:
            parts = line.split("=", 1)
            prefix = parts[0]
            lines[idx] = f"{prefix}= {new_val}\n"
        else:
            print(f"Warning: line {line_num} does not contain '='")
    else:
        print(f"Warning: line {line_num} is out of bounds")

with open(file_path, "w") as f:
    f.writelines(lines)

print("Replacements completed.")
