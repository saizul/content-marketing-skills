---
name: internal-linking
description: Suggest internal links between blog posts with a script that reads a folder of Markdown/MDX/HTML files (Hugo, Jekyll, Astro, Next.js, Eleventy, Gatsby, exported WordPress HTML) - titles, URLs from frontmatter slug/permalink/url or canonical tags, keywords and tags, existing links - compares posts by TF-IDF keyword overlap, proposes source -> target links with a natural anchor phrase found in the source text and the sentence it sits in, skips pairs that are already linked, and lists orphan pages nobody links to. Covers hub-and-spoke cluster linking, anchor text rules and how many links to add. Use when the user asks for internal links, internal linking suggestions, related posts, orphan pages, topic cluster linking, "which posts should link to this new post", or wants to improve site structure for SEO from a content folder.
license: MIT
compatibility: Python 3.8+ standard library only. Works offline on local files; never crawls a live site and never edits posts.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# Internal linking

Find the links a human editor would add if they remembered every post: relevant, with
anchor text that already exists in the sentence. The script proposes; the user approves
every edit.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Suggest internal links for my blog", "which old posts should link to this new one?"
- Finding orphan posts (no internal links point to them)
- Building hub-and-spoke links for a topic cluster
- After a content refresh or migration, to rebuild links

## When not to use

- Live-site crawling, broken-link checks or redirects: use a crawler; this skill reads files
- External link building or outreach
- Navigation menus and footers: site design, not in-content links

## Workflow

1. **Locate the content folder** (e.g. `content/posts`, `src/content/blog`, `_posts`, an
   HTML export). Ask for the site domain so absolute links to it count as internal.
2. **Run the suggester (read-only):**
   ```bash
   python3 scripts/suggest_links.py content/posts --site example.com
   python3 scripts/suggest_links.py content/ --site example.com --max-per-page 5 --csv links.csv
   python3 scripts/suggest_links.py content/ --only new-post.md --json
   python3 scripts/suggest_links.py content/ --fail-on-orphans     # CI: exit 1 if orphans
   ```
   URLs come from frontmatter `url`/`permalink`, then `slug` (in the file's folder), then
   the path (`blog/2026-01-05-my-post.md` -> `/blog/my-post/`). Links already in a post
   (relative `.md` links, root-relative, absolute same-site) are skipped. HTML nav,
   header, footer and aside are ignored.
3. **Review the suggestions** with [references/linking-rules.md](references/linking-rules.md):
   - Accept when the target answers a question the source raises at that sentence.
   - Prefer suggestions with an `anchor` (phrase already in the text). For `anchor_hint`
     ones, propose a short sentence edit and show it.
   - Spokes link up to the pillar; the pillar links down to every spoke.
   - Fix orphans first: each needs at least 2-3 inbound links from related posts.
4. **Propose edits as a diff or a table** (file, sentence before, sentence after) and
   **wait for approval** before editing files. Keep the author's sentence; only wrap the
   anchor. Never link the same target twice from one post, and never more than one link
   per sentence.
5. **Apply approved edits** and re-run the script to confirm the links are detected and
   the orphan count dropped.

## Output

```
42 posts, 118 existing internal links, 61 suggestions, 4 orphans

content-brief.md -> /content-calendar/  anchor "content calendar"  score 0.41
  in: "Good briefs also list the internal links to add, such as the pillar page for the content calendar."
  edit: link "content calendar" in that sentence to /content-calendar/

Orphans: /guides/linkedin-hooks/ (suggest links from repurposing.html, content-calendar.md)

Applied 9 of 12 proposed links (3 rejected: weak relevance). Re-run: 3 orphans left.
```
