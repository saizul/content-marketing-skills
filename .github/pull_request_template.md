## What does this pull request do?

<!-- One or two sentences. Link the issue: "Closes #123". -->

## Type

- [ ] New skill
- [ ] New check or option in an existing script
- [ ] Workflow / reference / template improvement
- [ ] Bug fix
- [ ] Repository tooling (validator, CI)

## Checklist

- [ ] `python tools/validate_skills.py` passes
- [ ] `ruff check . && ruff format --check .` passes
- [ ] `pytest` passes; new script behaviour has tests with fixtures in `tests/fixtures/`
- [ ] Scripts use only the Python standard library, support `--help`, have a `--json`
      option where output is structured, and exit non-zero on findings
- [ ] Scripts are read-only on inputs, make no network calls and never overwrite files
      without `--force`
- [ ] Fixtures contain no client data, real subscriber data or real site URLs (use example.com)
- [ ] Skill text never tells the agent to invent statistics, quotes or results, or to
      publish/send without the user
- [ ] New skills: listed in `.claude-plugin/marketplace.json`, the README skills table,
      `AGENTS.md`, the bug report dropdown and CHANGELOG.md
