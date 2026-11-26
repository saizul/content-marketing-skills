---
name: editorial-calendar
description: Plan a content calendar from topic clusters - pillar pages and supporting posts, one keyword per post, a funnel mix (TOFU/MOFU/BOFU) and a publishing cadence a small team can keep - then generate the calendar as a CSV with a script (dates by weekday and interval, holidays skipped, pillar first, clusters interleaved, brief due dates, owners, pillar link targets, optional LinkedIn/newsletter repurposing dates) that imports into Google Sheets, Notion, Airtable or Excel. Warns about keyword cannibalisation, topics without keywords, clusters without a pillar and unbalanced funnels. Use when the user asks for a content calendar, editorial calendar, content plan, blog schedule, publishing schedule, topic clusters, "what should we publish next quarter", or has a list of topics to put on dates.
license: MIT
compatibility: Python 3.8+ standard library only. Works offline; writes only the CSV you ask for.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# Editorial calendar

Turn business goals into topic clusters, and clusters into dated work the team can ship.
The script does the date maths and the consistency checks; you do the strategy.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Build us a content calendar for Q1", "plan 12 weeks of blog posts"
- The user has a list of topics or keywords and needs them scheduled
- Setting up topic clusters / pillar pages for a site, agency client or founder blog
- Re-planning after a missed month: new cadence, holidays, more writers

## When not to use

- Writing a single post: `blog-post-writer`
- Finding which existing posts to update: `content-refresh` (its output can feed this calendar)
- Social-only schedules with no source content: plan them directly; use `content-repurposing`
  when posts derive from articles

## Workflow

1. **Gather inputs** (ask only for what is missing):
   - Audience and offer: who buys, what they search before buying.
   - Goal for the period: traffic, leads, sales enablement, authority.
   - Capacity: writers, hours per post, review steps. This sets the cadence.
   - Existing content and known keywords (a Search Console export helps).
   - Fixed dates: launches, holidays, events, blackout weeks.
2. **Design 2-5 topic clusters** using [references/planning-guide.md](references/planning-guide.md):
   one pillar page per cluster plus 4-8 spokes, one focus keyword per topic, a funnel stage
   and a format each. Show the clusters as a table and **get the user's approval** before
   scheduling; this is the strategic decision.
3. **Pick the cadence.** Default to what the team can sustain (see the cadence table in the
   reference). Fewer, better posts beat a schedule that slips by week three.
4. **Write the topics file** (CSV or JSON, format in the reference;
   [assets/topics-template.csv](assets/topics-template.csv) is a starting point). Required:
   `cluster`, `title`. Recommended: `keyword`, `type` (pillar/spoke), `funnel`, `format`,
   `priority` (1 = first), `owner`.
5. **Build the calendar (read-only on inputs):**
   ```bash
   python3 scripts/build_calendar.py topics.csv --start 2026-01-05 --per-week 2 --weeks 12
   python3 scripts/build_calendar.py topics.csv --start 2026-01-05 --days tue,thu \
     --skip 2026-01-19,2026-02-16 --owners Ana,Ben --repurpose --out calendar.csv
   python3 scripts/build_calendar.py topics.json --interval-weeks 2 --days wed --json
   ```
   - `--days` overrides `--per-week`; `--interval-weeks 2` publishes fortnightly.
   - `--lead-days 7` sets the brief due date; `--repurpose` adds `linkedin_date` (next
     workday) and `newsletter_date` (next `--newsletter-day`, default Friday).
   - `--out` refuses to overwrite an existing file unless `--force`.
   - Warnings go to stderr; `--strict` exits 1 when there are any (useful in a review step).
6. **Resolve warnings** before handing over:
   - Same keyword on two topics: merge them or give one a different intent.
   - Topics did not fit: extend `--weeks`, raise cadence, or cut the lowest priority.
   - Cluster without a pillar: add one or schedule the pillar first manually.
   - Funnel all TOFU: add comparison, case study, pricing or "how to choose" posts.
7. **Hand over** the CSV with import notes: Google Sheets (File > Import), Notion (import
   CSV as database), Airtable (CSV import). Suggest a monthly review slot.

## Output

```
Clusters (approved): Content planning (pillar + 3), SEO writing (pillar + 2), Repurposing (pillar + 2)
Cadence: Tue + Thu from 2026-01-05, 12 weeks, skipping 2026-01-19

calendar.csv - 10 posts, 3 pillars first, briefs due 7 days ahead, owners Ana/Ben
Columns: date, weekday, week, cluster, type, title, keyword, funnel, format, owner, status,
         brief_due, links_to, linkedin_date, newsletter_date

Fix before writing:
- 'content repurposing' is the keyword of 2 topics -> retarget "Turn One Blog Post into a
  LinkedIn Week" to "repurpose blog post for linkedin"
- "Newsletter Ideas from Old Posts" has no keyword -> "newsletter ideas"

Next: write briefs for weeks 1-2 (blog-post-writer), review on the first Monday of each month.
```
