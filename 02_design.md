[rules]

- `yyyymmdd` is the current date.
- `hhmmss` is the current time.
- `_nn_` is a sequential number.

[tasks]

Show progress while working.
Follow these instructions exactly.

1. Find files matching `plans/*_plan.md`.
   Do not read files under the `done` directory.
   If no matching files exist in `plans/`, stop.
   Sort the files by filename in ascending order.
   Select the first file as the target plan file.

2. Read the target plan file.
   Read `rules/coding.md`.
   Read `rules/toolchain.md`.
   Read `routing.md`.
   Use `routing.md` to identify the target feature and the related implementation files.

3. For each item in `Implementation steps`, check whether it has already been implemented.
   If an item is not implemented, create a file-level implementation and test procedure document.
   `target_file_name` is the name of the file to implement and test.
   Create the document only.
   Do not implement anything.
   Save it as `implementations/yyyymmdd-hhmmss_{target_file_name}.md`.
   Write it in clear and concise English for AI understanding.
   Use this section structure:
   - Goal
   - Scope
   - Assumptions
   - Implementation
   - Validation plan

4. Follow `skills/python-implementation/SKILL.md`.

5. After the plan is complete, move the processed plan file to `plan/done`.

6. Create a Git commit.

7. End the task.
