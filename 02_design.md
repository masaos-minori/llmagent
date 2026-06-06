[rules]

- Use the current date for `yyyymmdd`.
- Use the current time for `hhmmss`.
- Use a sequential number for `_nn_`.

[tasks]

Show progress while working.
Follow these instructions exactly.

1. Search for files matching `plans/yyyymmdd_hhmmss_plan.md`.
   Sort the matching files by filename in ascending order.
   Use the first file as the target plan file.
   If there are no matching files in `plans/`, stop immediately.

2. Read the target plan file.
   Read `rules/coding.md`.
   Read `rules/toolchain.md`.
   Read `routing.md`.
   Use `routing.md` to identify the target feature and the related implementation files.

3. For each item in `Implementation steps`, determine whether it has already been implemented.
   If an item is not implemented, create a file-level implementation and test procedure document.
   Save it as `implementations/yyyymmdd-hhmmss_{target_file_name}.md`.
   Write the document in clear and concise English for AI understanding.
   Use this section structure:
   - Goal
   - Scope
   - Assumptions
   - Implementation
   - Validation plan
   Follow:
   - `skills/python-implementation/SKILL.md`
