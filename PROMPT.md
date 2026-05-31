# Ralph Loop: Keep on the Borderlands MUD

You are building this project iteratively. Each invocation, do ONE task.

## Workflow
1. Read /docs/specs/ to understand the architecture
2. Read /tasks.md and pick the first unchecked task
3. If the task requires a spec that doesn't exist, write the spec first
   in /docs/specs/<system>.md and stop. Mark task progress, commit, exit.
4. If the spec exists but tests don't, write the test suite in
   /tests/<system>/ derived from the spec. Stop. Commit. Exit.
5. If tests exist but fail or are missing implementation, implement
   until all tests pass. Then commit. Exit.
6. Before any commit: run `pytest`, `mypy --strict`, `ruff check`.
   If any fail, fix before committing. Do not commit red.
7. Mark the task complete in /tasks.md if and only if the full
   spec→test→implementation cycle for it is done and green.

## Conventions
- Evennia contribs preferred over custom code; document choices in
  /docs/decisions/
- Type hints everywhere, mypy strict
- One subsystem per commit; commit messages reference the task
- Never modify another subsystem's tests to make your code pass

## Stop conditions
- If /tasks.md is fully checked, write "RALPH: project complete"
  to /STATUS.md and exit
- If you encounter a decision not covered by specs, write the
  question to /docs/questions.md and exit without committing code
- If tests have been red for 3 consecutive commits on the same task,
  write to /STATUS.md and exit for human review

## Important
- Do not invent requirements not in the specs
- Do not skip the spec or test phase to get to implementation faster
- Do not modify /docs/specs/ to match your implementation; modify
  the implementation to match the spec, or escalate via /docs/questions.md
