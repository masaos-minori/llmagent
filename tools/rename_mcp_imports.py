#!/usr/bin/env python3
"""Replace imports after MCP server file renaming."""

import re
import subprocess
import sys

DIRS = ["browser", "cicd", "file", "git", "github", "mdq", "rag_pipeline", "shell", "web_search"]
OLD_NAMES = ["models", "server", "service", "tools"]
NEW_PREFIXES = {
    "browser": "browser_",
    "cicd": "cicd_",
    "file": "file_",
    "git": "git_",
    "github": "github_",
    "mdq": "mdq_",
    "rag_pipeline": "rag_pipeline_",
    "shell": "shell_",
    "web_search": "web_search_",
}

def main():
    # Find all Python files with matching imports
    result = subprocess.run(
        ["rg", "-l", r"from mcp_servers\.[a-z_]+\.(models|server|service|tools) import"],
        capture_output=True, text=True, cwd="/home/sugimoto/llmagent"
    )
    
    if result.returncode != 0:
        print("No files found or rg error:", result.stderr)
        return
    
    files = result.stdout.strip().split("\n")
    files = [f for f in files if f]  # remove empty strings
    
    replaced_count = 0
    for filepath in files:
        full_path = f"/home/sugimoto/llmagent/{filepath}"
        try:
            content = open(full_path).read()
        except FileNotFoundError:
            continue
        
        original_content = content
        
        for d in DIRS:
            prefix = NEW_PREFIXES[d]
            for old_name in OLD_NAMES:
                # Replace "from mcp_servers.<dir>.<old_name> import" with "from mcp_servers.<dir>.<prefix><old_name> import"
                pattern = rf"(from mcp_servers\.{d}\.)({old_name} import)"
                replacement = rf"\g<1>{prefix}\2"
                content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(full_path, "w") as f:
                f.write(content)
            replaced_count += 1
            print(f"Updated: {filepath}")
    
    print(f"\nTotal files updated: {replaced_count}")

if __name__ == "__main__":
    main()
