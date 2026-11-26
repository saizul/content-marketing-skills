---
name: headline-testing
description: Write and compare headlines, SEO title tags, email subject lines and social hooks - 12 proven formulas (how-to, numbered list, question, comparison, mistakes, without, result in time, bracket qualifiers) - and rank the variants with a script that scores length for the channel (title tag ~50-60 chars, email <= 50, social), word count, numbers, power words, formula match, focus keyword presence and position, and flags clickbait, ALL CAPS, repeated punctuation, vague words and fake "RE:" prefixes. Then plans a real test (Search Console title change, email A/B split, social variants). Use when the user asks for headline ideas, a better title, title tag or H1, blog title options, email subject line variants, to "A/B test headlines", or asks which of several headlines is best.
license: MIT
compatibility: Python 3.8+ standard library only. Works offline; English word lists.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# Headline testing

Generate many honest variants, filter them with a consistent score, then let real readers
decide. The score compares variants of the same idea; it does not predict click-through.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Give me 10 headline options", "is this a good title?", "which subject line is best?"
- Title tag and H1 for a new post, or a refresh of a post whose CTR dropped
- Subject line variants for an email A/B test; hooks for social posts

## When not to use

- The rest of the post: `blog-post-writer`
- Full newsletter checks (preview text, merge tags, links): `newsletter-writer`
- Diagnosing why CTR fell across many pages: `content-refresh` first

## Workflow

1. **Collect**: the topic, the reader, the focus keyword (for SEO), the channel (`seo`,
   `blog`, `email`, `social`) and the one promise the content keeps. A headline must not
   promise more than the content delivers.
2. **Write 8-15 variants** using different formulas from
   [references/formulas.md](references/formulas.md): at least one how-to, one number, one
   question or "why", one specific-result, one with a bracket qualifier. Keep the keyword
   near the front for SEO titles.
3. **Score and rank (read-only):**
   ```bash
   python3 scripts/score_headlines.py --type seo --keyword "content calendar" \
     "How to Build a Content Calendar Your Team Will Actually Use" \
     "7 Content Calendar Mistakes That Quietly Kill Your Traffic"
   python3 scripts/score_headlines.py --file variants.txt --type email --json
   printf '%s\n' "Variant A" "Variant B" | python3 scripts/score_headlines.py --file - --type social
   ```
   Lines starting with `#` in the file are ignored; duplicates are removed. Exit 1 when no
   variant reaches `--min-score` (default 60).
4. **Edit, do not just pick.** Fix the flags on the top 3-5 (too long, keyword late,
   vague words, hype), re-score, and drop anything flagged as clickbait or deceptive.
5. **Recommend 2-3 finalists** with a one-line reason each, and the test plan from
   [references/testing.md](references/testing.md): what to change, how long to wait, what
   metric decides.

## Output

```
Channel: seo, keyword "content calendar"

score chars headline
  95   58   7 Content Calendar Mistakes That Quietly Kill Your Traffic   (list, mistakes)
  88   61   Content Calendar Template for Small Teams (Free Google Sheet) (long: trim "Google")
  85   59   How to Build a Content Calendar Your Team Will Actually Use   (how-to)
  45   57   You Won't Believe This SHOCKING Content Calendar Trick!!!     (clickbait - dropped)

Recommendation: title tag = #1 (specific, number, keyword first); H1 = #3 (matches how-to intent)
Test: change the title tag only, compare 28 days of Search Console CTR at similar position
```
