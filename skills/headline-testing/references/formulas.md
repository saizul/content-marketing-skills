# Headline formulas

Each formula with a template and an example for the topic "content calendar".

| # | Formula | Template | Example |
| --- | --- | --- | --- |
| 1 | How-to | How to [achieve outcome] [without pain / in time] | How to Build a Content Calendar in One Afternoon |
| 2 | Numbered list | [N] [things] to/for [outcome] | 7 Content Calendar Templates for Small Teams |
| 3 | Mistakes | [N] [topic] Mistakes That [cost] | 5 Content Calendar Mistakes That Waste Your Budget |
| 4 | Question | [Specific question the reader asks]? | How Often Should a Small Team Publish? |
| 5 | Why | Why [common belief] [is wrong / fails] | Why Most Content Calendars Fail by Week Three |
| 6 | Without | [Outcome] Without [common pain] | A Content Calendar Without Spreadsheets Hell |
| 7 | Result in time | How We [result] in [time] | How We Doubled Output in 90 Days with One Calendar |
| 8 | Comparison | [X] vs [Y]: [which is better for whom] | Notion vs Sheets: Which Content Calendar Fits Your Team? |
| 9 | Guide / asset | The [adjective] [topic] [guide/checklist/template] | The Practical Content Calendar Checklist |
| 10 | Bracket qualifier | [Headline] ([Template] / [2026] / [Examples]) | Content Calendar Template (Free Sheet + Examples) |
| 11 | Audience call-out | [Topic] for [specific audience] | Content Calendars for Two-Person Marketing Teams |
| 12 | Contrarian | Stop [common practice]. Do [this] Instead | Stop Planning a Year Ahead. Plan 8 Weeks Instead |

## Rules by channel

| Channel (`--type`) | Ideal length | Notes |
| --- | --- | --- |
| `seo` (title tag) | 40-60 chars | Google truncates by pixel width (about 600 px); keyword near the start; brand at the end only if room |
| `blog` (H1) | 40-70 chars | Can be longer and more descriptive than the title tag |
| `email` (subject) | 25-50 chars | The first ~30-40 chars carry it on mobile; no fake "RE:"/"FWD:" |
| `social` (hook) | 40-110 chars | Must make sense alone, before "see more" |

## Scoring used by score_headlines.py

| Part | Points | Rule |
| --- | --- | --- |
| length | 25 | full inside the ideal band; -1 per char short, -2 per char long |
| words | 10 | 6-12 words |
| number | 10 | digit or number word |
| power words | 15 | 1 word = 10, 2 = 15, 3 = 12, more = 6 (hype) |
| formula | 15 | any formula detected |
| keyword | 15 | only with `--keyword`: present in first half 15, second half 10 |
| clarity | 10 | minus clickbait (10), ALL CAPS (4), `!!`/`??` (4), vague words (3), fake reply (10) |

Without `--keyword`, the total is scaled from 85 to 100.

## Honesty rules

- Every number in a headline must be true for the content ("7 mistakes" means 7 sections).
- No curiosity gaps the content does not close.
- "Free" only if it is free without a sales call.
