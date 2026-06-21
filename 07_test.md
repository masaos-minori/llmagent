[tasks]

Show progress while working.
Follow these instructions exactly.

1. Find files matching `~/llmagent/plans/*_plan.md`.
   Do not read files under the `~/llmagent/plans/done/` directory.
   If no matching files exist in `~/llmagent/plans/`, stop.
   Sort the files by filename in ascending order.
   Select the first file as the target plan file.

2. Read the target plan file.
   Read `~/llmagent/rules/coding.md`.
   Read `~/llmagent/rules/toolchain.md`.
   Read `~/llmagent/routing.md`.
   Use `routing.md` to identify the target feature and the related implementation files.

3. For each item in `Implementation steps`, check whether it has already been implemented.
   If an item is not implemented, create a file-level implementation and test procedure document.
   `target_file_name` is the name of the file to implement and test.
   Create the document only.
   Do not implement anything.
   Save it as `~/llmagent/implementations/yyyymmdd-hhmmss_{target_file_name}.md`.
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

4. Follow `~/llmagent/skills/python-implementation/SKILL.md`.

5. After the plan is complete, move the processed plan file to `~/llmagent/plans/done`.

6. Create a Git commit.

7. Compress the current context immediately.

8. End the task.

すべてのテストケースを実行し、テストが失敗するケースを洗い出し、「GitHub Issue Markdown テンプレート形式(1 issue = 1 task)」のファイルを /issues フォルダに 1 issue ごとに `yyyymmdd-hhmmss_issues.md` ファイルを出力
