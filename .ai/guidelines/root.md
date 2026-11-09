# piper-desktop-releases guidelines (root)

## What this repo is

Release tracking for the Piper Desktop app. It holds no application code: `README.md` is the list of published versions, newest last, one line each. The app itself lives in `piper-desktop`.

## Rules

- Only change `README.md` to add or correct a release entry. Do not add code, build files or tooling.
- One line per release: `* v<major>.<minor>.<patch>: <what changed, in user-facing words>`.
- Keep entries in version order and the format of the existing lines.
- Release notes describe what users get; leave internal details (refactors, CI changes) out.
