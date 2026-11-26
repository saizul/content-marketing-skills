---
name: linkedin-post-writer
description: Write LinkedIn posts for founders, freelancers and agencies that get read and start conversations - hook formulas for the first line before "see more", body structures (story, listicle, contrarian take, how-to, lesson learned, case study), closing CTAs and a strict no-emoji mode - then check the draft with a script - 3,000-character limit, hook length and weak openers ("I'm excited to announce"), walls of text and line breaks, hashtag count and duplicates, links in the post body, emoji, Unicode "bold" letters, @mention spam, ALL CAPS and a missing call to action. Use when the user asks to write, rewrite, shorten or review a LinkedIn post, turn an idea, win, lesson or article into a LinkedIn post, wants a week of LinkedIn content, or asks for posts "without emojis".
license: MIT
compatibility: Python 3.8+ standard library only. Works offline on text you paste or save; never posts anything.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# LinkedIn post writer

One idea per post, a first line that earns the click on "see more", short lines, one ask
at the end. You draft; the script checks the mechanics. Posting is always the user's call.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Write a LinkedIn post about...", "make this sound less corporate", "shorten this post"
- Turning a client win, lesson, launch, opinion or blog post into a post
- Reviewing a draft before it goes out; batch-writing a week of posts
- The user wants posts with no emoji (common for B2B founders)

## When not to use

- Repurposing a whole article into several channels at once: `content-repurposing`
  (then polish its LinkedIn draft here)
- Choosing between many headline-style hooks: `headline-testing --type social` helps
- Scheduling or publishing: this skill never posts; hand the text to the user or their tool

## Workflow

1. **Get the raw material.** Ask for the one idea, the audience (who should stop
   scrolling), the proof (numbers, story details, screenshots) and the desired outcome
   (comments, DMs, profile visits, clicks). Ask whether emoji are allowed; default to none
   for B2B unless the user's past posts use them.
2. **Pick a structure** from [references/patterns.md](references/patterns.md): story,
   listicle, contrarian, how-to, lesson learned, case study or announcement-done-right.
3. **Write 3 hook options** (first line, under ~150 characters, ideally 8-15 words) and
   let the user choose, or pick the strongest and say why. The hook must make sense alone:
   LinkedIn shows roughly the first 2-3 lines (about 140-210 characters, depending on
   device) before "see more".
4. **Write the body**: one idea per paragraph, 1-3 short lines each, blank line between
   paragraphs, concrete details (numbers, names of tools, timeframes). Plain text only:
   no Markdown (LinkedIn shows `**` literally) and no Unicode "bold" generators.
5. **Close** with one specific question or action. Put 0-5 relevant hashtags at the end.
   If there is a link, suggest the first comment instead of the body and let the user
   decide (many creators report less reach for posts with external links; LinkedIn does
   not publish how its feed ranks posts).
6. **Check the draft (read-only):**
   ```bash
   python3 scripts/check_post.py draft.txt
   python3 scripts/check_post.py draft.txt --no-emoji --max-hashtags 3
   python3 scripts/check_post.py --text "$(pbpaste)" --allow-links --json
   ```
   Exit 1 when a finding is at or above `--fail-on` (default `medium`). Fix every high and
   medium finding; explain any low finding you keep on purpose.
7. **Deliver** the final text in a plain code block (so line breaks survive copying), the
   hook alternatives, the first comment text if a link was moved, and the check result.

## Output

````
Hook options:
1. We cut content production time by 40% without hiring.   <- chosen (number + tension)
2. Our clients stopped missing deadlines when we deleted one meeting.
3. Most content calendars fail in week three. Ours did too.

```
We cut our client's content production time by 40% without hiring.

Here is what changed:
...
What is the one step in your content process you would cut first?

#ContentMarketing #B2BMarketing
```

First comment: Full breakdown and the brief template: https://example.com/blog/briefs/
Check: 612/3000 chars, 2 hashtags, 0 links, 0 emoji - no findings
````
