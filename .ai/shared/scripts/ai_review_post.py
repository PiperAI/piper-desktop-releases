#!/usr/bin/env python3
"""Turn the reviewer's JSON into a GitHub pull request review (approve, request changes or comment).

Shared copy: do not edit in this repository. Used by .github/workflows/ai-review.yml.
The verdict is derived here from the findings, not chosen by the model:
  any blocking finding                         -> REQUEST_CHANGES
  any should_fix finding                       -> COMMENT
  otherwise, if complete, risk not high and
  approvals are enabled                        -> APPROVE
  otherwise                                    -> COMMENT

Env: GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER, HEAD_SHA, MODEL, EFFORT, AI_REVIEW_APPROVE ("true"/"false").
Usage: ai_review_post.py REVIEW_JSON DIFF_PATCH [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path

BOT = "github-actions[bot]"
MARKER = "<!-- ai-review -->"
SEVERITY = {"blocking": "Blocking", "should_fix": "Should fix", "consider": "Consider"}
LABEL = {"APPROVE": "Approved", "REQUEST_CHANGES": "Changes requested", "COMMENT": "Comments"}


def commentable_lines(diff: str) -> dict[str, set[int]]:
    """Lines of the new version of each file that GitHub accepts inline comments on (added or context)."""
    lines: dict[str, set[int]] = {}
    path, new_line = None, 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = None if raw[4:] == "/dev/null" else raw[4:].removeprefix("b/")
            if path:
                lines.setdefault(path, set())
        elif raw.startswith("@@"):
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
            new_line = int(match.group(1)) if match else 0
        elif path and raw.startswith(("+", " ")) and not raw.startswith("+++"):
            lines[path].add(new_line)
            new_line += 1
    return lines


def verdict(review: dict, approve_enabled: bool) -> str:
    severities = {f.get("severity") for f in review.get("findings", [])}
    if "blocking" in severities:
        return "REQUEST_CHANGES"
    if "should_fix" in severities:
        return "COMMENT"
    if approve_enabled and review.get("complete") is True and review.get("risk") != "high":
        return "APPROVE"
    return "COMMENT"


def build(review: dict, diff: str, event: str, env: dict) -> tuple[str, list[dict]]:
    valid = commentable_lines(diff)
    findings = sorted(review.get("findings", []), key=lambda f: list(SEVERITY).index(f.get("severity", "consider"))
                      if f.get("severity") in SEVERITY else 3)
    inline, listed = [], []
    for i, f in enumerate(findings, 1):
        sev = SEVERITY.get(f.get("severity"), "Consider")
        where = f"`{f.get('path')}:{f.get('line')}`" if f.get("path") else ""
        listed.append(f"{i}. **{sev}** {where} {f.get('title', '').strip()}")
        if f.get("path") in valid and isinstance(f.get("line"), int) and f["line"] in valid[f["path"]]:
            inline.append({"path": f["path"], "line": f["line"], "side": "RIGHT",
                           "body": f"**{sev}**: {f.get('title', '').strip()}\n\n{f.get('body', '').strip()}"})
        else:
            listed[-1] += "\n\n" + textwrap.indent(f.get("body", "").strip(), "   ")
    parts = [MARKER, f"## AI review: {LABEL[event]}", "", f"**Risk:** {review.get('risk', 'unknown')}", "",
             review.get("summary", "").strip(), ""]
    if listed:
        parts += ["### Findings", "", *listed, ""]
        if inline:
            parts += [f"_Inline comments: {len(inline)}. Findings outside the diff are explained above._", ""]
    else:
        parts += ["No findings.", ""]
    if review.get("tests"):
        parts += ["### Tests", "", review["tests"].strip(), ""]
    if review.get("complete") is not True:
        parts += ["_The reviewer could not cover the whole change, so it did not approve._", ""]
    parts.append(f"<sub>opencode · llmgateway/{env.get('MODEL')} ({env.get('EFFORT')}) · {env.get('HEAD_SHA', '')[:7]} · "
                 "rules: .ai/shared/skills/code-review + .ai/guidelines/review.md</sub>")
    return "\n".join(parts), inline


def api(method: str, path: str, token: str, payload: dict | None = None):
    request = urllib.request.Request(
        f"https://api.github.com{path}", method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
    with urllib.request.urlopen(request) as response:
        body = response.read()
        return json.loads(body) if body else None


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    env = os.environ
    review_path, diff_path = Path(args[0]), Path(args[1])
    try:
        review = json.loads(review_path.read_text())
        assert isinstance(review, dict)
    except Exception as error:  # the model wrote nothing usable: fail loudly, never approve
        print(f"::error::No valid review JSON at {review_path}: {error}")
        return 1
    event = verdict(review, env.get("AI_REVIEW_APPROVE", "true").lower() == "true")
    body, inline = build(review, diff_path.read_text(), event, env)
    if dry_run:
        print(json.dumps({"event": event, "body": body, "comments": inline}, indent=2))
        return 0

    repo, number, token = env["GITHUB_REPOSITORY"], env["PR_NUMBER"], env["GITHUB_TOKEN"]
    base = f"/repos/{repo}/pulls/{number}/reviews"
    # Our earlier approvals or change requests no longer apply to the new commits.
    for old in api("GET", f"{base}?per_page=100", token) or []:
        if old["user"]["login"] == BOT and old["state"] in ("APPROVED", "CHANGES_REQUESTED") and MARKER in (old.get("body") or ""):
            try:
                api("PUT", f"{base}/{old['id']}/dismissals", token,
                    {"message": f"Superseded by the AI review of {env['HEAD_SHA'][:7]}.", "event": "DISMISS"})
            except urllib.error.HTTPError as error:
                print(f"::warning::Could not dismiss review {old['id']}: {error.code}")
    payload = {"commit_id": env["HEAD_SHA"], "event": event, "body": body, "comments": inline}
    try:
        api("POST", base, token, payload)
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="ignore")
        if error.code == 422 and "approve" in detail.lower():
            print("::warning::GitHub Actions may not approve pull requests here; posting as a comment instead. "
                  "Enable it in Settings > Actions > General > Workflow permissions.")
            payload["event"] = "COMMENT"
            event = "COMMENT"
        elif error.code == 422 and inline:
            print(f"::warning::Inline comments rejected ({detail[:200]}); posting them in the review body.")
            payload["comments"] = []
        else:
            raise
        api("POST", base, token, payload)
    print(f"Submitted review: {event} with {len(payload['comments'])} inline comment(s).")
    summary = env.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as handle:
            handle.write(body + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
