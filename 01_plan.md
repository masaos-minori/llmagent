[tasks]

Show progress while working.
Follow these steps strictly.

0. Read:
   - `routing.md`
   - `skills/python-issue-to-plan/SKILL.md`
   - `skills/python-issue-to-plan/workflow.md`

1. Search for files matching `requires/*_require.md`.
   Do not read files under the `done` directory.
   If there are no files in `requires/`, stop the task.
   Sort the matching files in ascending order by filename.
   Select the first file as the target requirement file and read it.

2. Create a work plan file.
   - The filename must be `plans/{%Y%m%d-%H%M%S}_plan.md`.
     - `%Y%m%d-%H%M%S` is the current date time.
   Create the plan only.
   Do not implement anything.
   Use the following section structure in the work plan:
   - Goal
   - Scope
   - Assumptions
   - Unknowns
   - Affected areas
   - Design
   - Implementation steps
   - Validation plan
   - Risks

3. Check `routing.md` to identify the source code files that would be modified.
   Read those files.

4. Analyze the `Unknowns` section in the work plan.
   Update the work plan with the analysis results.

5. If any `Unknowns` cannot be resolved through analysis, ask the user questions.
   Reflect the answers in the work plan.
   If any issues remain unresolved, output the result as a GitHub Issue Markdown template file.
   - The filename must be `issues/{%Y%m%d-%H%M%S}_issue.md`.
     - `%Y%m%d-%H%M%S` is the current date time.
   - 1 issue = 1 section

6. Analyze the `Risks` section in the work plan.
   Add any necessary mitigation steps to the work plan.
   If any issues remain unresolved, output the result as a GitHub Issue Markdown template file.
   - The filename must be `issues/{%Y%m%d-%H%M%S}_issue.md`.
     - `%Y%m%d-%H%M%S` is the current date time.
   - 1 issue = 1 section

7. After the work plan is complete, move the processed requirement file to `requires/done`.

8. Create a Git commit.

9. Compress the current context immediately.

10. End the task.
