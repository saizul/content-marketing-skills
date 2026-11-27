#!/usr/bin/env python3
"""Score and rank headline variants: length, word count, numbers, power words, formula and keyword.

Length targets depend on --type: seo (title tag, ~50-60 chars before Google truncates),
blog (on-page H1), email (subject line, <= 50 chars), social (LinkedIn/X hook). Flags
clickbait phrases, ALL CAPS, repeated punctuation and vague words.

--suffix adds the text your CMS appends to every title tag (for example " | Acme Blog")
before the length is scored, so the limit applies to what search results actually show.

The score is a heuristic for comparing variants of the same idea, not a prediction of
click-through rate. Real tests (search CTR, email A/B, social posts) decide.

Read-only, offline. Headlines come from arguments, --file (one per line) or stdin.

Exit codes: 0 = best headline scores >= --min-score, 1 = none reaches it, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

TYPES = {
    # ideal (min, max) characters, hard limit where truncation is likely
    "seo": (40, 60, 60),
    "blog": (40, 70, 90),
    "email": (25, 50, 60),
    "social": (40, 110, 150),
}
POWER_WORDS = set(
    """
    proven simple easy fast quick instant essential ultimate complete definitive practical actionable
    effortless surprising secret hidden little-known overlooked mistake mistakes avoid stop never always
    best worst new free exclusive powerful honest real truth brutal costly expensive cheap save boost
    grow double triple win lose fail failed failing broke broken fix eliminate crush skyrocket
    step-by-step beginner beginners expert experts pros lessons learned exactly without everything
    nobody everyone checklist template templates framework playbook blueprint guide
    """.split()
)
CLICKBAIT = [
    "you won't believe",
    "you will not believe",
    "will blow your mind",
    "mind-blowing",
    "what happened next",
    "this one trick",
    "one weird trick",
    "doctors hate",
    "shocking",
    "jaw-dropping",
    "will shock you",
    "changed my life forever",
]
VAGUE = {"things", "stuff", "tips and tricks", "various", "some", "nice", "good", "great"}
NUMBER_WORDS = r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|hundred)\b"
FORMULAS = [
    ("how-to", re.compile(r"^how (to|i|we)\b", re.I)),
    ("list", re.compile(r"^\d+\s+\w|^(" + NUMBER_WORDS[2:-2] + r")\s+\w", re.I)),
    ("question", re.compile(r"\?\s*$")),
    ("why", re.compile(r"^why\b", re.I)),
    ("guide", re.compile(r"\b(guide|playbook|checklist|template|framework|blueprint)\b", re.I)),
    ("comparison", re.compile(r"\bvs\.?\b|\bversus\b|\bor\b.+\?$", re.I)),
    ("mistakes", re.compile(r"\b(mistakes?|myths?|lessons|wrong)\b", re.I)),
    ("without", re.compile(r"\bwithout\b", re.I)),
    ("result", re.compile(r"\b(from \S+ to \S+|in \d+ (days|weeks|months|minutes|hours))\b", re.I)),
    ("bracket", re.compile(r"[\[(][^\])]+[\])]")),
]


def score_headline(text: str, kind: str = "seo", keyword: str | None = None, suffix: str = "") -> dict:
    h = re.sub(r"\s+", " ", text).strip()
    suffix = re.sub(r"\s+", " ", suffix or "")
    if h and suffix and h.lower().endswith(suffix.strip().lower()):
        suffix = ""  # the headline already carries the suffix; do not count it twice
    lo, hi, hard = TYPES[kind]
    chars = len(h) + len(suffix)
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", h)
    lower_words = [w.lower() for w in words]
    flags: list[str] = []
    parts: dict = {}

    # Length (25)
    if lo <= chars <= hi:
        parts["length"] = 25
    elif chars < lo:
        parts["length"] = max(0, 25 - (lo - chars))
        flags.append(f"short: {chars} chars (ideal {lo}-{hi})")
    else:
        parts["length"] = max(0, 25 - 2 * (chars - hi))
        flags.append(f"long: {chars} chars (ideal {lo}-{hi})")
    if chars > hard:
        flags.append(f"likely truncated after ~{hard} chars")
    if suffix and chars > hi >= len(h):
        flags.append(f"suffix {suffix.strip()!r} pushes it over {hi} chars; shorten the headline or the suffix")

    # Words (10)
    n = len(words)
    parts["words"] = 10 if 6 <= n <= 12 else max(0, 10 - 2 * (6 - n if n < 6 else n - 12))

    # Number (10)
    has_number = bool(re.search(r"\d", h) or re.search(NUMBER_WORDS, h, re.I))
    parts["number"] = 10 if has_number else 0

    # Power words (15)
    power = sorted({w for w in lower_words if w in POWER_WORDS})
    parts["power_words"] = {0: 0, 1: 10, 2: 15, 3: 12}.get(len(power), 6)
    if len(power) > 3:
        flags.append("many power words; may read as hype")

    # Formula (15)
    formulas = [name for name, rx in FORMULAS if rx.search(h)]
    parts["formula"] = 15 if formulas else 0

    # Keyword (15)
    if keyword:
        kw = keyword.lower().strip()
        pos = h.lower().find(kw)
        if pos == -1:
            parts["keyword"] = 0
            flags.append(f"missing keyword '{keyword}'")
        else:
            parts["keyword"] = 15 if pos <= len(h) / 2 else 10
            if pos > len(h) / 2:
                flags.append("keyword is in the second half; move it forward")
    else:
        parts["keyword"] = None

    # Clarity (10)
    clarity = 10
    lowered = h.lower()
    bait = [c for c in CLICKBAIT if c in lowered]
    if bait:
        clarity -= 10
        flags.append("clickbait: " + ", ".join(bait))
    caps = [w for w in words if len(w) >= 4 and w.isupper()]
    if caps:
        clarity -= 4
        flags.append("ALL CAPS: " + ", ".join(caps))
    if re.search(r"[!?]{2,}", h):
        clarity -= 4
        flags.append("repeated punctuation")
    vague = [v for v in VAGUE if re.search(rf"\b{re.escape(v)}\b", lowered)]
    if vague:
        clarity -= 3
        flags.append("vague: " + ", ".join(sorted(vague)))
    if kind == "email" and re.match(r"^(re|fwd?):", lowered):
        clarity -= 10
        flags.append("fake reply/forward prefix is deceptive")
    parts["clarity"] = max(0, clarity)

    scored = {k: v for k, v in parts.items() if v is not None}
    max_points = 100 if keyword else 85
    total = round(100 * sum(scored.values()) / max_points)
    return {
        "headline": h,
        "title": h + suffix,
        "score": min(100, total),
        "chars": chars,
        "words": n,
        "has_number": has_number,
        "power_words": power,
        "formulas": formulas,
        "parts": parts,
        "flags": flags,
    }


def rank(headlines: list[str], kind: str = "seo", keyword: str | None = None, suffix: str = "") -> list[dict]:
    seen = set()
    results = []
    for h in headlines:
        key = h.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        results.append(score_headline(h, kind, keyword, suffix))
    return sorted(results, key=lambda r: (-r["score"], r["chars"]))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Score and rank headline variants (length, numbers, power words, formulas, keyword).",
        epilog="Example: score_headlines.py --type seo --keyword 'content calendar' 'How to ...' 'Content ...'",
    )
    p.add_argument("headlines", nargs="*", help="headlines to score (or use --file / stdin)")
    p.add_argument("--file", help="file with one headline per line (- for stdin)")
    p.add_argument("--type", choices=sorted(TYPES), default="seo", help="length targets (default seo)")
    p.add_argument("--keyword", help="focus keyword that should appear early")
    p.add_argument(
        "--suffix",
        default="",
        help="text appended to every title, e.g. ' | Acme Blog'; counted in the length score",
    )
    p.add_argument("--min-score", type=int, default=60, help="exit 1 if no headline reaches it (default 60)")
    p.add_argument("--json", action="store_true", help="print JSON")
    args = p.parse_args(argv)
    headlines = list(args.headlines)
    try:
        if args.file == "-" or (not headlines and not args.file and not sys.stdin.isatty()):
            headlines += sys.stdin.read().splitlines()
        elif args.file:
            with open(args.file, encoding="utf-8") as fh:
                headlines += fh.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    headlines = [h for h in headlines if h.strip() and not h.lstrip().startswith("#")]
    if not headlines:
        print("error: no headlines given", file=sys.stderr)
        return 2
    results = rank(headlines, args.type, args.keyword, args.suffix)
    if args.json:
        print(
            json.dumps(
                {"type": args.type, "keyword": args.keyword, "suffix": args.suffix, "results": results},
                indent=2,
            )
        )
    else:
        print(f"{'score':>5}  {'chars':>5}  headline")
        for r in results:
            print(f"{r['score']:>5}  {r['chars']:>5}  {r['headline']}")
            extras = []
            if r["formulas"]:
                extras.append("formula: " + ", ".join(r["formulas"]))
            if r["power_words"]:
                extras.append("power: " + ", ".join(r["power_words"]))
            extras += r["flags"]
            if extras:
                print(" " * 14 + "; ".join(extras))
    return 0 if results[0]["score"] >= args.min_score else 1


if __name__ == "__main__":
    sys.exit(main())
