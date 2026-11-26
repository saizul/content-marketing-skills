#!/usr/bin/env python3
"""Check a LinkedIn post draft before publishing.

Checks: the 3,000-character limit, hook length (what shows before "...see more"),
weak openers, walls of text and line breaks, hashtag count, links in the body,
emoji (or none at all with --no-emoji), tag spam, Unicode "bold" letters that screen
readers cannot read, shouting in capitals and a closing call to action.

Read-only, offline. Input: a text/Markdown file, - for stdin, or --text.

Exit codes: 0 = no findings at or above --fail-on, 1 = findings, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

LINKEDIN_MAX = 3000
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}
URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s<>()]+|\b[a-z0-9-]+\.(?:com|io|co|org|net|dev|app|ai)/[^\s]*", re.I)
HASHTAG_RE = re.compile(r"(?<![\w&])#([A-Za-z][\w]*)")
MENTION_RE = re.compile(r"(?<![\w.])@[A-Z][\w-]*(?:\s[A-Z][\w-]*)?")
WEAK_OPENERS = re.compile(
    r"^(i'?m (so )?(excited|thrilled|happy|delighted|proud|humbled) to|i am (so )?(excited|thrilled|happy|delighted|"
    r"proud|humbled)|hello (everyone|linkedin|connections)|hi (everyone|all|linkedin)|happy (monday|friday|"
    r"tuesday|wednesday|thursday)|just a quick (post|note)|in today'?s (fast-paced|world)|have you ever wondered)",
    re.I,
)
CTA_RE = re.compile(
    r"\?|\b(comment|share|repost|follow|dm me|message me|reply|tell me|let me know|save this|subscribe|"
    r"book a|grab|download|join|sign up|check out|thoughts|agree)\b",
    re.I,
)


def is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x1F300 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x27BF
        or 0x1F000 <= cp <= 0x1F2FF
        or 0x1F1E6 <= cp <= 0x1F1FF
        or cp in (0x2B50, 0x2B55, 0x2B06, 0x2B07, 0x2B05, 0x2934, 0x2935, 0x3030, 0x303D, 0x203C)
        or (0x2190 <= cp <= 0x21FF and unicodedata.category(ch) == "So")
    )


def is_fancy_letter(ch: str) -> bool:
    """Mathematical alphanumeric symbols used by 'bold text generators'."""
    return 0x1D400 <= ord(ch) <= 0x1D7FF


def check(text: str, no_emoji: bool = False, max_hashtags: int = 5, allow_links: bool = False) -> dict:
    findings: list[dict] = []

    def add(sev: str, check_id: str, message: str, fix: str = ""):
        findings.append({"severity": sev, "check": check_id, "message": message, "fix": fix})

    text = text.replace("\r\n", "\n").strip("\n")
    chars = len(text)
    lines = text.split("\n")
    non_empty = [ln for ln in lines if ln.strip()]
    hook = non_empty[0].strip() if non_empty else ""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    hashtags = HASHTAG_RE.findall(text)
    urls = URL_RE.findall(text)
    emoji = [ch for ch in text if is_emoji(ch)]
    fancy = [ch for ch in text if is_fancy_letter(ch)]
    mentions = MENTION_RE.findall(text)
    caps = [w for w in re.findall(r"\b[A-Z]{5,}\b", text) if w not in {"LINKEDIN"}]

    if not text.strip():
        add("high", "post.empty", "the post is empty")
        return {"chars": 0, "findings": findings, "hook": "", "stats": {}}
    if chars > LINKEDIN_MAX:
        add("high", "length.over_limit", f"{chars} characters; LinkedIn allows {LINKEDIN_MAX}", "cut or split it")
    elif chars > 2200:
        add("low", "length.long", f"{chars} characters", "long posts work only if every line earns its place")
    elif chars < 250:
        add("info", "length.short", f"{chars} characters", "fine for a one-liner; add context if it is a story")

    if len(hook) > 150:
        add("medium", "hook.too_long", f"first line is {len(hook)} chars", "make the hook one line under ~150 chars")
    if len(hook.split()) > 20:
        add("low", "hook.wordy", f"hook has {len(hook.split())} words", "8-15 words is easier to scan")
    if WEAK_OPENERS.match(hook):
        add("medium", "hook.weak_opener", f"generic opener: '{hook[:60]}'", "lead with the result, tension or number")
    preview = text[:210]
    if "\n" not in preview and chars > 210:
        add("low", "hook.no_break", "no line break in the first 210 chars", "break after the hook so it stands alone")

    if chars > 400 and len(paragraphs) == 1:
        add("medium", "format.wall_of_text", "no blank lines in a long post", "one idea per short paragraph")
    walls = [p for p in paragraphs if len(p) > 300 or p.count("\n") >= 3 and len(p) > 200]
    if walls and len(paragraphs) > 1:
        add("low", "format.long_paragraph", f"{len(walls)} paragraph(s) over ~3 lines", "split them")

    if len(hashtags) > max_hashtags:
        add("medium", "hashtags.too_many", f"{len(hashtags)} hashtags", f"use {max_hashtags} or fewer relevant ones")
    lower_tags = [h.lower() for h in hashtags]
    if len(set(lower_tags)) < len(lower_tags):
        add("low", "hashtags.duplicate", "duplicate hashtags", "remove repeats")
    if hashtags and any(HASHTAG_RE.search(ln) for ln in non_empty[:1]):
        add("low", "hashtags.in_hook", "hashtag in the hook", "keep the first line clean; tags go at the end")

    if urls and not allow_links:
        where = "hook" if URL_RE.search(hook) else "body"
        add(
            "medium" if where == "hook" else "low",
            "links.in_post",
            f"{len(urls)} link(s) in the {where}",
            "many creators see less reach with links; consider the first comment, or pass --allow-links",
        )

    if no_emoji and emoji:
        add("high", "emoji.present", f"{len(emoji)} emoji found but --no-emoji is set", "remove them")
    elif len(emoji) > 6:
        add("low", "emoji.many", f"{len(emoji)} emoji", "use a few as signposts, not decoration")
    if fancy:
        add(
            "medium",
            "format.unicode_bold",
            f"{len(fancy)} 'fancy' Unicode letters",
            "screen readers and search cannot read them; use plain text",
        )
    if len(mentions) > 5:
        add("low", "mentions.many", f"{len(mentions)} @mentions", "tag only people who are in the story")
    if len(caps) > 3:
        add("low", "format.shouting", f"{len(caps)} ALL-CAPS words", "use capitals sparingly")

    closing = paragraphs[-1] if paragraphs else ""
    closing_wo_tags = HASHTAG_RE.sub("", closing).strip()
    if not closing_wo_tags and len(paragraphs) > 1:
        closing_wo_tags = paragraphs[-2]
    if not CTA_RE.search(closing_wo_tags):
        add("low", "cta.missing", "no question or call to action at the end", "end with one specific ask")

    findings.sort(key=lambda f: -SEVERITY_ORDER[f["severity"]])
    return {
        "chars": chars,
        "hook": hook,
        "stats": {
            "chars": chars,
            "words": len(text.split()),
            "lines": len(non_empty),
            "paragraphs": len(paragraphs),
            "hashtags": len(hashtags),
            "links": len(urls),
            "emoji": len(emoji),
            "mentions": len(mentions),
        },
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Check a LinkedIn post: length, hook, line breaks, hashtags, links, emoji, CTA.",
        epilog="Example: check_post.py draft.txt --no-emoji --fail-on medium",
    )
    p.add_argument("path", nargs="?", help="text file, or - for stdin")
    p.add_argument("--text", help="post text given inline instead of a file")
    p.add_argument("--no-emoji", action="store_true", help="treat any emoji as a high finding")
    p.add_argument("--max-hashtags", type=int, default=5, help="maximum hashtags (default 5)")
    p.add_argument("--allow-links", action="store_true", help="do not report links in the post")
    p.add_argument("--fail-on", choices=list(SEVERITY_ORDER), default="medium", help="exit 1 threshold")
    p.add_argument("--json", action="store_true", help="print JSON")
    args = p.parse_args(argv)
    try:
        if args.text is not None:
            text = args.text
        elif args.path in (None, "-"):
            text = sys.stdin.read()
        else:
            with open(args.path, encoding="utf-8") as fh:
                text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result = check(text, no_emoji=args.no_emoji, max_hashtags=args.max_hashtags, allow_links=args.allow_links)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        s = result["stats"]
        print(
            f"LinkedIn post: {s.get('chars', 0)}/{LINKEDIN_MAX} chars, {s.get('paragraphs', 0)} paragraphs, "
            f"{s.get('hashtags', 0)} hashtags, {s.get('links', 0)} links, {s.get('emoji', 0)} emoji"
        )
        print(f"Hook: {result['hook'][:150]}")
        for f in result["findings"]:
            fix = f"  -> {f['fix']}" if f["fix"] else ""
            print(f"{f['severity'].upper():6} {f['check']}: {f['message']}{fix}")
        if not result["findings"]:
            print("No findings.")
    threshold = SEVERITY_ORDER[args.fail_on]
    return 1 if any(SEVERITY_ORDER[f["severity"]] >= threshold for f in result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
