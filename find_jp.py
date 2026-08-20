import os
import re


def find_japanese_files(directory):
    jp_pattern = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]")
    jp_files = []

    if not os.path.exists(directory):
        return []

    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, encoding="utf-8", errors="ignore") as file:
                    if jp_pattern.search(file.read()):
                        jp_files.append(filename)
            except OSError:
                pass

    return jp_files


if __name__ == "__main__":
    jp_files = find_japanese_files("docs")
    for f in jp_files:
        print(f)
