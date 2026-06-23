[tasks]

Show progress while working.
Follow these instructions exactly.

0. Read:
   - `routing.md`
   - `skills/python-design/SKILL.md`
   - `skills/python-design/workflow.md`

1. Find files matching `plans/*_plan.md`.
   Do not read files under the `plans/done/` directory.
   If no matching files exist in `plans/` directory, stop.
   Sort the files by filename in ascending order.
   Select the first file as the target plan file.

2. Read the target plan file.
   Use `routing.md` to identify the target feature and the related implementation files.

3. For each item in `Implementation steps`, check whether it has already been implemented.
   If an item is not implemented, create a file-level implementation and test procedure document.
   `target_file_name` is the name of the file to implement and test.
   Create the document only.
   Do not implement anything.
   Save it as `implementations/{yyyymmdd-hhmmss}_{target_file_name}.md`.
   - `yyyymmdd-hhmmss` is the current date time.
   Write it in clear and concise English for AI understanding.
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

4. After the plan is complete, move the processed plan file to `plans/done` directory.

5. Create a Git commit.

6. Compress the current context immediately.

7. End the task.
