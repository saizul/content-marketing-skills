---
name: content-repurposing
description: Turn one blog post into a LinkedIn post, an X (Twitter) thread, a newsletter section and a 45-60 second short video script (Reels, Shorts, TikTok) - a script extracts the title, sections, key sentences and numbers and builds first drafts within each channel's limits (LinkedIn 3,000 chars, X 280 per post with URLs counted as 23, subject and preview lengths, ~2.5 spoken words per second), then fill-in templates and channel rules guide the rewrite in the author's voice, without emoji unless asked. Use when the user asks to repurpose, recycle, atomize or "get more mileage" from a blog post or article, wants social posts, a thread, a newsletter or a video script from existing content, or plans a week of distribution for a new post.
license: MIT
compatibility: Python 3.8+ standard library only. Works offline on Markdown; writes files only to the --out folder you name.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# Content repurposing

One researched post, four native formats. The script builds a faithful scaffold from the
post's own sentences; you rewrite each piece so it reads as if written for that channel.
Nothing is posted or sent.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Repurpose this post", "turn this article into a LinkedIn post and a thread"
- "Write a newsletter section from last week's blog", "make a short video script from this"
- Planning distribution for a new post (day 1 LinkedIn, day 2 thread, Friday newsletter)

## When not to use

- Writing an original LinkedIn post without a source article: `linkedin-post-writer`
- A full newsletter issue with several stories: `newsletter-writer` (use this skill for
  the section about one post)
- The source post itself needs work: `blog-post-writer` first

## Workflow

1. **Get the source** as Markdown (frontmatter `title`, `description`, `url` help). For a
   web page, ask the user to paste it or save it as `.md`; do not scrape sites.
2. **Ask** the audience per channel, the CTA (newsletter signup, template, call), the
   canonical URL, and whether emoji are allowed (default: none).
3. **Generate the scaffold:**
   ```bash
   python3 scripts/repurpose.py post.md --url https://example.com/blog/post/
   python3 scripts/repurpose.py post.md --channels linkedin,x --cta "Get the template" --json
   python3 scripts/repurpose.py post.md --seconds 45 --max-points 4 --out drafts/post-slug
   ```
   `--out` writes `linkedin.md`, `x-thread.md`, `newsletter.md`, `video-script.md` and
   refuses to overwrite without `--force`. Wrap-up sections (Conclusion, FAQ, Next steps)
   are not used as points. A post without H2s produces intro-only drafts and a warning.
4. **Rewrite each draft** with the templates and rules:
   - LinkedIn: [assets/templates/linkedin.md](assets/templates/linkedin.md) - hook that
     stands alone, one idea, short lines, link in the first comment.
   - X thread: [assets/templates/x-thread.md](assets/templates/x-thread.md) - post 1 must
     work alone; each post one point; the link in the last post.
   - Newsletter: [assets/templates/newsletter.md](assets/templates/newsletter.md) - personal
     opener, why it matters to this list, 3 takeaways, one CTA.
   - Video: [assets/templates/video-script.md](assets/templates/video-script.md) - hook in
     under 3 seconds, one point per beat, on-screen text, spoken CTA.
   Channel limits and conventions: [references/channel-specs.md](references/channel-specs.md).
   Keep every claim traceable to the source post; never add new statistics.
5. **Check** the pieces: re-run `--json` and read `chars`, `lengths` and the video `notes`;
   if the companion skills are installed, run the LinkedIn checker from
   `linkedin-post-writer` and the newsletter checker from `newsletter-writer`.
6. **Deliver** each piece in its own code block plus a suggested schedule (for example:
   publish day, LinkedIn +1 workday, thread +2, newsletter on the next send day, video
   the following week).

## Output

````
Source: "Content Calendar for Small Teams" (4 sections, 2 numbers)

LinkedIn (612/3000, no emoji)
```
We tested this with 14 client sites: clusters with a pillar page got 38% more clicks.
...
```
First comment: https://example.com/blog/content-calendar/

X thread (6 posts, longest 241/280) - newsletter (subject 43 chars, preview 96) -
video script (52s, 130 words, 3 points)

Schedule: Tue publish, Wed LinkedIn, Thu thread, Fri newsletter, next Tue video
````
