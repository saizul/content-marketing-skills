#!/usr/bin/env python3
"""Score a Markdown blog draft: structure, keyword placement, readability and E-E-A-T signals.

Checks headings (one H1, no skipped levels, enough H2s, long sections), the focus keyword
in title / H1 / first 100 words / an H2 / slug / meta description, keyword stuffing,
meta title and description length, word count, Flesch reading ease, sentence length,
passive voice, long paragraphs, images without alt text, internal and external links,
and signals of experience and trust (author, dates, first-hand wording, data, sources).

Read-only. Works offline on one Markdown file (YAML frontmatter optional) or stdin.

Exit codes: 0 = score >= --min-score, 1 = score below --min-score, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

SEVERITY_PENALTY = {"high": 15, "medium": 7, "low": 3, "info": 0}
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}

ABBREVIATIONS = ["e.g.", "i.e.", "etc.", "vs.", "Mr.", "Mrs.", "Ms.", "Dr.", "Inc.", "Ltd.", "approx.", "No."]
BE_VERBS = r"(?:am|is|are|was|were|be|been|being|get|gets|got|gotten|getting)"
IRREGULAR_PARTICIPLES = (
    "known written given taken made done seen shown built found held kept left lost paid sent sold "
    "told thought brought bought caught taught chosen driven eaten fallen forgotten hidden broken "
    "spoken stolen worn torn born drawn grown thrown flown blown begun sung swum understood read "
    "led fed met won spent lent meant heard felt hit hurt shut split spread"
).split()
NOT_PARTICIPLES = {"need", "seed", "feed", "speed", "bleed", "breed", "greed", "indeed", "embed", "proceed", "exceed"}
PASSIVE_RE = re.compile(
    rf"\b{BE_VERBS}\s+(?:\w+ly\s+)?(\w+ed|{'|'.join(IRREGULAR_PARTICIPLES)})\b",
    re.I,
)
EXPERIENCE_RE = re.compile(
    r"\b(I|we)\s+(tested|tried|built|ran|used|measured|found|learned|launched|shipped|interviewed|surveyed|analy[sz]ed)\b"
    r"|\bin my experience\b|\bour (data|clients|customers|team|results|test|tests)\b|\bcase study\b"
    r"|\bwhen I\b|\bI've\b|\bwe've\b",
    re.I,
)
DATA_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|percent|x\b|times\b|hours?\b|days?\b|users?\b|clients?\b)", re.I)
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")


# --------------------------------------------------------------------------- parsing


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter dict of simple scalars and lists, body)."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if lines[0].strip() != "---":
        return {}, text
    data: dict = {}
    key = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() in ("---", "..."):
            return data, "\n".join(lines[i + 1 :])
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1).lower(), m.group(2).strip()
            if value.startswith("[") and value.endswith("]"):
                data[key] = [_unquote(v.strip()) for v in value[1:-1].split(",") if v.strip()]
            else:
                data[key] = _unquote(value)
        elif key and re.match(r"^\s+-\s+", line):
            item = _unquote(re.sub(r"^\s+-\s+", "", line).strip())
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(item)
    return {}, text


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def strip_inline(text: str) -> str:
    """Remove Markdown/HTML inline syntax, keeping visible text."""
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(\*\*|__|\*|_|~~)(?=\S)(.+?)(?<=\S)\1", r"\2", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_markdown(body: str) -> dict:
    """Split a Markdown body into headings, paragraphs, images and links (code blocks skipped)."""
    headings: list[dict] = []
    paragraphs: list[str] = []
    images: list[dict] = []
    links: list[str] = []
    in_code = False
    current: list[str] = []
    section_words: list[int] = [0]

    def flush():
        if current:
            para = strip_inline(" ".join(current))
            if para:
                paragraphs.append(para)
                section_words[-1] += len(WORD_RE.findall(para))
            current.clear()

    for line_no, raw in enumerate(body.splitlines(), start=1):
        line = raw.rstrip()
        if re.match(r"^\s*(```|~~~)", line):
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        images += [{"alt": a.strip(), "line": line_no} for a in re.findall(r"!\[([^\]]*)\]\([^)]*\)", line)]
        images += [
            {"alt": (re.search(r'alt\s*=\s*"([^"]*)"', tag) or [None, ""])[1].strip(), "line": line_no}
            for tag in re.findall(r"<img\b[^>]*>", line, re.I)
        ]
        links += re.findall(r"(?<!!)\[[^\]]+\]\(([^)\s]+)[^)]*\)", line)
        links += re.findall(r'<a\s[^>]*href="([^"]+)"', line, re.I)
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            flush()
            headings.append({"level": len(m.group(1)), "text": strip_inline(m.group(2)), "line": line_no})
            section_words.append(0)
            continue
        if not line.strip() or re.match(r"^\s*(\|.*\||[-*_]{3,})\s*$", line):
            flush()
            continue
        item = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$", line)
        if item:
            flush()
            current.append(item.group(1))
            flush()
            continue
        current.append(re.sub(r"^\s*>\s?", "", line))
    flush()
    return {
        "headings": headings,
        "paragraphs": paragraphs,
        "images": images,
        "links": links,
        "section_words": section_words,
    }


def split_sentences(text: str) -> list[str]:
    protected = text
    for abbr in ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", "․"))
    parts = re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"'(\[])", protected)
    return [p.replace("․", ".").strip() for p in parts if WORD_RE.search(p)]


def count_syllables(word: str) -> int:
    w = word.lower().strip("'")
    if not w:
        return 0
    if w.isdigit():
        return max(1, len(w) // 2)
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def is_passive(sentence: str) -> bool:
    for m in PASSIVE_RE.finditer(sentence):
        if m.group(1).lower() not in NOT_PARTICIPLES:
            return True
    return False


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def contains_phrase(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    pattern = r"\b" + r"[\s-]+".join(re.escape(w) for w in phrase.lower().split()) + r"\b"
    return re.search(pattern, text.lower()) is not None


def count_phrase(text: str, phrase: str) -> int:
    pattern = r"\b" + r"[\s-]+".join(re.escape(w) for w in phrase.lower().split()) + r"\b"
    return len(re.findall(pattern, text.lower()))


# --------------------------------------------------------------------------- analysis


def analyze(text: str, keyword: str | None = None, min_words: int = 800, site: str | None = None) -> dict:
    fm, body = parse_frontmatter(text)
    doc = parse_markdown(body)
    findings: list[dict] = []

    def add(sev: str, check: str, message: str, fix: str = ""):
        findings.append({"severity": sev, "check": check, "message": message, "fix": fix})

    keyword = (keyword or fm.get("keyword") or fm.get("focus_keyword") or "").strip() or None
    headings = doc["headings"]
    h1s = [h for h in headings if h["level"] == 1]
    h2s = [h for h in headings if h["level"] == 2]
    title = fm.get("title") or (h1s[0]["text"] if h1s else "")
    description = fm.get("description") or fm.get("meta_description") or ""
    prose = " ".join(doc["paragraphs"])
    words = WORD_RE.findall(prose)
    n_words = len(words)
    sentences = [s for p in doc["paragraphs"] for s in split_sentences(p)]
    n_sent = max(1, len(sentences))
    syllables = sum(count_syllables(w) for w in words)
    sent_lengths = [len(WORD_RE.findall(s)) for s in sentences]
    long_sent = [s for s, n in zip(sentences, sent_lengths) if n > 25]
    passive = [s for s in sentences if is_passive(s)]
    flesch = 206.835 - 1.015 * (n_words / n_sent) - 84.6 * (syllables / max(1, n_words)) if n_words else 0.0
    grade = 0.39 * (n_words / n_sent) + 11.8 * (syllables / max(1, n_words)) - 15.59 if n_words else 0.0

    # Structure
    if len(h1s) > 1:
        add(
            "high", "structure.multiple_h1", f"{len(h1s)} H1 headings", "keep one H1 (the title); demote the rest to H2"
        )
    elif not h1s and not fm.get("title"):
        add("high", "structure.no_title", "no H1 and no frontmatter title", "add a '# Title' or title: in frontmatter")
    elif not h1s:
        add("info", "structure.title_from_frontmatter", "no H1; assuming the site renders frontmatter title as H1")
    prev = 1
    for h in headings:
        if h["level"] > prev + 1:
            add(
                "medium",
                "structure.skipped_level",
                f"line {h['line']}: H{h['level']} '{h['text']}' follows H{prev}",
                f"use H{prev + 1}",
            )
        prev = h["level"]
    if n_words >= 300 and len(h2s) < 2:
        add("medium", "structure.few_h2", f"{len(h2s)} H2 sections for {n_words} words", "add H2s every 200-350 words")
    for i, count in enumerate(doc["section_words"]):
        if count > 400:
            where = headings[i - 1]["text"] if i > 0 else "intro"
            add("low", "structure.long_section", f"section '{where}' has {count} words", "split it with an H3 or list")
    if n_words < min_words:
        add(
            "medium" if n_words < min_words * 0.6 else "low",
            "structure.word_count",
            f"{n_words} words (target {min_words}+)",
            "cover the questions searchers ask; do not pad",
        )
    long_paras = [p for p in doc["paragraphs"] if len(WORD_RE.findall(p)) > 120]
    if long_paras:
        add(
            "low", "readability.long_paragraphs", f"{len(long_paras)} paragraph(s) over 120 words", "2-4 sentences each"
        )

    # Hook
    if doc["paragraphs"]:
        intro_sents = split_sentences(doc["paragraphs"][0])
        if intro_sents and len(WORD_RE.findall(intro_sents[0])) > 30:
            add(
                "low", "hook.long_first_sentence", "first sentence is over 30 words", "open with a short, specific line"
            )
        if re.match(r"^(in this (article|post|blog)|in today's|welcome to|have you ever)", doc["paragraphs"][0], re.I):
            add("low", "hook.generic_opening", "intro opens with a generic phrase", "lead with the problem or a result")

    # Meta
    if fm:
        if title and len(title) > 60:
            add("medium", "meta.title_length", f"title is {len(title)} chars (Google shows ~50-60)", "shorten to <= 60")
        elif title and len(title) < 25:
            add("low", "meta.title_length", f"title is only {len(title)} chars", "add the benefit or a qualifier")
        if not description:
            add("medium", "meta.no_description", "no meta description in frontmatter", "write 120-160 chars")
        elif not 70 <= len(description) <= 160:
            add("low", "meta.description_length", f"meta description is {len(description)} chars", "aim for 120-160")

    # Keyword
    kw: dict = {}
    if keyword:
        first100 = " ".join(words[:100])
        slug = fm.get("slug") or ""
        kw = {
            "keyword": keyword,
            "in_title": contains_phrase(title, keyword),
            "in_h1": any(contains_phrase(h["text"], keyword) for h in h1s) if h1s else contains_phrase(title, keyword),
            "in_first_100_words": contains_phrase(first100, keyword),
            "in_h2": any(contains_phrase(h["text"], keyword) for h in h2s),
            "in_slug": contains_phrase(slug.replace("-", " "), keyword) if slug else None,
            "in_description": contains_phrase(description, keyword) if description else None,
            "occurrences": count_phrase(prose, keyword),
        }
        kw["density_pct"] = round(100 * kw["occurrences"] * len(keyword.split()) / max(1, n_words), 2)
        if not kw["in_title"]:
            add("high", "keyword.title", f"'{keyword}' is not in the title", "put it near the start of the title")
        if not kw["in_first_100_words"]:
            add("medium", "keyword.intro", f"'{keyword}' is not in the first 100 words", "mention it in the intro")
        if h2s and not kw["in_h2"]:
            add("low", "keyword.h2", f"'{keyword}' (or a close variant) is in no H2", "use it in one H2 naturally")
        if kw["in_slug"] is False:
            add("low", "keyword.slug", f"slug '{slug}' lacks the keyword", f"e.g. {slugify(keyword)}")
        if kw["in_description"] is False:
            add("low", "keyword.description", "meta description lacks the keyword", "include it once")
        if kw["density_pct"] > 2.5:
            add(
                "medium", "keyword.stuffing", f"keyword density {kw['density_pct']}%", "use synonyms; write for readers"
            )
    else:
        add("info", "keyword.none", "no focus keyword given", "pass --keyword or set keyword: in frontmatter")

    # Readability
    if n_words:
        if flesch < 50:
            add(
                "medium",
                "readability.flesch",
                f"Flesch reading ease {flesch:.0f} (hard)",
                "shorter sentences and words",
            )
        elif flesch < 60:
            add("low", "readability.flesch", f"Flesch reading ease {flesch:.0f}", "aim for 60+ for a general audience")
        avg = n_words / n_sent
        if avg > 20:
            add("medium", "readability.sentence_length", f"average sentence is {avg:.1f} words", "aim for 15-20")
        if len(long_sent) / n_sent > 0.2:
            add(
                "low",
                "readability.long_sentences",
                f"{len(long_sent)} of {len(sentences)} sentences exceed 25 words",
                "split the longest ones",
            )
        if len(passive) / n_sent > 0.1:
            add(
                "low",
                "readability.passive_voice",
                f"{len(passive)} of {len(sentences)} sentences look passive ({100 * len(passive) / n_sent:.0f}%)",
                "name who does what",
            )

    # Media and links
    missing_alt = [i for i in doc["images"] if not i["alt"]]
    if missing_alt:
        lines = ", ".join(str(i["line"]) for i in missing_alt)
        add(
            "medium",
            "media.missing_alt",
            f"{len(missing_alt)} image(s) without alt text (lines {lines})",
            "describe them",
        )
    internal, external = classify_links(doc["links"], site)
    if not internal:
        add("medium", "links.no_internal", "no internal links", "link 2-5 related posts (see internal-linking skill)")
    if not external:
        add("low", "links.no_external", "no external sources cited", "link primary sources for claims and data")

    # E-E-A-T signals
    signals = {
        "author": bool(fm.get("author") or fm.get("authors")),
        "date": bool(fm.get("date") or fm.get("published") or fm.get("updated") or fm.get("lastmod")),
        "first_hand_experience": bool(EXPERIENCE_RE.search(prose)),
        "data_or_numbers": len(DATA_RE.findall(prose)) >= 2,
        "external_sources": bool(external),
    }
    if fm and not signals["author"]:
        add("low", "eeat.author", "no author in frontmatter", "add an author with a bio page")
    if fm and not signals["date"]:
        add("low", "eeat.date", "no published/updated date", "show dates; update them when you refresh")
    if not signals["first_hand_experience"]:
        add("low", "eeat.experience", "no first-hand wording found", "add what you tested, built or saw with clients")
    if not signals["data_or_numbers"]:
        add("low", "eeat.data", "few or no concrete numbers", "add results, benchmarks or examples with numbers")

    penalty = sum(SEVERITY_PENALTY[f["severity"]] for f in findings)
    findings.sort(key=lambda f: -SEVERITY_ORDER[f["severity"]])
    return {
        "title": title,
        "score": max(0, 100 - penalty),
        "metrics": {
            "words": n_words,
            "sentences": len(sentences),
            "paragraphs": len(doc["paragraphs"]),
            "h1": len(h1s),
            "h2": len(h2s),
            "flesch_reading_ease": round(flesch, 1),
            "fk_grade": round(grade, 1),
            "avg_sentence_words": round(n_words / n_sent, 1) if n_words else 0,
            "long_sentences": len(long_sent),
            "passive_sentences": len(passive),
            "images": len(doc["images"]),
            "internal_links": len(internal),
            "external_links": len(external),
        },
        "keyword": kw,
        "eeat_signals": signals,
        "findings": findings,
        "examples": {"long_sentences": long_sent[:3], "passive_sentences": passive[:3]},
    }


def classify_links(links: list[str], site: str | None) -> tuple[list[str], list[str]]:
    internal, external = [], []
    host = re.sub(r"^https?://", "", site or "").strip("/").lower()
    for link in links:
        if link.startswith(("mailto:", "tel:", "#")):
            continue
        if re.match(r"^https?://", link, re.I):
            link_host = re.sub(r"^https?://", "", link, flags=re.I).split("/")[0].lower()
            if host and (link_host == host or link_host == "www." + host or "www." + link_host == host):
                internal.append(link)
            else:
                external.append(link)
        else:
            internal.append(link)
    return internal, external


# --------------------------------------------------------------------------- CLI


def format_report(result: dict) -> str:
    m = result["metrics"]
    out = [
        f'Draft score: {result["score"]}/100  "{result["title"]}"',
        f"{m['words']} words, {m['sentences']} sentences, H2 x{m['h2']}, Flesch {m['flesch_reading_ease']}, "
        f"grade {m['fk_grade']}, avg sentence {m['avg_sentence_words']} words, "
        f"passive {m['passive_sentences']}, links {m['internal_links']} internal / {m['external_links']} external",
    ]
    kw = result["keyword"]
    if kw:
        marks = [k.replace("in_", "") for k, v in kw.items() if k.startswith("in_") and v]
        out.append(f"Keyword '{kw['keyword']}': in {', '.join(marks) or 'nothing'}; density {kw['density_pct']}%")
    sig = result["eeat_signals"]
    out.append("E-E-A-T signals: " + ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in sig.items()))
    out.append("")
    for f in result["findings"]:
        fix = f"  -> {f['fix']}" if f["fix"] else ""
        out.append(f"{f['severity'].upper():6} {f['check']}: {f['message']}{fix}")
    for s in result["examples"]["long_sentences"]:
        out.append(f"  long: {s[:140]}")
    for s in result["examples"]["passive_sentences"]:
        out.append(f"  passive?: {s[:140]}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Score a Markdown blog draft (structure, keyword placement, readability, E-E-A-T signals).",
        epilog="Example: score_draft.py post.md --keyword 'content calendar' --min-score 75",
    )
    p.add_argument("path", help="Markdown file, or - for stdin")
    p.add_argument("--keyword", help="focus keyword (default: frontmatter keyword:)")
    p.add_argument("--min-words", type=int, default=800, help="target word count (default 800)")
    p.add_argument("--min-score", type=int, default=70, help="exit 1 below this score (default 70)")
    p.add_argument("--site", help="your domain, so absolute links to it count as internal (example.com)")
    p.add_argument("--json", action="store_true", help="print JSON")
    args = p.parse_args(argv)
    try:
        if args.path == "-":
            text = sys.stdin.read()
        else:
            with open(args.path, encoding="utf-8") as fh:
                text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result = analyze(text, keyword=args.keyword, min_words=args.min_words, site=args.site)
    print(json.dumps(result, indent=2) if args.json else format_report(result))
    return 1 if result["score"] < args.min_score else 0


if __name__ == "__main__":
    sys.exit(main())
