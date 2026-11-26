# content-marketing-skills

[![CI](https://github.com/saizul/content-marketing-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/saizul/content-marketing-skills/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/saizul/content-marketing-skills?sort=semver)](https://github.com/saizul/content-marketing-skills/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/saizul/content-marketing-skills?style=social)](https://github.com/saizul/content-marketing-skills/stargazers)

**Agent Skills that help Claude Code and Codex plan, write and repurpose content that ranks and converts - with tested scripts that check drafts, build calendars and read your Search Console data.**

Eight skills for founders, freelancers and agencies who publish without a big content
team: plan a calendar from topic clusters, write SEO blog posts and LinkedIn posts, turn
one post into four channels, add internal links, test headlines, write newsletters and
find the posts that are losing traffic. Every skill ships a standard-library-only Python
script that works offline on your Markdown, HTML and CSV files.

- **Checks, not vibes.** Scripts score drafts (headings, keyword placement, readability,
  passive voice, alt text, links), check LinkedIn posts and newsletters against real
  limits, and report as text or JSON with CI-friendly exit codes.
- **Honest by default.** The skills tell the agent never to invent statistics, quotes,
  clients or results, and to mark gaps as `[ADD: ...]` instead.
- **Nothing is published or sent.** Scripts are read-only on inputs, make no network
  calls, never touch your CMS, email platform or Google account, and refuse to overwrite
  files without `--force`.
- **No emoji unless you want them.** LinkedIn, repurposing and newsletter checks have a
  strict `--no-emoji` mode.
- **Tested.** 100+ tests with fixture posts, newsletters and Search Console exports, run
  on Python 3.11-3.13 in CI.

## Skills

| Skill | What it does | Try asking |
| --- | --- | --- |
| [editorial-calendar](skills/editorial-calendar/SKILL.md) | Topic clusters (pillar + spokes), funnel mix and cadence; script builds a calendar CSV with dates, holidays skipped, brief due dates, owners, pillar link targets and repurposing dates; warns about keyword cannibalisation | "Plan 12 weeks of blog posts for our three service lines, two posts a week" |
| [blog-post-writer](skills/blog-post-writer/SKILL.md) | Intent check, outlines by post type, hooks, E-E-A-T signals; script scores a Markdown draft: headings, keyword in title/H1/intro/H2/slug/meta, stuffing, Flesch, sentence length, passive voice, alt text, links | "Write a post for 'content calendar template' and score it" |
| [linkedin-post-writer](skills/linkedin-post-writer/SKILL.md) | Hook, body and CTA patterns, no-emoji formatting; script checks 3,000-char limit, hook length, weak openers, line breaks, hashtags, links in body, Unicode bold, CTA | "Turn this client win into a LinkedIn post, no emojis" |
| [content-repurposing](skills/content-repurposing/SKILL.md) | One blog post into a LinkedIn post, X thread (280 per post, URLs = 23), newsletter section and 45-60 s video script; templates for the rewrite | "Repurpose this article for LinkedIn, X and our newsletter" |
| [internal-linking](skills/internal-linking/SKILL.md) | Script reads a Markdown/MDX/HTML content folder, suggests source -> target links by TF-IDF keyword overlap with anchor text found in the sentence, skips existing links, lists orphan pages | "Which old posts should link to my new post, and what anchor text?" |
| [headline-testing](skills/headline-testing/SKILL.md) | 12 headline formulas; script ranks variants for SEO titles, H1s, email subjects or social hooks: length, numbers, power words, formula, keyword position, clickbait flags; real test plans | "Give me 10 title options for this post and rank them" |
| [newsletter-writer](skills/newsletter-writer/SKILL.md) | Issue formats, subject lines and preview text; script checks subject length, spam phrases, caps, fake RE:, preview text, merge tags and fallbacks, CTAs, alt text, unsubscribe | "Write this week's newsletter from these notes and check it" |
| [content-refresh](skills/content-refresh/SKILL.md) | Script finds decaying pages in a Search Console export (compare CSV, two files or daily rows), diagnoses rankings slipped / demand fell / CTR fell / collapsed, lists striking-distance pages; refresh playbook | "Our blog traffic dropped. Here is Pages.csv - what should we update?" |

## Install

### Claude Code: plugin marketplace (recommended)

```text
/plugin marketplace add saizul/content-marketing-skills
/plugin install content-marketing-skills@content-marketing-skills
```

Or from your shell:

```bash
claude plugin marketplace add saizul/content-marketing-skills
claude plugin install content-marketing-skills@content-marketing-skills
```

Plugin skills are namespaced, e.g. `/content-marketing-skills:blog-post-writer`. Claude
also picks them up automatically when your request matches a skill's description. Update
later with `/plugin marketplace update content-marketing-skills`.

### Claude Code: copy the skills

```bash
git clone https://github.com/saizul/content-marketing-skills.git
# all projects (personal skills)
mkdir -p ~/.claude/skills && cp -r content-marketing-skills/skills/* ~/.claude/skills/
# or just one project
mkdir -p .claude/skills && cp -r content-marketing-skills/skills/blog-post-writer .claude/skills/
```

Each release also has one zip per skill and an all-skills zip under
[Releases](https://github.com/saizul/content-marketing-skills/releases).

### Codex CLI

Codex reads skills from `~/.agents/skills` (all repositories) and `.agents/skills` in a
repository (from the current directory up to the repository root):

```bash
git clone https://github.com/saizul/content-marketing-skills.git
mkdir -p ~/.agents/skills && cp -r content-marketing-skills/skills/* ~/.agents/skills/
# or per repository
mkdir -p .agents/skills && cp -r content-marketing-skills/skills/content-refresh .agents/skills/
```

Codex also ships a `$skill-installer` skill that can install skills from a GitHub
repository; ask it to install from `saizul/content-marketing-skills`. Skill locations and
the installer are described in the [Codex skills documentation](https://developers.openai.com/codex/skills);
check it if your Codex version behaves differently. [AGENTS.md](AGENTS.md) explains how
Codex and other agents should use these skills.

### Any other agent

The skills follow the open [Agent Skills format](https://agentskills.io/specification):
a folder with `SKILL.md` (YAML frontmatter + instructions), `scripts/`, `references/` and
`assets/`. Point your agent at the folder, or run the scripts yourself; every script has `--help`.

## Usage examples

```text
> Here is drafts/content-calendar.md. Is it ready to publish?
  (Runs score_draft.py: 62/100 - two H1s, keyword missing from the intro, 3 images
   without alt text, no internal links. Fixes them, marks "[ADD: client result]" where
   proof is missing, re-scores to 91.)

> Search Console says clicks are down 18%. Pages.csv is attached.
  (find_decay.py lists 23 decaying pages: the calendar guide lost CTR at the same
   position -> rewrite the title; the copywriting guide slipped from 8.9 to 14.2 ->
   refresh brief; the Black Friday post is seasonal -> leave until October.)

> Turn this post into a LinkedIn post and an X thread, no emojis.
  (repurpose.py builds both from the post's own sentences, then the agent rewrites the
   hook and checks the LinkedIn draft with check_post.py --no-emoji.)
```

Run the scripts directly too:

```bash
python3 skills/editorial-calendar/scripts/build_calendar.py topics.csv --start 2026-01-05 --per-week 2 --weeks 12 --out calendar.csv
python3 skills/blog-post-writer/scripts/score_draft.py post.md --keyword "content calendar"
python3 skills/linkedin-post-writer/scripts/check_post.py draft.txt --no-emoji
python3 skills/content-repurposing/scripts/repurpose.py post.md --url https://example.com/blog/post/ --out drafts/post
python3 skills/internal-linking/scripts/suggest_links.py content/posts --site example.com --csv links.csv
python3 skills/headline-testing/scripts/score_headlines.py --file variants.txt --type seo --keyword "content calendar"
python3 skills/newsletter-writer/scripts/check_newsletter.py issue.md --no-emoji
python3 skills/content-refresh/scripts/find_decay.py Pages.csv --opportunities
```

## How skills work

At startup the agent loads only each skill's `name` and `description` (about 100 tokens
each). When your request matches a description, it reads that skill's `SKILL.md`: the
workflow, decision points and rules. Longer material lives in `references/` and is read
only when a step needs it; `assets/` holds templates to fill in. Scripts run as normal
commands, so their output is exact and repeatable.

```
skills/<skill-name>/
  SKILL.md          frontmatter (name, description) + workflow
  scripts/          standalone Python 3 helpers (stdlib only, --help, --json)
  references/       playbooks, formulas, check explanations
  assets/           templates (topics CSV, channel templates)
```

## FAQ

**Will the agent publish posts or send emails?**
No. The skills draft and check; publishing, scheduling and sending stay with you. No
script calls LinkedIn, X, your CMS, your email platform or Google.

**Does it make things up?**
The skills instruct the agent to use only facts you provide and to leave `[ADD: ...]`
placeholders where proof is missing. Review drafts before publishing anyway.

**Do I need an SEO tool subscription?**
No. The content-refresh skill reads Search Console exports you download yourself;
everything else works on your own files.

**Which blog platforms work with internal-linking?**
Anything that stores posts as Markdown/MDX (Hugo, Jekyll, Astro, Next.js, Eleventy,
Gatsby) or HTML (static exports, WordPress HTML exports). It reads files; it does not crawl.

**Is the readability scoring valid for other languages?**
Flesch reading ease and passive-voice detection are English-only. Structure, keyword,
link and alt-text checks work for any language.

**Can I use the checkers in CI?**
Yes: every checker supports `--json` and exits 1 on findings (or below `--min-score`).

## Roadmap

Ideas for new skills (great first contributions; see [CONTRIBUTING.md](CONTRIBUTING.md)):

- `content-brief-generator` - turn a keyword and SERP notes into a structured brief
- `case-study-writer` - interview questions, structure and a results checker for client case studies
- `x-thread-writer` - native threads with hook variants and a per-post length checker
- `youtube-script-writer` - long-form video scripts with chapters and retention beats
- `lead-magnet-builder` - checklists, templates and email sequences that deliver them
- `content-audit` - inventory a content folder: word counts, dates, missing meta, thin pages
- `seo-meta-writer` - title tags and meta descriptions in bulk with a CSV length checker
- `brand-voice-guide` - extract a voice guide from past posts and check drafts against it

## Contributing

Contributions are welcome: new checks, new skills, fixtures that expose false positives,
better templates and clearer docs. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the skill
template, the quality bar and how to run the validator and tests:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python tools/validate_skills.py && ruff check . && ruff format --check . && pytest
```

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) and report security issues
privately as described in [SECURITY.md](SECURITY.md).

LinkedIn, X, Google and Search Console are trademarks of their owners. This project is
independent and not affiliated with them.

## License

[MIT](LICENSE) (c) Saizul Amin
