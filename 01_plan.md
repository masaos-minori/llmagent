[rules]

- `yyyymmdd` is the current date.
- `hhmmss` is the current time.
- `_nn_` is a sequential number.

[tasks]

Show progress while working.
Follow these steps strictly.

1. Search for files matching `~/llmagent/requires/*_require.md`.
   Do not read files under the `done` directory.
   If there are no files in `~/llmagent/requires/`, stop the task.
   Sort the matching files in ascending order by filename.
   Select the first file as the target instruction file and read it.

2. Create a work plan file.
   - The filename must be `~/llmagent/plans/yyyymmdd-hhmmss_plan.md`.
   Create the plan only.
   Do not implement anything.
   Read:
   - `~/llmagent/skills/python-issue-to-plan/SKILL.md`
   - `~/llmagent/skills/python-issue-to-plan/workflow.md`
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

3. Check `~/llmagent/routing.md` to identify the source code files that would be modified.
   Read those files.

4. Analyze the `Unknowns` section in the work plan.
   Update the work plan with the analysis results.

5. If any `Unknowns` cannot be resolved through analysis, ask the user questions.
   Reflect the answers in the work plan.
   If any issues remain unresolved, write them to `~/llmagent/issues/yyyyymmdd-hhmmss.md`.

6. Analyze the `Risks` section in the work plan.
   Add any necessary mitigation steps to the work plan.
   If any issues remain unresolved, write them to `~/llmagent/issues/yyyyymmdd-hhmmss.md`.

7. After the work plan is complete, move the processed instruction file to `~/llmagent/requires/done`.

8. Create the necessary directories for the implementation.

9. Create a Git commit.

10. End the task.
