[tasks]

Show progress while working.
Follow these instructions exactly.

0. Read `routing.md`.
   Read `rules/coding.md`.
   Read `rules/toolchain.md`.

1. Search for files matching `implementations/*.md`.
   Do not read files under the `implementations/done` directory.
   If there are no matching files in `implementations/`, stop the task.
   Sort the matching files by filename in ascending order.
   Use the first file as the target implementation file.
   If there are no matching files in `implementations/`, stop immediately.

2. Read the target plan file.
   Use `routing.md` to identify the target feature and the related implementation file.

3. Implement the feature according to the implementation document.
   Follow:
   - `skills/python-implementation/SKILL.md`
   - `skills/python-lint-typecheck/SKILL.md`

4. Test the feature according to the implementation procedure document.
   If test coverage is insufficient, add the required test cases and test programs.
   Repeat until all tests pass.
   Follow:
   - `skills/python-test-and-fix/SKILL.md`
   - `skills/python-debug-root-cause/SKILL.md`

5. After implementation and testing are complete, move the completed implementation procedure document to `implementations/done/` directory.

6. Update `docs/*.md` for every changed file.

7. Create a Git commit.

8. Compress the current context immediately.

9. End the task.
