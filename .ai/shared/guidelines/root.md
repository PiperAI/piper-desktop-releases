# Engineering guidelines

General rules for this repository. Shared copy: do not edit it here.

This repository's own guidelines are in `.ai/guidelines/root.md`; read them next and follow their routing. They win where they conflict with this file.

## Rules

- Plan briefly, implement, then run the repository's checks before declaring the work done.
- Every new or changed behavior has a test.
- Never put secrets, tokens or personal data in code, logs, prompts or commits.
- Before a task, check the skills in `.ai/shared/skills/` and `.ai/skills/` and use the one whose description matches.
- When a change alters architecture, workflow or conventions, update the matching guideline in the same pull request.
- Before changing anything under `.ai/`, `AGENTS.md` or `CLAUDE.md`, read `.ai/shared/guidelines/ai-context.md`.
