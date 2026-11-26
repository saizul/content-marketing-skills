# Planning guide: clusters, funnel, cadence, input format

## Topic clusters

A cluster is one broad topic your buyers care about, covered by:

- **One pillar page**: the broad guide for the head term ("content calendar"). Long,
  updated, linked from every spoke.
- **4-8 spokes**: specific questions and long-tail keywords ("content calendar template",
  "how often to publish blog posts"). Each links up to the pillar and to 1-2 siblings.

How to find clusters:

1. List the 3-5 problems your offer solves. Each problem is a candidate cluster.
2. For each, collect questions from sales calls, support tickets, Search Console queries,
   "People also ask", Reddit/forums and competitor sitemaps.
3. Group questions that a single page could answer (same intent) into one topic. Different
   intent = different topic, even with similar words ("content calendar template" is a
   download; "content calendar examples" is inspiration).
4. Give each topic exactly **one** focus keyword. Two topics with one keyword compete with
   each other (cannibalisation); the script warns about this.

## Funnel mix

| Stage | Intent | Formats | Share for a young blog |
| --- | --- | --- | --- |
| TOFU (awareness) | learn, define, ideas | guides, explainers, lists | 40-50% |
| MOFU (consideration) | how to, compare approaches | how-tos, templates, case studies | 30-40% |
| BOFU (decision) | choose a provider/tool | comparisons, alternatives, pricing, "X for Y" | 15-25% |

Founders and agencies often over-produce TOFU. BOFU posts get less traffic but convert;
schedule at least one per cluster early.

## Cadence by team size

| Team | Sustainable cadence | Notes |
| --- | --- | --- |
| Solo founder / freelancer | 2-4 posts a month | batch writing; repurpose every post |
| 1 writer + 1 editor | 1-2 a week | brief a week ahead, edit within 2 days |
| Small agency pod (2-3 writers) | 2-3 a week per client | owners round-robin, monthly review |

Rules of thumb: fixed weekdays (readers and writers learn the rhythm), pillar pages first
(spokes need something to link up to), never two posts of the same cluster back to back
(the script interleaves clusters), keep one buffer slot a month for news or refreshes.

## Input format

CSV (header names are case-insensitive; only `cluster` and `title` are required):

```csv
cluster,title,keyword,type,funnel,format,priority,owner
Content planning,Content Calendar: The Complete Guide,content calendar,pillar,tofu,guide,1,
Content planning,Free Content Calendar Template,content calendar template,spoke,bofu,template,1,Ana
```

- `type`: `pillar` (also `hub`, `cornerstone`) or `spoke` (default)
- `funnel`: `tofu`/`mofu`/`bofu` (also `awareness`, `consideration`, `decision`)
- `priority`: lower numbers publish first within a cluster (default 100)
- `owner`: left empty, `--owners` assigns writers round-robin

JSON:

```json
{"clusters": [
  {"name": "Email",
   "pillar": {"title": "Email Newsletter Guide", "keyword": "email newsletter"},
   "topics": [{"title": "Subject Lines That Get Opened", "keyword": "newsletter subject lines"},
              "Preview Text Explained"]}
]}
```

## Output columns

`date, weekday, week, cluster, type, title, keyword, funnel, format, owner, status,
brief_due, links_to` and, with `--repurpose`, `linkedin_date, newsletter_date`.
`links_to` is the cluster's pillar title for every spoke: the minimum internal link.

## Brief template (one per row)

```
Title / keyword / funnel stage:
Reader and the problem they have right now:
Search intent (what they expect to find):
3-5 questions the post must answer:
Proof we can add (data, client example, screenshot):
Internal links: pillar page + 1-2 siblings
CTA (one):
```
