# E-E-A-T signals

E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) comes from Google's
Search Quality Rater Guidelines. It is not a single ranking factor; it describes what
helpful content looks like. Google's guidance on "helpful, reliable, people-first content"
asks similar questions: does the content show first-hand experience, would you trust it,
does it leave the reader satisfied?

Use only facts the user provides. Mark gaps with `[ADD: ...]` placeholders.

## Experience (first-hand)

- What you did, tested, built or saw: "We tried three posts a week for a quarter..."
- Screenshots, photos, before/after numbers with dates
- Mistakes you made and what you changed
- Client stories (with permission or anonymised: "a 12-person SaaS team")

## Expertise

- Specific steps, numbers and edge cases a beginner would not know
- Correct terminology, explained once
- Author bio with relevant background, linked from the post

## Authoritativeness

- Links to primary sources (official docs, studies, original data), not to rewrites of them
- Mentions or quotes from recognised practitioners (real, attributed, with permission)
- Internal links that show depth on the topic (the cluster)

## Trust

- Author name and published / updated dates on the page
- Claims backed by sources; numbers with their source and date
- Clear disclosure of affiliate links or that you sell the product discussed
- Contact and about pages reachable from the post

## Checklist the script approximates

| Signal | What `score_draft.py` looks for |
| --- | --- |
| author | `author:` or `authors:` in frontmatter |
| date | `date:`, `published:`, `updated:` or `lastmod:` |
| first-hand experience | phrases like "we tested", "I built", "our clients", "in my experience", "case study" |
| data | at least two numbers with units (%, x, days, users, clients) |
| sources | at least one external link |

The heuristics only show that signals exist, not that they are true or good. Read the post.
