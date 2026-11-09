# AI context structure

How this repository's AI context is organized. Shared copy: do not edit it here.

## Structure

- `AGENTS.md` and `CLAUDE.md` contain only `@.ai/shared/guidelines/root.md` and `@.ai/guidelines/root.md`, in that order.
- `.ai/guidelines/root.md` says what the repository is and how to run its checks, then links every other guideline in `.ai/guidelines/` with when to read it.
- `.ai/guidelines/review.md` holds the repository's review rules; the `code-review` skill reads it.
- Skills live in `.ai/skills/`, one folder per skill with a `SKILL.md`; commands in `.ai/commands/`.
- `.ai/shared/` and the shared review workflow are shared copies, changed at their source, never here.
- Tool folders (`.claude/`, `.cursor/`, …) only hold generated pointers to every skill and command. Never edit them; regenerate them with the AI context sync after adding, renaming or removing a skill or command.

## Writing rules

- Write every path from the repository root (`.ai/...`, `src/...`), never `./` or `../`: skills and guidelines are loaded through pointers and imports, so relative paths resolve from the wrong folder.
- Size limits: `.ai/guidelines/root.md` 200 lines, other guidelines 250, `SKILL.md` 300, commands 200. Over the limit, split by area or move a procedure into a skill.
- `SKILL.md` frontmatter has a `name` equal to its folder and a `description` that says when to use it.
- Write instructions an agent can act on. No history, no file-by-file inventories, no text that repeats another file the agent already loads.
- When an agent repeats the same mistake twice, add a rule or a skill step.
- A skill useful beyond this repository is proposed as a shared skill instead of being copied.
