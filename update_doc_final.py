import re


def update_doc():
    file_path = "docs/04_mcp_03_02_tool-registry.md"
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # 1. Replace section 47-59
    # We look for the header and then everything until the next blank line after the paragraph.
    pattern_section = r"### 新しいツールの追加.*?\n\n(?=\n|\n\n|###)"
    replacement_section = """### 新しいツールの追加
詳細な手順は [Adding a new tool](docs/04_mcp_03_05_lifecycle-and-new-server.md#adding-a-new-tool) を参照してください。なお、`config` の `tool_names` はルーティングの入力ではなく、あくまでドリフト検証用のメタデータです."""

    # If the regex doesn't match, we try a simpler one
    if not re.search(pattern_section, content, re.DOTALL):
        # Fallback: find the header and the next double newline
        pattern_section = r"### 新しいツールの追加.*?(\*\*推奨手順\*\*.*?\n)?"
        content = re.sub(
            pattern_section, replacement_section + "\n\n", content, flags=re.DOTALL
        )
    else:
        content = re.sub(
            pattern_section, replacement_section + "\n\n", content, flags=re.DOTALL
        )

    # 2. Update _SIDE_EFFECT_TOOLS
    old_side_effects = """_SIDE_EFFECT_TOOLS = (
    WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
)"""
    new_side_effects = """_SIDE_EFFECT_TOOLS = (
    WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
    | CICD_WRITE_TOOLS | RAG_WRITE_TOOLS | MDQ_WRITE_TOOLS
)"""
    content = content.replace(old_side_effects, new_side_effects)

    # 3. Update prose note
    old_prose = "（注: `_SIDE_EFFECT_TOOLS` は `WRITE_TOOLS` / `DELETE_TOOLS` / `shell_run` に加え、Git 書き込み系（`GIT_WRITE_TOOLS`）と GitHub 書き込み・危険操作系（`GITHUB_WRITE_TOOLS`、`GITHUB_DANGEROUS_TOOLS`）も含む。Explicit in code: `shared/tool_executor_helpers.py`。）"
    new_prose = "（注: `_SIDE_EFFECT_TOOLS` は `WRITE_TOOLS` / `DELETE_TOOLS` / `shell_run` に加え、Git 書き込み系（`GIT_WRITE_TOOLS`）、GitHub 書き込み・危険操作系（`GITHUB_WRITE_TOOLS`、`GITHUB_DANGEROUS_TOOLS`）、および CICD/RAG/MDQ 書き込み系（`CICD_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `MDQ_WRITE_TOOLS`）も含む。Explicit in code: `shared/tool_executor_helpers.py`。）"
    content = content.replace(old_prose, new_prose)

    with open(file_path + ".tmp", "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    update_doc()
