#!/usr/bin/env python3
"""Remove mock_repo_state_snapshot_dynamic fixture and update tests to set _cfg.protected_branches directly."""

filepath = "/home/sugimoto/llmagent/tests/mcp_servers/git/test_git_security_compliance.py"

with open(filepath, "r") as f:
    lines = f.readlines()

# Find and remove the mock_repo_state_snapshot_dynamic fixture block
# It starts at "@pytest.fixture" followed by "def mock_repo_state_snapshot_dynamic"
# and ends before the next "@pytest.mark.asyncio" or another fixture
new_lines = []
skip_until_next_fixture_or_test = False
in_dynamic_fixture = False
brace_depth = 0

i = 0
while i < len(lines):
    line = lines[i]
    
    if '@pytest.fixture' in line and 'mock_repo_state_snapshot_dynamic' in lines[i+1]:
        # Skip this fixture entirely - find where it ends
        skip_until_next_fixture_or_test = True
        in_dynamic_fixture = True
        brace_depth = 0
        i += 1
        continue
    
    if skip_until_next_fixture_or_test:
        # Count braces to track nested function definitions
        for ch in line:
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
        
        # End of fixture: either we hit a new fixture/test decorator or braces are balanced
        if ('@pytest.fixture' in line or '@pytest.mark.asyncio' in line) and brace_depth <= 0:
            skip_until_next_fixture_or_test = False
            in_dynamic_fixture = False
            brace_depth = 0
            new_lines.append(line)
        i += 1
        continue
    
    # Remove mock_repo_state_snapshot_dynamic from test signatures
    if 'mock_repo_state_snapshot_dynamic,' in line:
        line = line.replace('mock_repo_state_snapshot_dynamic,', '').replace(', mock_repo_state_snapshot_dynamic', '')
    
    new_lines.append(line)
    i += 1

lines = new_lines

# Now add _cfg.protected_branches to denial tests
denial_tests = {
    'test_checkout_protected_branch_denied': ['main'],
    'test_pull_protected_branch_denied': ['master'],
    'test_push_protected_branch_denied': ['release'],
}

new_lines = []
current_test_name = None
for line in lines:
    # Track which test we're in
    if 'async def test_' in line:
        current_test_name = line.strip().split('(')[0].replace('async def ', '')
    
    # After setting allowed_repo_paths in denial tests, add protected_branches
    if current_test_name in denial_tests:
        branches = denial_tests[current_test_name]
        if 'server_service._allowed_repo_paths = ["/tmp/allowed"]' in line:
            new_lines.append(line)
            new_lines.append(f'        server_cfg.protected_branches = {branches!r}\n')
            continue
    
    new_lines.append(line)

with open(filepath, "w") as f:
    f.writelines(new_lines)

print("Done")
