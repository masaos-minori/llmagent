import os
import re


def contains_japanese(text):
    # Regex for Hiragana, Katakana, and common Kanji ranges
    japanese_pattern = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]")
    return bool(japanese_pattern.search(text))


def main():
    target_dir = "docs/"
    if not os.path.exists(target_dir):
        print(f"Directory {target_dir} does not exist.")
        return

    japanese_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        if contains_japanese(content):
                            japanese_files.append(file_path)
                except OSError as e:
                    print(f"Error reading {file_path}: {e}")

    if japanese_files:
        print("Files containing Japanese characters:")
        for f in japanese_files:
            print(f)
    else:
        print("No Japanese files found.")


if __name__ == "__main__":
    main()
