# AGENTS.md

Guidance for Codex CLI and other coding agents that use or work on this repository.

## Using the skills

The skills live in `skills/<name>/SKILL.md` and follow the Agent Skills format. Codex
discovers them when they are copied to `~/.agents/skills/` or `.agents/skills/` (see
README "Install"). If you are reading this file inside the repository instead:

1. Pick the skill whose `description` matches the user's request:

   | Request is about | Skill |
   | --- | --- |
   | content plan, editorial calendar, topic clusters, publishing schedule | `editorial-calendar` |
   | writing, editing or SEO-checking a blog post or article | `blog-post-writer` |
   | writing or reviewing a LinkedIn post, posts without emoji | `linkedin-post-writer` |
   | turning one post into LinkedIn, X thread, newsletter, video script | `content-repurposing` |
   | internal links, related posts, orphan pages, cluster linking | `internal-linking` |
   | headline, title tag, subject line options and A/B tests | `headline-testing` |
   | newsletter issues, subject lines, preview text, pre-send checks | `newsletter-writer` |
   | traffic drops, decaying posts, Search Console exports, what to update | `content-refresh` |

2. Read that `SKILL.md` completely and follow its Workflow section in order.
3. Paths such as `scripts/x.py`, `references/y.md` and `assets/z.md` are relative to the
   skill folder. `${CLAUDE_SKILL_DIR}` in the text means that folder; Codex does not expand it.
4. Read files in `references/` only when a workflow step points to them.

## Rules (apply to every skill)

- Never invent statistics, quotes, testimonials, client names or results. Use what the
  user gives you; mark gaps as `[ADD: ...]`.
- Never publish, schedule, post or send anything, and never edit, redirect or delete
  pages on a live site. Draft, check, and hand the result to the user.
- Do not ask for passwords or API keys (Google, LinkedIn, email platforms). The scripts
  work on files the user exports.
- Drafts, subscriber data and Search Console exports can be confidential client data.
  Work on local files; quote only what is needed.
- Scripts never overwrite files without `--force`; do not pass `--force` unless the user
  agreed to replace that file.
- Default to no emoji in drafts unless the user asks for them.

## Working on this repository

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python tools/validate_skills.py   # frontmatter, sections, links, assets, marketplace listing
ruff check . && ruff format --check .
pytest
```

- Scripts: Python 3.8+ standard library only, `#!/usr/bin/env python3`, `argparse` with
  `--help`, `--json` where output is structured, exit 0/1/2 (ok / findings / error).
- Scripts must stay standalone (one file each, no shared module) so a single skill folder
  can be copied on its own.
- Every script needs tests in `tests/test_<skill_with_underscores>.py` with fixtures in
  `tests/fixtures/<skill>/`. Use `example.com` URLs and invented, clearly fictional data.
- Keep each `SKILL.md` under 400 lines; move detail to `references/`.
- A new skill must be added to `.claude-plugin/marketplace.json` (`plugins[0].skills`), the
  README table, the table above, the bug report dropdown and `CHANGELOG.md`. The
  validator enforces the manifest.
