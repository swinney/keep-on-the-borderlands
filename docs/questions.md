# Questions / Escalation Log

This is the live escalation log referenced by `PROMPT.md` (CLAUDE.md §5). When a
Claude Code session (Ralph Loop or otherwise) hits a decision **not authorized by
the specs and with no sensible default**, it records the question here and stops
without committing speculative content, rather than inventing a requirement.

Resolved design questions (with reasoning) live in `docs/open-questions.md`; this
file is only for *open blockers* awaiting human input.

## Format

```
### <short title>
- **Context:** what was being worked on
- **Question:** the decision needed
- **Why blocked:** why no default is safe to assume
- **Date / phase:** when raised
```

## Open blockers

_None as of Phase 0 (2026-05-30)._ All open questions were resolvable from
`CLAUDE.md` context and are answered in `docs/open-questions.md`.
