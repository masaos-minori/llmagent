[rules]

- In each filename, `yyyymmdd` represents the current date.
- In each filename, `hhmmss` represents the current time.
- In each filename, `_nn_` represents a sequential number.

[tasks]

Show progress while working.
Follow these instructions exactly.

1. Search for files matching `plans/*_plan.md`.
   If there are no matching files in `plans/`, stop the task.
   Sort the matching files in ascending order by filename.
   Select the first file as the target plan file.

2. Read the target plan file.
   Read `rules/coding.md`.
   Read `rules/toolchain.md`.
   Read `routing.md`.
   Use `routing.md` to identify the target feature and the related implementation files.

3. For each item in `Implementation steps`, determine whether it has already been implemented.
   If an item has not been implemented, create a file-level implementation and test procedure document.
   Create the implementation and test procedure document only.
   Do not implement anything.
   Save it as `implementations/yyyymmdd-hhmmss_{target_file_name}.md`.
   Write the document in clear and concise English that an AI can understand easily.
   Use the following section structure:
   - Goal
   - Scope
   - Assumptions
   - Implementation
   - Validation plan

4. Follow:
   - `skills/python-implementation/SKILL.md`

5. After the plan is complete, move the processed plan file to `plans/done`.
