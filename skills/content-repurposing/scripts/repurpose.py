#!/usr/bin/env python3
"""Turn one Markdown blog post into first drafts for LinkedIn, an X thread, a newsletter and a short video.

Extracts the title, intro, H2 sections, the first sentence of each section and
sentences with numbers, then fills channel templates within each channel's limits:
LinkedIn (<= 3,000 chars, link in first comment), X thread (<= 280 weighted chars per
post, URLs count as 23), newsletter (subject options, preview text, takeaways, one CTA),
and a 45-60 second vertical video script (~2.5 spoken words per second).

The output is a deterministic scaffold built only from the post's own sentences; the
agent then rewrites it in the author's voice. No emoji are added. Read-only on input;
with --out it writes one file per channel and refuses to overwrite without --force.

Exit codes: 0 = drafts produced, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

CHANNELS = ("linkedin", "x", "newsletter", "video")
X_LIMIT = 280
X_URL_WEIGHT = 23
LINKEDIN_LIMIT = 3000
WORDS_PER_SECOND = 2.5
URL_RE = re.compile(r"https?://\S+")
WRAP_UP = re.compile(
    r"^(conclusion|summary|final thoughts|wrapping up|wrap-up|key takeaways|takeaways|faqs?|"
    r"frequently asked questions|what to do next|next steps|further reading|resources|references)\b",
    re.I,
)


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
            data[m.group(1).lower()] = m.group(2).strip().strip("\"'")
    return {}, text


def clean(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1", r"\2", text)
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    protected = re.sub(r"\b(e\.g|i\.e|etc|vs|Dr|Mr|Ms|Mrs)\.", lambda m: m.group(0).replace(".", "․"), text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", protected)
    return [p.replace("․", ".").strip() for p in parts if len(p.split()) >= 3]


def parse_post(text: str) -> dict:
    fm, body = parse_frontmatter(text)
    body = re.sub(r"(?ms)^(```|~~~).*?^\1\s*$", "", body)
    title = fm.get("title", "")
    intro: list[str] = []
    sections: list[dict] = []
    current = None
    para: list[str] = []

    def flush():
        if para:
            p = clean(" ".join(para))
            if p:
                (current["paragraphs"] if current else intro).append(p)
            para.clear()

    for line in body.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*$", line)
        if m:
            flush()
            level, heading = len(m.group(1)), clean(m.group(2))
            if level == 1 and not title:
                title = heading
            elif level == 2:
                current = {"heading": heading, "paragraphs": []}
                sections.append(current)
            elif current is not None:
                current["paragraphs"].append(heading + ".")
            continue
        if not line.strip() or re.match(r"^\s*(\|.*\||[-*_]{3,})\s*$", line):
            flush()
            continue
        item = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$", line)
        if item:
            flush()
            para.append(item.group(1).rstrip(".") + ".")
            flush()
            continue
        para.append(re.sub(r"^\s*>\s?", "", line))
    flush()
    all_sents = [s for p in intro for s in sentences(p)] + [
        s for sec in sections for p in sec["paragraphs"] for s in sentences(p)
    ]
    stats = [s for s in all_sents if re.search(r"\d", s) and len(s) <= 220]
    points = []
    for sec in sections:
        if WRAP_UP.match(sec["heading"]):
            continue
        first = next((s for p in sec["paragraphs"] for s in sentences(p)), "")
        points.append({"heading": sec["heading"], "point": first})
    return {
        "title": title or "Untitled",
        "description": fm.get("description", ""),
        "url": fm.get("url") or fm.get("canonical") or "",
        "intro": intro,
        "points": points,
        "stats": stats,
        "sentences": all_sents,
    }


def shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 3].rsplit(" ", 1)[0].rstrip(",;:-")
    return cut + "..."


def x_length(text: str) -> int:
    """X counts every URL as 23 characters."""
    return len(URL_RE.sub("x" * X_URL_WEIGHT, text))


def hook_line(post: dict) -> str:
    if post["stats"]:
        return shorten(post["stats"][0], 150)
    if post["intro"]:
        first = sentences(post["intro"][0])
        if first:
            return shorten(first[0], 150)
    return shorten(post["title"], 150)


def context_line(post: dict) -> str:
    """First intro sentence that is not already the hook."""
    hook = hook_line(post)
    for s in (s for p in post["intro"] for s in sentences(p)):
        if shorten(s, 150) != hook:
            return s
    return ""


def linkedin(post: dict, cta: str | None, max_points: int) -> str:
    lines = [hook_line(post), ""]
    context = context_line(post)
    if context:
        lines += [shorten(context, 220), ""]
    points = [p for p in post["points"] if p["heading"]][:max_points]
    if points:
        lines.append(f"{len(points)} things that matter:")
        lines.append("")
        for i, p in enumerate(points, 1):
            detail = shorten(p["point"], 160) if p["point"] else ""
            lines.append(f"{i}. {p['heading']}" + (f": {detail}" if detail else ""))
            lines.append("")
    lines.append(cta or "Which of these are you working on right now?")
    if post["url"]:
        lines += ["", "(Full post linked in the first comment.)"]
    text = "\n".join(lines).strip() + "\n"
    if len(text) > LINKEDIN_LIMIT and len(points) > 1:
        return linkedin(post, cta, len(points) - 1)
    return text


def split_for_x(text: str, limit: int) -> list[str]:
    if x_length(text) <= limit:
        return [text]
    out, cur = [], ""
    for s in sentences(text) or [text]:
        candidate = f"{cur} {s}".strip()
        if x_length(candidate) <= limit:
            cur = candidate
            continue
        if cur:
            out.append(cur)
        cur = s if x_length(s) <= limit else shorten(s, limit)
    if cur:
        out.append(cur)
    return out


def x_thread(post: dict, cta: str | None, max_points: int) -> list[str]:
    budget = X_LIMIT - 8  # room for " 10/12"
    raw = [hook_line(post) + "\n\nThe short version, in a thread:"]
    for p in post["points"][:max_points]:
        body = p["heading"] + (f"\n\n{p['point']}" if p["point"] else "")
        raw += split_for_x(body, budget)
    closing = cta or "If this was useful, follow for more like it."
    if post["url"]:
        closing = f"Full post with examples: {post['url']}\n\n{closing}"
    raw += split_for_x(closing, budget)
    n = len(raw)
    return [f"{t} {i}/{n}" for i, t in enumerate(raw, 1)]


def newsletter(post: dict, cta: str | None, max_points: int) -> dict:
    title = post["title"]
    subjects = [shorten(title, 50)]
    if post["stats"]:
        subjects.append(shorten(post["stats"][0].rstrip("."), 50))
    if post["points"]:
        subjects.append(shorten("This week: " + post["points"][0]["heading"], 50))
    preview_src = post["description"] or (post["sentences"][0] if post["sentences"] else title)
    preview = shorten(preview_src, 110)
    if preview.lower().startswith(subjects[0].lower()):
        preview = shorten(post["sentences"][1] if len(post["sentences"]) > 1 else preview_src, 110)
    intro = post["intro"][0] if post["intro"] else ""
    body = ["Hi {{first_name | default: 'there'}},", "", shorten(intro, 400), ""]
    body.append("This week's takeaways:")
    body.append("")
    for p in post["points"][:max_points]:
        body.append(f"- **{p['heading']}**" + (f" {shorten(p['point'], 180)}" if p["point"] else ""))
    body.append("")
    link = post["url"] or "{{post_url}}"
    body.append(f"[{cta or 'Read the full post'}]({link})")
    body += ["", "Reply and tell me what you would add. I read every reply.", "", "[Unsubscribe]({{unsubscribe_url}})"]
    return {"subjects": subjects, "preview": preview, "body": "\n".join(body) + "\n"}


def video(post: dict, cta: str | None, max_points: int, seconds: int) -> dict:
    budget = int(seconds * WORDS_PER_SECOND)
    beats = [("HOOK", hook_line(post))]
    setup = context_line(post)
    if setup:
        beats.append(("SETUP", shorten(setup, 160)))
    for p in post["points"][: min(max_points, 3)]:
        beats.append(("POINT", shorten(p["point"] or p["heading"], 180)))
    beats.append(("CTA", cta or "Full breakdown is linked in my profile. Follow for part two."))
    words = sum(len(b[1].split()) for b in beats)
    while words > budget and sum(1 for b in beats if b[0] == "POINT") > 1:
        idx = max(i for i, b in enumerate(beats) if b[0] == "POINT")
        beats.pop(idx)
        words = sum(len(b[1].split()) for b in beats)
    t = 0
    timed = []
    for kind, line in beats:
        dur = max(2, round(len(line.split()) / WORDS_PER_SECOND))
        timed.append({"time": f"{t}-{t + dur}s", "beat": kind, "say": line, "on_screen": on_screen(kind, line, post)})
        t += dur
    notes = []
    hook_words = len(beats[0][1].split())
    if hook_words > 8:
        notes.append(f"hook is {hook_words} words (~{round(hook_words / WORDS_PER_SECOND)}s); cut it to 8 or fewer")
    if words < budget * 0.6:
        notes.append(f"{words} words for a {seconds}s target; add an example or a number to each POINT")
    return {"seconds_estimate": round(words / WORDS_PER_SECOND), "words": words, "beats": timed, "notes": notes}


def on_screen(kind: str, line: str, post: dict) -> str:
    if kind == "HOOK":
        return shorten(post["title"], 40)
    if kind == "POINT":
        for p in post["points"]:
            if p["point"] and p["point"][:40] in line or p["heading"] in line:
                return shorten(p["heading"], 40)
    if kind == "CTA":
        return "Link in profile"
    return shorten(line, 40)


def render(post: dict, channels: list[str], cta: str | None, max_points: int, seconds: int) -> dict:
    out: dict = {"title": post["title"], "source_points": len(post["points"])}
    if "linkedin" in channels:
        text = linkedin(post, cta, max_points)
        out["linkedin"] = {"text": text, "chars": len(text)}
    if "x" in channels:
        thread = x_thread(post, cta, max_points)
        out["x"] = {"posts": thread, "lengths": [x_length(t) for t in thread]}
    if "newsletter" in channels:
        out["newsletter"] = newsletter(post, cta, max_points)
    if "video" in channels:
        out["video"] = video(post, cta, max_points, seconds)
    return out


def to_markdown(result: dict) -> dict:
    files = {}
    if "linkedin" in result:
        li = result["linkedin"]
        files["linkedin.md"] = f"<!-- LinkedIn draft: {li['chars']}/{LINKEDIN_LIMIT} chars -->\n\n{li['text']}"
    if "x" in result:
        parts = [
            f"<!-- post {i}: {n}/{X_LIMIT} -->\n{t}"
            for i, (t, n) in enumerate(zip(result["x"]["posts"], result["x"]["lengths"]), 1)
        ]
        files["x-thread.md"] = "\n\n---\n\n".join(parts) + "\n"
    if "newsletter" in result:
        nl = result["newsletter"]
        subj = "\n".join(f"- {s}" for s in nl["subjects"])
        files["newsletter.md"] = (
            f'---\nsubject: "{nl["subjects"][0]}"\npreview: "{nl["preview"]}"\n---\n\n'
            f"<!-- subject options:\n{subj}\n-->\n\n{nl['body']}"
        )
    if "video" in result:
        v = result["video"]
        rows = "\n".join(f"| {b['time']} | {b['beat']} | {b['say']} | {b['on_screen']} |" for b in v["beats"])
        files["video-script.md"] = (
            f"# Short video script (~{v['seconds_estimate']}s, {v['words']} words)\n\n"
            f"| Time | Beat | Say | On screen |\n| --- | --- | --- | --- |\n{rows}\n"
            + "".join(f"\n- TODO: {n}" for n in v["notes"])
            + ("\n" if v["notes"] else "")
        )
    return files


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Draft LinkedIn, X thread, newsletter and short-video versions of a Markdown blog post.",
        epilog="Example: repurpose.py post.md --url https://example.com/blog/post/ --out drafts/post",
    )
    p.add_argument("path", help="Markdown blog post (- for stdin)")
    p.add_argument("--channels", default=",".join(CHANNELS), help="comma list of linkedin,x,newsletter,video")
    p.add_argument("--url", help="canonical URL of the post (default: frontmatter url/canonical)")
    p.add_argument("--cta", help="call to action to use instead of the defaults")
    p.add_argument("--max-points", type=int, default=5, help="maximum sections to use (default 5)")
    p.add_argument("--seconds", type=int, default=60, help="video length target in seconds (default 60)")
    p.add_argument("--out", help="folder to write one Markdown file per channel")
    p.add_argument("--force", action="store_true", help="overwrite files in --out")
    p.add_argument("--json", action="store_true", help="print JSON")
    args = p.parse_args(argv)
    channels = [c.strip().lower() for c in args.channels.split(",") if c.strip()]
    bad = [c for c in channels if c not in CHANNELS]
    if bad or not channels:
        print(f"error: unknown channel(s) {bad}; choose from {', '.join(CHANNELS)}", file=sys.stderr)
        return 2
    try:
        if args.path == "-":
            text = sys.stdin.read()
        else:
            with open(args.path, encoding="utf-8") as fh:
                text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    post = parse_post(text)
    if args.url:
        post["url"] = args.url
    if not post["points"]:
        print("warning: no H2 sections found; drafts use the intro only", file=sys.stderr)
    result = render(post, channels, args.cta, args.max_points, args.seconds)
    files = to_markdown(result)
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        existing = [f for f in files if os.path.exists(os.path.join(args.out, f))]
        if existing and not args.force:
            print(f"error: {', '.join(existing)} exist in {args.out}; pass --force", file=sys.stderr)
            return 2
        for name, content in files.items():
            with open(os.path.join(args.out, name), "w", encoding="utf-8") as fh:
                fh.write(content)
        print(f"wrote {', '.join(files)} to {args.out}", file=sys.stderr)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif not args.out:
        for name, content in files.items():
            print(f"===== {name}\n{content}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
