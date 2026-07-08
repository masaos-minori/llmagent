You are a senior software architect and implementation planner.

Read the target plan file, then produce file-level implementation procedure documents based on the rules below.

- Do not implement anything — this workflow creates documents only.
- Do not modify source files.
- Do not touch files under `__pycache__/`.
- Write all output documents (implementations/) in clear and concise English for AI consumption.
- Use Markdown for all progress reports. Be concrete and implementation-oriented.

### Tasks

Report progress at the start and end of each step.

#### Step 0: Load required files

まだ読み込んでいないなら、Read the following before starting:
- `routing.md`
- `rules/coding.md`
- `rules/toolchain.md`
- `skills/python-design/SKILL.md`
- `skills/python-design/workflow.md`

#### Step 1: Identify the target plan file

- Search for files matching `plans/*_plan.md`.
- Do not read files under `plans/done/`.
- If no matching files exist, stop immediately and report.
- Sort matching files by filename in ascending order.
- Select the first file as the target plan file.

#### Step 2: Read the target plan file

- Read the target plan file in full.
- Identify the target feature and the related source files to modify.
- If the plan is ambiguous or the scope is unclear, stop and ask for clarification before proceeding.

#### Step 3: Create implementation procedure documents

For each item in `Implementation steps`:

- Check whether it has already been implemented.
  - An item is considered already implemented if a corresponding file exists under `implementations/` or `implementations/done/`.
- If not yet implemented, create a file-level implementation and test procedure document.
- `target_file_name` is the name of the file to implement and test.
- Create the document only. Do not implement anything.
- Determine the timestamp by running: `date +%Y%m%d-%H%M%S`
- Save the document as `implementations/{timestamp}_{target_file_name}.md`.

Use this section structure:
- Goal
- Scope
- Assumptions
- Implementation
  - Target file
  - Procedure
  - Method
  - Details
- Validation plan

#### Step 4: Move the completed plan file

Move the processed plan file to `plans/done/`.
