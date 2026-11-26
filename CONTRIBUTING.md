# Contributing to content-marketing-skills

Thank you for helping! New checks, new skills, fixes, fixtures that expose false positives,
better templates and clearer docs are all welcome.

- [Ways to contribute](#ways-to-contribute)
- [Good first issues](#good-first-issues)
- [Development setup](#development-setup)
- [Repository layout](#repository-layout)
- [Write a new skill](#write-a-new-skill)
- [Quality bar](#quality-bar)
- [Pull request process](#pull-request-process)

## Ways to contribute

| Size | Idea |
| --- | --- |
| 10 minutes | Fix a typo, clarify a workflow step, add a hook or headline formula with an example |
| 30 minutes | Add a fixture (draft, post, CSV) that triggers a false positive or a missed finding |
| 1-2 hours | Add a check or option to an existing script (see below) |
| Half a day | Write a new skill from the template |

Comment on an issue before you start so nobody else picks the same one.

## Good first issues

Each of these is self-contained and touches one script and its test file.

1. **blog-post-writer: transition words.** Report the share of sentences that start with a
   transition word ("however", "for example", "so") as a metric, with a low finding under 10%.
2. **blog-post-writer: heading questions.** Count H2s phrased as questions and mention them
   as featured-snippet candidates in the report (info only).
3. **linkedin-post-writer: `--max-chars`.** Let users set their own length target (e.g.
   1,300) and report `length.over_target` as low.
4. **linkedin-post-writer: engagement bait.** Flag "Comment YES if...", "Like if you agree"
   and "Agree?" as the only CTA (low).
5. **headline-testing: `--words` power word file.** Load extra power words from a text file
   so teams can use their own lists (and other languages).
6. **newsletter-writer: Mailchimp merge tag default syntax.** Recognise
   `*|FNAME:default|*`-style fallbacks if your platform supports them, with tests.
7. **editorial-calendar: `--ics` output.** Write an iCalendar file next to the CSV so the
   plan can be imported into Google Calendar or Outlook.
8. **editorial-calendar: per-cluster cadence.** Allow a `weight` column so one cluster gets
   two slots for every one of another.
9. **internal-linking: `--exclude` glob.** Skip drafts, tag pages or archive folders.
10. **internal-linking: Markdown patch output.** `--patch` prints a unified diff that wraps
    the anchor text in a link, without writing files.
11. **content-refresh: Queries.csv mode.** Group decaying queries by the page they map to
    when both exports are given.
12. **content-repurposing: carousel outline.** Add a `carousel` channel that outputs 6-10
    slide texts (title, one point per slide, CTA slide).
13. **New skill: `content-brief-generator`** (see the roadmap in the README).

## Development setup

```bash
git clone https://github.com/saizul/content-marketing-skills.git
cd content-marketing-skills
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt

python tools/validate_skills.py   # SKILL.md frontmatter, sections, links, assets, marketplace listing
ruff check . && ruff format --check .
pytest
```

To try your changes in Claude Code, either copy a skill to `~/.claude/skills/` or add your
checkout as a local marketplace:

```bash
claude plugin marketplace add ./content-marketing-skills
claude plugin install content-marketing-skills@content-marketing-skills
```

For Codex, copy the skill folder to `~/.agents/skills/`.

## Repository layout

```
.claude-plugin/
  marketplace.json      marketplace + plugin entry listing every skill
  plugin.json           plugin manifest (name, version, author)
skills/<name>/
  SKILL.md              frontmatter + workflow (the part agents read)
  scripts/*.py          standalone helpers, Python 3.8+ stdlib only
  references/*.md       detail loaded on demand
  assets/               templates (topics CSV, channel templates)
templates/skill/        copy this to start a new skill
tests/
  test_<skill>.py       one test module per skill
  fixtures/<skill>/     inputs: drafts, posts, newsletters, Search Console CSVs
tools/validate_skills.py
```

## Write a new skill

1. Open a "New skill proposal" issue first so we can agree on scope.
2. Copy the template:
   ```bash
   cp -r templates/skill skills/my-skill
   mv skills/my-skill/scripts/your_script.py skills/my-skill/scripts/my_check.py
   ```
3. Edit `SKILL.md`:
   - `name` equals the folder name: lowercase letters, digits, single hyphens, max 64 chars.
   - `description` (max 1024 chars) says **what** it does with concrete keywords and **when**
     to use it, starting the second part with "Use when ...". This text decides whether
     the agent picks the skill, so list the phrases users actually type.
   - Required sections: `## When to use`, `## When not to use`, `## Workflow`, `## Output`.
   - Workflow steps are imperative and numbered, with exact commands, decision points and
     the point where the agent must ask before publishing, sending or editing anything.
   - Keep it under 400 lines; move formulas, tables and long templates to `references/`
     or `assets/`.
4. Write the script: `argparse` with a useful `--help`, `--json` output, exit codes
   0 (ok) / 1 (findings) / 2 (error), read-only on inputs, no network, no overwriting
   without `--force`.
5. Add `tests/test_my_skill.py` and fixtures in `tests/fixtures/my-skill/`. Cover a bad
   input, a good input with no findings, edge cases and the CLI exit codes.
6. Add the skill to `.claude-plugin/marketplace.json` (`plugins[0].skills`), the README
   skills table, the table in `AGENTS.md`, the bug report dropdown and `CHANGELOG.md`
   under "Unreleased".
7. Run the validator, ruff and pytest.

## Quality bar

- **Honest.** A skill must never tell the agent to invent data, quotes, reviews or
  results, or to imitate a real person or brand.
- **Safe.** No skill publishes, posts, sends, schedules or changes a live site; the user
  does that after review.
- **Grounded.** Platform limits (characters, row limits, legal rules) must be sourced from
  official documentation; say "about" when a platform does not publish an exact number.
- **Deterministic where it matters.** If a step is "count, measure or compare", write a
  script and test it instead of asking the model to eyeball it.
- **Low false positives.** If a check is often wrong, make it `low`/`info` or drop it, and
  document known limitations in the skill's references.
- **Fictional fixtures.** Use example.com, invented companies and numbers; never real
  client data or subscriber lists.

## Pull request process

1. Fork, create a branch, make focused commits.
2. Make sure CI passes locally (validator, ruff, pytest).
3. Fill in the pull request template.
4. A maintainer reviews within a few days. Small, focused pull requests are merged fastest.

By contributing you agree that your contributions are licensed under the MIT License.
