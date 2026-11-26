---
name: content-refresh
description: Find decaying blog posts from a Google Search Console export and plan the refresh - a script compares two periods (a Search Console "Compare" Pages.csv, two single-period CSVs, or daily rows from the Search Console API, BigQuery bulk export or Looker Studio), finds pages whose clicks dropped by a threshold, diagnoses each one (rankings slipped, demand fell or seasonality, CTR fell from SERP features or a weak snippet, collapsed from indexing or cannibalisation), ranks them by clicks lost, and lists striking-distance pages (position 4-20). Then a playbook maps each diagnosis to an action - update, rewrite the title and meta description, expand, consolidate and redirect, or leave alone. Use when the user says traffic dropped, posts are losing clicks, asks for content decay analysis, a content audit, which posts to update or refresh, or shares a Search Console CSV.
license: MIT
compatibility: Python 3.8+ standard library only. Works offline on CSV exports; never calls Google APIs.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# Content refresh

Refresh the posts that lost the most, for the reason they lost it. The script does the
period comparison and diagnosis; you confirm with the page and its queries before
recommending work.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Our blog traffic is down", "which posts should we update?", "find decaying content"
- Quarterly content audits for a client or your own site
- The user shares Search Console Pages.csv, Queries.csv or an API/BigQuery export

## When not to use

- Site-wide technical drops (all pages fell on one day, manual action, migration): check
  Search Console's Pages (indexing) report, Manual actions and recent site changes first
- Writing the refreshed post: `blog-post-writer` (this skill decides what to fix)
- Planning new topics: `editorial-calendar` (feed it the refresh list as priority-1 rows)

## Workflow

1. **Get the export** (the user downloads it; never ask for Google credentials):
   Search Console > Performance > Search results > Date > **Compare** (e.g. last 3 months
   vs previous period) > Pages tab > Export > Download CSV, then unzip and use
   `Pages.csv`. The UI export holds at most 1,000 rows; for bigger sites use the
   Search Console API, the BigQuery bulk export, or Looker Studio. Compare equal-length
   periods; for seasonal sites compare year over year.
2. **Run the finder (read-only):**
   ```bash
   python3 scripts/find_decay.py Pages.csv
   python3 scripts/find_decay.py Pages.csv --min-clicks 20 --min-drop 25 --opportunities
   python3 scripts/find_decay.py last-3m.csv --previous prev-3m.csv --json
   python3 scripts/find_decay.py daily.csv --split-date 2026-09-01 --csv-out decay.csv
   ```
   - A page decays when previous clicks >= `--min-clicks` (10), clicks fell by >=
     `--min-drop` percent (20) and by >= `--min-loss` clicks (5).
   - Column detection: the column whose header says "previous"/"prior"/"before" is the
     older period. If headers do not say, pass `--current-label`/`--previous-label`.
     Comma, tab and semicolon files, `1,234` and `3.5%` values are handled.
   - Exit 1 when decaying pages are found (`--exit-zero` to suppress), 2 on bad input.
3. **Sanity-check the top results** before advising: compare total clicks (is the whole
   site down?), look for known events (migration, redesign, algorithm update dates,
   seasonality), and for the top 5 pages open the Queries tab filtered to that page.
4. **Decide per page** with [references/refresh-playbook.md](references/refresh-playbook.md):
   - `rankings_slipped` -> content refresh (update, expand, improve intent match, links)
   - `ctr_fell` -> rewrite title tag and meta description (`headline-testing`), check
     what now sits above the result
   - `demand_fell` -> usually leave it or update the angle/year; do not rewrite for nothing
   - `collapsed` -> technical/cannibalisation check before touching content
   - `mixed` -> review top queries, refresh the sections they map to
5. **Present a prioritised refresh list** (clicks lost x business value) and ask the user
   which pages to tackle; then produce a refresh brief per page (checklist in the
   playbook). Do not edit or redirect pages without explicit approval.
6. **Measure**: note the refresh date per URL and compare 4-8 weeks later with the same
   script and equal-length periods.

## Output

```
Pages.csv: 412 rows; clicks 18,240 -> 14,905 (-18.3%); 23 decaying

-830  (-45%) /blog/content-calendar/      ctr_fell          CTR 4.5% -> 2.5% at pos 5.8 -> 6.1
      -> rewrite title + meta (keep keyword first), check new SERP features
-560  (-88%) /blog/black-friday-email-ideas/  demand_fell   seasonal: compare year over year, update for 2026 in October
-410  (-57%) /blog/seo-copywriting/        rankings_slipped  pos 8.9 -> 14.2 -> full refresh brief below
-148  (-99%) /blog/old-tool-review/        collapsed         URL Inspection: canonical points to /tools/ -> consolidate?

Refresh this sprint: seo-copywriting (brief), content-calendar (titles). Leave: black-friday until October.
```
