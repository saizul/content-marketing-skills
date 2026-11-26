---
name: blog-post-writer
description: Write and edit SEO blog posts that rank and convert - search-intent check, outline by post type (how-to, list, comparison, guide, case study), hooks that skip the throat-clearing, E-E-A-T signals (first-hand experience, data, sources, author and dates), one CTA - then score the Markdown draft with a script - one H1, heading hierarchy, section length, focus keyword in title, H1, first 100 words, an H2, slug and meta description, keyword stuffing, meta title/description length, word count, Flesch reading ease and grade, sentence length, passive voice, long paragraphs, images without alt text, internal and external links. Use when the user asks to write, outline, draft, edit, improve, optimise or "SEO-check" a blog post or article, shares a Markdown draft, or asks why a post is not ranking because of on-page quality.
license: MIT
compatibility: Python 3.8+ standard library only. Works offline on Markdown files (YAML frontmatter optional). Readability formulas are for English.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# Blog post writer

Write for one reader with one problem, prove it with experience, then let the script catch
the mechanical issues. Never invent statistics, quotes, clients or results.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Write a blog post about X", "outline an article for keyword Y"
- The user shares a draft (`.md`) and asks to edit, tighten or SEO-check it
- Turning a brief from the editorial calendar into a draft
- Rewriting an old post as part of a refresh

## When not to use

- Scheduling many posts: `editorial-calendar`
- Diagnosing traffic loss across a site: `content-refresh` first, then come back
- Picking between title options only: `headline-testing`
- Social posts and newsletters from a finished post: `content-repurposing`
- Technical SEO (crawling, indexing, schema, speed): outside this skill

## Workflow

1. **Brief.** Confirm or ask for: reader, focus keyword, search intent, the one action
   the reader should take, what first-hand proof exists (results, screenshots, client
   stories, tests), and the target length. If the user has no proof, say where the post
   will be thin rather than faking it.
2. **Check intent.** Describe what currently ranks for the keyword (type of page, depth,
   format) if the user can share it; match the format (a "template" query wants a
   template, not an essay). Do not claim to have searched if you have not.
3. **Outline** with the matching pattern in [references/structure.md](references/structure.md):
   H1 with the keyword near the front, 4-8 H2s that answer the questions a searcher has
   in order, the proof and the CTA placed. Share the outline before drafting a long post.
4. **Draft** in Markdown with frontmatter:
   ```yaml
   ---
   title: "Content Calendar for Small Teams: A Simple System"   # <= 60 chars
   description: "120-160 chars that promise the outcome and include the keyword."
   keyword: content calendar
   slug: content-calendar-small-teams
   author: Name
   date: 2026-11-26
   ---
   ```
   - Hook: open with the problem, a result or a specific claim; no "In this article".
     Formulas in [references/structure.md](references/structure.md#hooks).
   - Short paragraphs (2-4 sentences), sentences mostly under 20 words, active voice.
   - E-E-A-T: add the signals in [references/eeat.md](references/eeat.md), using only
     facts the user gave you. Mark gaps as `[ADD: client result]` instead of inventing.
   - 2-5 internal links (pillar page + related posts) and links to primary sources.
5. **Score the draft (read-only):**
   ```bash
   python3 scripts/score_draft.py post.md
   python3 scripts/score_draft.py post.md --keyword "content calendar" --min-words 1200
   python3 scripts/score_draft.py post.md --site example.com --json
   cat draft.md | python3 scripts/score_draft.py - --min-score 80
   ```
   Score = 100 minus 15 per high, 7 per medium, 3 per low finding. Exit 1 when below
   `--min-score` (default 70). What each check means: [references/checks.md](references/checks.md).
6. **Fix in priority order:** high (title/keyword/H1) > medium (structure, meta, alt text,
   internal links, readability) > low (polish). Do not chase 100: keyword density and
   word count are guides, and a check that would make the post worse for readers loses.
7. **Re-score** and report the before/after score with the remaining findings explained.

## Output

```
Draft: "Content Calendar for Small Teams: A Simple System" - score 62 -> 91

Fixed: second H1 demoted, keyword added to intro, 3 sentences split, alt text on 2 images,
       links to /content-brief/ and /topic-clusters/, meta description 148 chars
Kept on purpose: 'keyword.h2' (an H2 with the keyword read unnaturally)
Needs you: [ADD: the client result from March] in "Choose a cadence" - no numbers yet

Files: post.md (draft), score: python3 scripts/score_draft.py post.md -> 91/100
```
