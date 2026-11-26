# Internal linking rules

## Why it matters

Internal links help search engines discover pages, understand how they relate and which
pages you consider important; they help readers find the next useful page. Google's SEO
starter guide recommends descriptive anchor text and linking to relevant resources.

## How many

- New post: 3-5 contextual links out (pillar + related spokes + one BOFU page if natural)
  and 2-3 links in from older related posts.
- Pillar page: link to every spoke in its cluster.
- Spokes: one link up to the pillar, 1-2 to siblings.
- There is no magic number; stop when the next link would not help this reader.

## Anchor text

| Do | Avoid |
| --- | --- |
| Descriptive phrase that says what the target is: "content brief template" | "click here", "this post", "read more" |
| Vary anchors across posts pointing at the same target | The exact same keyword anchor on every post |
| Keep it short: 2-5 words inside a natural sentence | Whole sentences as links |
| One link per sentence | Several links stacked together |

## Where

- In the body, where the reader has the question the target answers. Links in the first
  half of a post get seen more.
- Not in headings.
- Not to redirected or noindexed URLs; link to the final canonical URL.

## Reading the script output

| Field | Meaning |
| --- | --- |
| `score` | Cosine similarity of TF-IDF vectors (words and two-word phrases; title and keywords weighted x3), +0.1 when an anchor phrase was found. 0.1-0.2 = loosely related, 0.3+ = strongly related. |
| `anchor` | A target keyword or title phrase found verbatim in the source text (case-insensitive) |
| `context` | The sentence containing the anchor; propose the edit there |
| `anchor_hint` | No phrase found; the best phrase to work into a sentence |
| `orphans` | Posts no other post in the set links to (nav and footer links are not counted) |

## Limitations

- Similarity is lexical: synonyms ("newsletter" vs "email list") do not match.
  Read the pair and judge relevance yourself.
- URL guessing from file paths may not match your router; set `url` or `permalink` in
  frontmatter, or check one suggestion against the live site.
- Shortcodes, MDX components and templating syntax are treated as text.
