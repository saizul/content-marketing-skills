---
name: newsletter-writer
description: Write email newsletters people open and reply to - issue formats (one big idea, curated links, how-to, case study, founder update), subject line and preview text formulas, a personal opener, one primary CTA, sign-off - then check the issue with a script - subject length, spam-trigger phrases, ALL CAPS, repeated punctuation, deceptive "RE:"/"FWD:" prefixes, emoji or a strict no-emoji mode, preview text missing, too short or long, repeating the subject or showing "View in browser", broken merge tags ({{first_name}}, *|FNAME|*, {% %}) and missing fallbacks, vague "click here" links, too many CTAs, images without alt text, very long issues and a missing unsubscribe link. Use when the user asks to write, outline, edit or check a newsletter, email issue, subject line, preview text or preheader, or plans a Substack, beehiiv, Kit (ConvertKit), Mailchimp or MailerLite send.
license: MIT
compatibility: Python 3.8+ standard library only. Works offline on Markdown/text; never sends email or calls an email platform.
metadata:
  author: Saizul Amin
  version: "0.1.0"
---

# Newsletter writer

A newsletter is a letter from a person: one clear reason to open, one thing to do, an
easy way to reply. Draft it, check it, and leave sending to the user.

Paths below are relative to this skill's folder (in Claude Code: `${CLAUDE_SKILL_DIR}`).

## When to use

- "Write this week's newsletter", "turn these notes/links into an issue"
- "Give me subject lines and preview text for...", "check this email before I send it"
- Setting up a recurring format for a founder, freelancer or agency newsletter

## When not to use

- Repurposing one blog post into a newsletter section among other channels:
  `content-repurposing` (then check the result here)
- Deliverability infrastructure (SPF, DKIM, DMARC, warm-up, blocklists): outside this skill
- Ranking many subject lines only: `headline-testing --type email` is faster

## Workflow

1. **Context.** Ask: the list (who subscribed and why), the issue goal (reply, click,
   book, buy), the platform (merge tag syntax differs), the regular format, and whether
   emoji are allowed (default: none).
2. **Choose the format** from [references/structure.md](references/structure.md) and
   outline: opener, the main piece, optional extras, one primary CTA, sign-off.
3. **Write the body** in a personal voice: first person, short paragraphs, one idea per
   paragraph, descriptive link text. Use the platform's merge tags with a fallback.
4. **Write 5 subject lines + matching preview texts** with
   [references/subject-lines.md](references/subject-lines.md). The preview continues the
   subject; it never repeats it. Optionally rank subjects with `headline-testing`.
5. **Save as Markdown** with frontmatter and **check (read-only):**
   ```markdown
   ---
   subject: "The 20-minute brief that fixed our calendar"
   preview: "One template, three questions and the links to add before anyone writes."
   ---
   ```
   ```bash
   python3 scripts/check_newsletter.py issue.md
   python3 scripts/check_newsletter.py issue.md --no-emoji --fail-on low --json
   python3 scripts/check_newsletter.py --subject "Five hooks we stole" --preview "Plus the one we dropped."
   ```
   Exit 1 when a finding is at or above `--fail-on` (default `medium`). With only
   `--subject`/`--preview`, body checks are skipped.
6. **Fix** high and medium findings. For `compliance.unsubscribe`, confirm the platform adds
   the footer (most do automatically); legal basics are in
   [references/compliance.md](references/compliance.md).
7. **Deliver** the final subject, preview, body and the check result; suggest a test send
   to the user's own inbox on mobile and desktop. Never send or schedule it yourself.

## Output

```
Subject (43): The 20-minute brief that fixed our calendar
Preview (88): One template, three questions and the internal links to add before anyone writes.
Alternatives: "Why our content calendar stopped slipping" / "3 questions every brief answers"

Body: 260 words (~1 min), 1 primary CTA (Get the brief template), reply prompt
Check: no findings (merge tag {{first_name | default: "there"}}, unsubscribe in footer)

Next: send a test to yourself; pick the subject with an A/B test if the list is 2,000+.
```
