# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `headline-testing`: `score_headlines.py --suffix " | Acme Blog"` counts the text a CMS
  appends to every title tag in the length score, flags headlines the suffix pushes over the
  ideal length and reports the full `title` in JSON. Keyword position is still measured on
  the headline alone.

## [0.1.0] - 2026-11-26

### Added

- `editorial-calendar`: `build_calendar.py` builds a calendar CSV (or JSON) from topic
  clusters in CSV/JSON - pillar first, clusters interleaved, weekdays, fortnightly
  cadence, skipped dates, brief due dates, owners, pillar link targets and repurposing
  dates - with warnings for keyword cannibalisation, missing keywords, clusters without a
  pillar and one-sided funnels; planning guide and topics template.
- `blog-post-writer`: `score_draft.py` scores Markdown drafts for headings, keyword
  placement, stuffing, meta length, word count, Flesch reading ease and grade, sentence
  length, passive voice, paragraphs, alt text, links and E-E-A-T signals; outlines, hooks
  and E-E-A-T references.
- `linkedin-post-writer`: `check_post.py` checks the 3,000-character limit, hook length and
  weak openers, line breaks, hashtags, links, emoji (`--no-emoji`), Unicode bold, mentions,
  capitals and the closing CTA; hook, body and CTA patterns.
- `content-repurposing`: `repurpose.py` drafts a LinkedIn post, an X thread (weighted
  280-character posts), a newsletter section and a short video script from a Markdown
  post; channel templates and specs.
- `internal-linking`: `suggest_links.py` suggests internal links between Markdown/MDX/HTML
  posts by TF-IDF overlap with anchor phrases and context, skips existing links and lists
  orphans; linking rules.
- `headline-testing`: `score_headlines.py` ranks headline variants for SEO titles, H1s,
  email subjects and social hooks; formulas and test plans.
- `newsletter-writer`: `check_newsletter.py` checks subject lines, preview text, merge
  tags, CTAs, alt text, spam phrases and unsubscribe links; formats, subject line and
  compliance references.
- `content-refresh`: `find_decay.py` finds decaying pages in Search Console compare
  exports, two single-period exports or daily rows, with diagnoses, actions and
  striking-distance pages; refresh playbook.
- Claude Code plugin marketplace manifest, `tools/validate_skills.py`, CI and release workflows.

[Unreleased]: https://github.com/saizul/content-marketing-skills/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/saizul/content-marketing-skills/releases/tag/v0.1.0
