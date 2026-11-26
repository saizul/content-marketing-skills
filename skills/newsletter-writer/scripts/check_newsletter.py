#!/usr/bin/env python3
"""Check a newsletter issue: subject line, preview text and body before sending.

Subject: missing, length (mobile inboxes cut ~40-50 chars), spam-trigger phrases,
ALL CAPS, repeated punctuation, fake "RE:"/"FWD:" prefixes, emoji (or any with
--no-emoji). Preview text: missing, too short/long, repeats the subject, "View in
browser" boilerplate. Body: broken or fallback-less merge tags ({{first_name}},
*|FNAME|*, {% %}), number of calls to action, "click here" links, images without alt
text, very long issues, a missing unsubscribe link, spam phrases.

Input: a Markdown/text file whose frontmatter has subject: and preview: (or pass
--subject / --preview). Read-only, offline; nothing is sent.

Exit codes: 0 = no findings at or above --fail-on, 1 = findings, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}
SPAM_PHRASES = [
    "100% free",
    "act now",
    "apply now",
    "buy now",
    "cash bonus",
    "click here",
    "dear friend",
    "double your",
    "earn money",
    "extra income",
    "free gift",
    "free money",
    "get paid",
    "guaranteed",
    "limited time only",
    "make money",
    "no cost",
    "no obligation",
    "order now",
    "risk-free",
    "risk free",
    "this is not spam",
    "urgent",
    "winner",
    "you have been selected",
    "$$$",
]
UNSUB_RE = re.compile(
    r"unsubscribe|\*\|unsub\|\*|\{\{\s*unsubscribe[\w_]*\s*\}\}|%unsubscribe%|\{\$unsubscribe\}|"
    r"\[unsubscribe\]|manage (your )?(preferences|subscription)|opt[- ]out",
    re.I,
)
TOKEN_RES = [
    ("{{", "}}"),
    ("{%", "%}"),
    ("*|", "|*"),
]
BOILERPLATE_PREVIEW = re.compile(
    r"^(view (this )?(email )?in (your )?browser|having trouble viewing|email not "
    r"displaying|can'?t see this email)",
    re.I,
)


def is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return 0x1F300 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or 0x1F000 <= cp <= 0x1F2FF or 0x1F1E6 <= cp <= 0x1F1FF


def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    data = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() in ("---", "..."):
            return data, "\n".join(lines[i + 1 :])
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            value = m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            data[m.group(1).lower()] = value
    return {}, text


def check_tokens(text: str, where: str, add) -> None:
    for start, end in TOKEN_RES:
        opens, closes = text.count(start), text.count(end)
        if opens != closes:
            add("high", "merge_tag.broken", f"{where}: {opens} '{start}' but {closes} '{end}'", "fix the merge tag")
    for tag in re.findall(r"\{\{\s*([^}]+?)\s*\}\}", text):
        name = tag.split("|")[0].strip().lower()
        if re.search(r"first_?name|fname|name$", name) and "|" not in tag and "default" not in tag:
            add("info", "merge_tag.no_fallback", f"{where}: {{{{{tag}}}}} has no fallback", "add a default ('there')")
    for tag in re.findall(r"\*\|([A-Z0-9_]+)\|\*", text):
        if tag in ("FNAME", "LNAME", "NAME"):
            add("info", "merge_tag.no_fallback", f"{where}: *|{tag}|* may be empty", "set a default merge value")


def spam_hits(text: str) -> list[str]:
    low = text.lower()
    return [p for p in SPAM_PHRASES if p in low]


def check(
    text: str, subject: str | None = None, preview: str | None = None, no_emoji: bool = False, max_words: int = 1200
) -> dict:
    fm, body = parse_frontmatter(text)
    subject = subject if subject is not None else fm.get("subject", "")
    preview = preview if preview is not None else fm.get("preview") or fm.get("preheader") or ""
    findings: list[dict] = []

    def add(sev: str, check_id: str, message: str, fix: str = ""):
        findings.append({"severity": sev, "check": check_id, "message": message, "fix": fix})

    # Subject
    s = subject.strip()
    if not s:
        add("high", "subject.missing", "no subject line", "add subject: to the frontmatter or pass --subject")
    else:
        if len(s) > 60:
            add("medium", "subject.long", f"subject is {len(s)} chars", "keep the point in the first ~40 chars")
        elif len(s) > 50:
            add("low", "subject.long", f"subject is {len(s)} chars", "mobile inboxes often cut around 40-50")
        elif len(s) < 12:
            add("low", "subject.short", f"subject is {len(s)} chars", "say what is inside")
        caps = [w for w in re.findall(r"\b[A-Z]{3,}\b", s) if w not in {"SEO", "API", "CEO", "USA", "FAQ", "AI"}]
        if len(caps) >= 2 or (s.isupper() and len(s) > 8):
            add("medium", "subject.caps", "subject shouts in capitals", "use sentence case")
        if re.search(r"[!?]{2,}", s) or s.count("!") > 1:
            add("medium", "subject.punctuation", "repeated ! or ?", "one mark at most")
        if re.match(r"^\s*(re|fwd?)\s*:", s, re.I):
            add("high", "subject.fake_reply", "subject fakes a reply or forward", "deceptive subjects break CAN-SPAM")
        hits = spam_hits(s)
        if hits:
            add("medium", "subject.spam_phrases", "spam-trigger phrases: " + ", ".join(hits), "rephrase plainly")
        emoji_s = [c for c in s if is_emoji(c)]
        if no_emoji and emoji_s:
            add("high", "emoji.subject", "emoji in subject but --no-emoji is set", "remove it")
        elif len(emoji_s) > 1:
            add("low", "emoji.subject", f"{len(emoji_s)} emoji in subject", "one at most, or none")
        check_tokens(s, "subject", add)

    # Preview text
    pv = preview.strip()
    if not pv:
        add("medium", "preview.missing", "no preview text", "inboxes will show the first body text instead")
    else:
        if BOILERPLATE_PREVIEW.match(pv):
            add("medium", "preview.boilerplate", "preview starts with browser-link boilerplate", "write a real teaser")
        if len(pv) < 35:
            add("low", "preview.short", f"preview is {len(pv)} chars", "40-130 chars; extend the subject's promise")
        elif len(pv) > 140:
            add("low", "preview.long", f"preview is {len(pv)} chars", "most clients show well under 140")
        if s and (pv.lower() == s.lower() or pv.lower().startswith(s.lower())):
            add("medium", "preview.repeats_subject", "preview repeats the subject", "add new information instead")
        if no_emoji and any(is_emoji(c) for c in pv):
            add("high", "emoji.preview", "emoji in preview but --no-emoji is set", "remove it")
        check_tokens(pv, "preview", add)

    # Body
    links = re.findall(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)[^)]*\)", body)
    html_links = re.findall(r"<a\s[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", body, re.I | re.S)
    anchors = [t for t, _ in links] + [re.sub(r"<[^>]+>", "", t) for _, t in html_links]
    hrefs = [u for _, u in links] + [u for u, _ in html_links]
    content_hrefs = {u for u in hrefs if not UNSUB_RE.search(u) and not u.startswith(("mailto:", "#"))}
    plain = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)|\[([^\]]+)\]\([^)]*\)", r"\1", body)
    words = re.findall(r"[A-Za-z0-9']+", plain)
    if not body.strip():
        add("medium", "body.empty", "no body text")
    if len(words) > max_words:
        add("low", "body.long", f"{len(words)} words", f"aim under {max_words} or link to the full post")
    if body.strip() and not content_hrefs:
        add("low", "cta.none", "no links in the body", "give readers one clear next step")
    elif len(content_hrefs) > 6:
        add("info", "cta.many", f"{len(content_hrefs)} different links", "make one primary CTA stand out")
    vague = [a for a in anchors if re.fullmatch(r"\s*(click )?here\s*|\s*link\s*|\s*read more\s*", a, re.I)]
    if vague:
        add("low", "cta.vague_anchor", f"{len(vague)} vague link text(s) ('here', 'read more')", "describe the target")
    missing_alt = re.findall(r"!\[\s*\]\(", body) + [
        t for t in re.findall(r"<img\b[^>]*>", body, re.I) if not re.search(r'alt\s*=\s*"[^"]+"', t)
    ]
    if missing_alt:
        add(
            "medium", "images.missing_alt", f"{len(missing_alt)} image(s) without alt text", "many clients block images"
        )
    if body.strip() and not UNSUB_RE.search(body):
        add(
            "medium",
            "compliance.unsubscribe",
            "no unsubscribe link or merge tag found",
            "confirm your email platform adds one; it is legally required for marketing email",
        )
    body_spam = spam_hits(plain)
    if len(body_spam) >= 3:
        add("low", "body.spam_phrases", "spam-trigger phrases: " + ", ".join(body_spam), "rephrase")
    if no_emoji and any(is_emoji(c) for c in body):
        add("high", "emoji.body", "emoji in body but --no-emoji is set", "remove them")
    check_tokens(body, "body", add)
    paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip() and not p.lstrip().startswith("#")]
    if paragraphs and len(re.findall(r"[A-Za-z0-9']+", paragraphs[0])) > 90:
        add("low", "body.slow_intro", "first paragraph is over 90 words", "get to the point in 2-3 sentences")

    findings.sort(key=lambda f: -SEVERITY_ORDER[f["severity"]])
    return {
        "subject": s,
        "preview": pv,
        "stats": {
            "subject_chars": len(s),
            "preview_chars": len(pv),
            "body_words": len(words),
            "links": len(content_hrefs),
            "reading_minutes": round(len(words) / 238, 1),
        },
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Check a newsletter issue: subject line, preview text, merge tags, CTA, alt text, unsubscribe.",
        epilog="Example: check_newsletter.py issue-42.md --no-emoji --fail-on medium",
    )
    p.add_argument("path", nargs="?", help="Markdown/text file with optional frontmatter (subject:, preview:)")
    p.add_argument("--subject", help="subject line (overrides frontmatter)")
    p.add_argument("--preview", help="preview text / preheader (overrides frontmatter)")
    p.add_argument("--no-emoji", action="store_true", help="treat any emoji as a high finding")
    p.add_argument("--max-words", type=int, default=1200, help="body length before a finding (default 1200)")
    p.add_argument("--fail-on", choices=list(SEVERITY_ORDER), default="medium", help="exit 1 threshold")
    p.add_argument("--json", action="store_true", help="print JSON")
    args = p.parse_args(argv)
    text = ""
    try:
        if args.path == "-":
            text = sys.stdin.read()
        elif args.path:
            with open(args.path, encoding="utf-8") as fh:
                text = fh.read()
        elif args.subject is None:
            print("error: give a file or --subject", file=sys.stderr)
            return 2
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result = check(text, args.subject, args.preview, args.no_emoji, args.max_words)
    if not args.path:
        result["findings"] = [
            f for f in result["findings"] if not f["check"].startswith(("body.", "cta.", "compliance."))
        ]
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        st = result["stats"]
        print(f"Subject ({st['subject_chars']}): {result['subject']}")
        print(f"Preview ({st['preview_chars']}): {result['preview']}")
        print(f"Body: {st['body_words']} words (~{st['reading_minutes']} min), {st['links']} distinct links")
        for f in result["findings"]:
            fix = f"  -> {f['fix']}" if f["fix"] else ""
            print(f"{f['severity'].upper():6} {f['check']}: {f['message']}{fix}")
        if not result["findings"]:
            print("No findings.")
    threshold = SEVERITY_ORDER[args.fail_on]
    return 1 if any(SEVERITY_ORDER[f["severity"]] >= threshold for f in result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
