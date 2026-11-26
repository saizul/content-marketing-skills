# score_draft.py checks

Score = 100 - 15 x high - 7 x medium - 3 x low (info costs nothing), floored at 0.

| Check | Severity | Rule | Fix |
| --- | --- | --- | --- |
| `structure.multiple_h1` | high | more than one `# ` heading | one H1; demote others |
| `structure.no_title` | high | no H1 and no frontmatter title | add one |
| `structure.title_from_frontmatter` | info | no H1, frontmatter title present | fine for most static site generators |
| `structure.skipped_level` | medium | e.g. H2 followed by H4 | use the next level |
| `structure.few_h2` | medium | 300+ words and fewer than 2 H2s | add sections |
| `structure.long_section` | low | 400+ words under one heading | split with H3s, lists, tables |
| `structure.word_count` | low/medium | under `--min-words` (medium under 60%) | answer more questions; never pad |
| `readability.long_paragraphs` | low | paragraph over 120 words | 2-4 sentences |
| `hook.long_first_sentence` | low | first sentence over 30 words | short, specific opener |
| `hook.generic_opening` | low | "In this article", "Have you ever", ... | lead with problem or result |
| `meta.title_length` | medium/low | title over 60 chars / under 25 | Google truncates by pixel width, ~50-60 chars |
| `meta.no_description` | medium | frontmatter without description | 120-160 chars |
| `meta.description_length` | low | outside 70-160 chars | Google may rewrite it anyway |
| `keyword.title` | high | keyword not in title | near the start |
| `keyword.intro` | medium | not in first 100 words | mention it naturally |
| `keyword.h2` | low | not in any H2 | one H2 with the keyword or a close variant |
| `keyword.slug` | low | slug lacks the keyword | short slug with the keyword |
| `keyword.description` | low | meta description lacks it | include once |
| `keyword.stuffing` | medium | density over 2.5% | synonyms, write for readers |
| `readability.flesch` | low/medium | Flesch reading ease < 60 / < 50 | shorter words and sentences |
| `readability.sentence_length` | medium | average over 20 words | split sentences |
| `readability.long_sentences` | low | over 20% of sentences exceed 25 words | split the longest |
| `readability.passive_voice` | low | over 10% of sentences look passive | name the actor |
| `media.missing_alt` | medium | image without alt text (Markdown or `<img>`) | describe the image |
| `links.no_internal` | medium | no relative or same-site links | 2-5 internal links |
| `links.no_external` | low | no external links | cite primary sources |
| `eeat.*` | low | missing author, date, first-hand wording, numbers | see eeat.md |

## Known limitations

- Passive voice is a regex (`is/was/were/been/get + -ed or irregular participle`), so
  "is interested" or "got tired" count as passive. Treat the examples as candidates.
- Flesch reading ease and grade are English formulas with heuristic syllable counts.
  For other languages, ignore the readability findings.
- Absolute links count as internal only with `--site example.com`.
- Keyword matching is exact-phrase (case and hyphen insensitive). Close variants and
  plurals are not matched; that is why `keyword.h2` is only low.
