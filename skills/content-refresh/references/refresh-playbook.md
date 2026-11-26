# Refresh playbook

## Diagnoses used by find_decay.py

Checked in this order; the first match wins.

| Diagnosis | Rule | Typical causes |
| --- | --- | --- |
| `collapsed` | current clicks <= 10% of previous | deindexed, noindex, wrong canonical, redirect, another URL of yours now ranks (cannibalisation), page removed |
| `rankings_slipped` | average position worse by >= 1.0 | competitors updated, content outdated, intent shifted, lost links, core update |
| `demand_fell` | impressions down >= `--min-drop` % with position within 1.0 | seasonality, fading trend, queries moved to other phrasing |
| `ctr_fell` | CTR down >= 20% relative, visibility similar | AI answers, featured snippets, ads, video or "People also ask" above you; a competitor's better title; Google rewrote your title |
| `mixed` | none of the above | several small losses; look at queries |

Average position in Search Console is impression-weighted and moves when the mix of
queries changes; treat a change under 1.0 as noise.

## Actions

### Rankings slipped: content refresh

1. Open the page's top 10 queries (Performance > filter Page > Queries) for both periods.
2. Compare with what ranks now for the top 2-3 queries: format, depth, freshness, sections
   you do not cover. Do not copy; find the gap.
3. Refresh brief:
   - Update facts, screenshots, prices, years, tool names
   - Add sections for questions now in "People also ask" / new queries
   - Add first-hand experience: results, examples, mistakes (see `blog-post-writer`)
   - Tighten the intro: the answer in the first 100 words
   - Add 2-3 internal links from strong related posts (see `internal-linking`)
   - Keep the URL. Update the visible "updated" date only for substantial changes
4. Request indexing in URL Inspection after publishing.

### CTR fell: snippet rewrite

- Rewrite the title tag (keyword first, specific benefit, number or year if true) and the
  meta description (the promise + proof). Use `headline-testing --type seo`.
- Check the live SERP: if an AI answer or featured snippet now answers the query fully,
  aim for the snippet (a direct 40-60 word answer under a question H2) or accept lower
  CTR and focus on queries with deeper intent.
- Add structured data where it applies (for example Article). Do not expect rich results
  from HowTo or FAQ markup: Google retired HowTo rich results and shows FAQ rich results
  only for a small set of authoritative sites.

### Demand fell: usually wait

- Check Google Trends for the head query and year-over-year Search Console data.
- Seasonal pages: refresh 4-6 weeks before the season, not after it ends.
- If the topic is fading for good, merge the page into a broader one.

### Collapsed: investigate before writing

1. URL Inspection: indexed? Which canonical did Google choose? Last crawl?
2. Is there a newer URL of yours ranking for the same queries (Performance > Queries >
   pick the query > Pages tab)? If yes: consolidate into the stronger page and 301 the other.
3. Check robots.txt, noindex tags, redirects and recent template changes.

## Consolidate, redirect or prune

| Situation | Action |
| --- | --- |
| Two posts compete for the same queries | merge the best parts into the stronger URL, 301 the weaker |
| Thin post with no clicks, no links, no purpose | improve it, merge it, or remove it (410/404) |
| Outdated post with backlinks | update it, or 301 to the closest current page |
| Post with conversions but falling traffic | refresh first; never delete converting pages |

Redirects and deletions change the live site: list them for the user and let them apply.

## Prioritising

Priority = clicks lost x value per visit (leads, signups, revenue). A BOFU comparison
page losing 50 clicks can matter more than a TOFU guide losing 500. Refresh 3-5 pages per
sprint, measure after 4-8 weeks, then do the next batch.

## Export notes

- The Search Console UI export is limited to 1,000 rows per table and anonymises rare
  queries; totals in the export may differ from the chart totals.
- Daily per-page data (API, BigQuery bulk export, Looker Studio) avoids the row limit;
  use `--split-date` to set the first day of the current period.
- Compare equal-length periods with the same weekdays (28 vs 28 days, 3 vs 3 months).
