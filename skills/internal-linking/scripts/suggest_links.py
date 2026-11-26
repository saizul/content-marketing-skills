#!/usr/bin/env python3
"""Suggest internal links between Markdown/HTML posts by keyword overlap, and find orphan pages.

For every post it reads the title, URL (frontmatter url/permalink/slug, HTML canonical,
or the file path), keywords (frontmatter keywords/tags/keyword) and body text, and the
internal links it already has. Posts are compared with TF-IDF over words and two-word
phrases; a target's keywords or title phrases that literally appear in the source text
become the suggested anchor text, with the sentence for context.

Pairs that are already linked are skipped. Orphans are posts no other post links to.

Read-only, offline. Input: files and/or folders (.md .markdown .mdx .html .htm).

Exit codes: 0 = ok, 1 = orphans found with --fail-on-orphans, 2 = error.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlparse

EXTS = (".md", ".markdown", ".mdx", ".html", ".htm")
STOPWORDS = set(
    """
    a about above after again against all also am an and any are as at be because been before being below
    between both but by can could did do does doing down during each few for from further get got had has
    have having he her here hers herself him himself his how i if in into is it its itself just let like
    make many me more most much my myself no nor not now of off on once only or other our ours ourselves
    out over own same she should so some such than that the their theirs them themselves then there these
    they this those through to too under until up us use used using very want was way we well were what
    when where which while who whom why will with without would you your yours yourself yourselves new
    one two three first next best need needs really thing things lot lots make makes made even every
    """.split()
)
WORD_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*")


# --------------------------------------------------------------------------- reading


class _HTMLText(HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "aside", "noscript", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.links: list[str] = []
        self.title = ""
        self.h1 = ""
        self.canonical = ""
        self.keywords = ""
        self._skip = 0
        self._in = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self._skip += 1
        elif tag == "a" and a.get("href") and not self._skip:
            self.links.append(a["href"])
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href") or ""
        elif tag == "meta" and (a.get("name") or "").lower() == "keywords":
            self.keywords = a.get("content") or ""
        if tag in ("title", "h1"):
            self._in = tag
        if tag in ("p", "br", "li", "h1", "h2", "h3", "h4", "div", "section", "article", "tr"):
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag == self._in:
            self._in = ""

    def handle_data(self, data):
        if self._in == "title" and not self.title:
            self.title = data.strip()
            return
        if self._in == "h1" and not self.h1:
            self.h1 = data.strip()
        if not self._skip:
            self.text.append(data)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
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
                data[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
            else:
                data[key] = value.strip("\"'")
        elif key and re.match(r"^\s+-\s+", line):
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(re.sub(r"^\s+-\s+", "", line).strip().strip("\"'"))
    return {}, text


def as_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def path_url(rel: str) -> str:
    stem, _ = os.path.splitext(rel.replace(os.sep, "/"))
    parts = stem.split("/")
    parts[-1] = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", parts[-1])  # Jekyll-style dated file names
    if parts[-1] in ("index", "_index", "README"):
        parts = parts[:-1]
    return "/" + "/".join(parts).strip("/") + ("/" if parts else "")


def host_of(netloc: str) -> str:
    host = netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def norm_url(url: str, site_hosts: set[str]) -> str | None:
    """Normalise a link to a site path, or None if it is external/not a page."""
    url = url.strip()
    if not url or url.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        if host_of(parsed.netloc) not in site_hosts:
            return None
    elif parsed.scheme:
        return None
    path = parsed.path
    if not path:
        return None
    path = re.sub(r"(index)?\.(md|markdown|mdx|html?)$", "", path)
    return "/" + path.strip("/") + "/" if path.strip("/") else "/"


def load_doc(path: str, root: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    rel = os.path.relpath(path, root) if root else os.path.basename(path)
    if path.lower().endswith((".html", ".htm")):
        parser = _HTMLText()
        parser.feed(raw)
        title = parser.h1 or parser.title
        url = parser.canonical or path_url(rel)
        keywords = as_list(parser.keywords)
        body = "".join(parser.text)
        links = parser.links
    else:
        fm, body_md = parse_frontmatter(raw)
        body_md = re.sub(r"(?ms)^(```|~~~).*?^\1\s*$", "", body_md)
        h1 = re.search(r"(?m)^#\s+(.+)$", body_md)
        title = fm.get("title") or (h1.group(1).strip() if h1 else os.path.splitext(os.path.basename(path))[0])
        url = fm.get("url") or fm.get("permalink") or ""
        if not url and fm.get("slug"):
            base = os.path.dirname(path_url(rel).rstrip("/"))
            url = base.rstrip("/") + "/" + fm["slug"].strip("/") + "/"
        url = url or path_url(rel)
        keywords = as_list(fm.get("keywords")) + as_list(fm.get("keyword")) + as_list(fm.get("tags"))
        links = re.findall(r"(?<!!)\[[^\]]*\]\(\s*<?([^)\s>]+)>?[^)]*\)", body_md)
        links += re.findall(r'href="([^"]+)"', body_md)
        body = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body_md)
        body = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
        body = re.sub(r"<[^>]+>|`|[*_#>]", " ", body)
    return {
        "file": rel,
        "abs": os.path.abspath(path),
        "title": title.strip(),
        "url": url,
        "keywords": keywords,
        "body": re.sub(r"[ \t]+", " ", body).strip(),
        "raw_links": links,
    }


def collect(paths: list[str]) -> list[tuple[str, str]]:
    out = []
    for p in paths:
        if os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith((".", "_", "node_modules")))
                for f in sorted(filenames):
                    if f.lower().endswith(EXTS):
                        out.append((os.path.join(dirpath, f), p))
        elif os.path.isfile(p):
            out.append((p, os.path.dirname(p)))
        else:
            raise FileNotFoundError(p)
    return out


# --------------------------------------------------------------------------- scoring


def light_stem(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def terms(text: str) -> list[str]:
    words = [light_stem(w) for w in WORD_RE.findall(text.lower())]
    out = [w for w in words if w not in STOPWORDS and len(w) > 2 and not w.isdigit()]
    for a, b in zip(words, words[1:]):
        if a not in STOPWORDS and b not in STOPWORDS and len(a) > 2 and len(b) > 2:
            out.append(f"{a} {b}")
    return out


def vectorize(docs: list[dict]) -> list[dict]:
    counts = []
    for d in docs:
        weighted = terms(d["body"]) + 3 * terms(d["title"]) + 3 * terms(" ".join(d["keywords"]))
        counts.append(Counter(weighted))
    df = Counter()
    for c in counts:
        df.update(set(c))
    n = len(docs)
    vectors = []
    for c in counts:
        vec = {t: (1 + math.log(tf)) * math.log((1 + n) / (1 + df[t]) + 1) for t, tf in c.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({t: v / norm for t, v in vec.items()})
    return vectors


def cosine(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(t, 0.0) for t, v in a.items())


def anchor_candidates(doc: dict) -> list[str]:
    cands = [k for k in doc["keywords"] if len(k) > 3]
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", re.sub(r"\(.*?\)|\[.*?\]", " ", doc["title"]))
    for size in (4, 3, 2):
        for i in range(len(words) - size + 1):
            gram = words[i : i + size]
            if gram[0].lower() in STOPWORDS or gram[-1].lower() in STOPWORDS:
                continue
            if any(w.isdigit() for w in gram):
                continue
            cands.append(" ".join(gram))
    seen, out = set(), []
    for c in sorted(cands, key=lambda c: -len(c.split())):
        if c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def find_anchor(source_body: str, target: dict) -> tuple[str | None, str | None]:
    for cand in anchor_candidates(target):
        pattern = r"\b" + r"[\s-]+".join(re.escape(w) for w in cand.split()) + r"s?\b"
        m = re.search(pattern, source_body, re.I)
        if m:
            start = max(source_body.rfind(".", 0, m.start()), source_body.rfind("\n", 0, m.start())) + 1
            end_dot = source_body.find(".", m.end())
            end_nl = source_body.find("\n", m.end())
            ends = [e for e in (end_dot, end_nl) if e != -1]
            end = min(ends) + 1 if ends else len(source_body)
            sentence = re.sub(r"\s+", " ", source_body[start:end]).strip()
            return m.group(0), sentence[:240]
    return None, None


def analyze(docs: list[dict], site_hosts: set[str], max_per_page: int = 3, min_score: float = 0.1) -> dict:
    by_url = {}
    for i, d in enumerate(docs):
        u = norm_url(d["url"], site_hosts) or d["url"]
        d["path"] = u
        by_url[u] = i
    file_lookup = {os.path.normcase(d["abs"]): i for i, d in enumerate(docs)}
    outgoing: list[set[int]] = []
    for d in docs:
        targets = set()
        for link in d["raw_links"]:
            idx = None
            if not re.match(r"^[a-z]+:", link) and re.search(r"\.(md|markdown|mdx|html?)(#.*)?$", link):
                candidate = os.path.normcase(
                    os.path.abspath(os.path.join(os.path.dirname(d["abs"]), link.split("#")[0]))
                )
                idx = file_lookup.get(candidate)
            if idx is None:
                u = norm_url(link, site_hosts)
                if u is not None and not urlparse(link).scheme and not link.startswith("/"):
                    base = d["path"] if d["path"].endswith("/") else d["path"] + "/"
                    u = norm_url(os.path.normpath(os.path.join(base, link)).replace(os.sep, "/"), site_hosts)
                idx = by_url.get(u) if u else None
            if idx is not None and docs[idx] is not d:
                targets.add(idx)
        outgoing.append(targets)
    inbound = Counter(t for tg in outgoing for t in tg)
    vectors = vectorize(docs)
    suggestions = []
    for i, src in enumerate(docs):
        scored = []
        for j, dst in enumerate(docs):
            if i == j or j in outgoing[i]:
                continue
            score = cosine(vectors[i], vectors[j])
            anchor, context = find_anchor(src["body"], dst)
            if anchor:
                score += 0.1
            if score >= min_score:
                scored.append((score, j, anchor, context))
        scored.sort(key=lambda s: (-(s[2] is not None), -s[0]))
        for score, j, anchor, context in scored[:max_per_page]:
            dst = docs[j]
            suggestions.append(
                {
                    "source": src["file"],
                    "source_title": src["title"],
                    "target": dst["file"],
                    "target_title": dst["title"],
                    "target_url": dst["path"],
                    "score": round(score, 3),
                    "anchor": anchor,
                    "context": context,
                    "anchor_hint": None if anchor else (anchor_candidates(dst) or [dst["title"]])[0],
                }
            )
    orphans = [{"file": d["file"], "title": d["title"], "url": d["path"]} for i, d in enumerate(docs) if not inbound[i]]
    return {
        "posts": len(docs),
        "existing_internal_links": sum(len(t) for t in outgoing),
        "suggestions": suggestions,
        "orphans": orphans,
        "inbound": {d["file"]: inbound[i] for i, d in enumerate(docs)},
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Suggest internal links between Markdown/HTML posts by keyword overlap; list orphan pages.",
        epilog="Example: suggest_links.py content/posts --site example.com --max-per-page 3 --csv links.csv",
    )
    p.add_argument("paths", nargs="+", help="post files or folders")
    p.add_argument("--site", action="append", default=[], help="your domain(s); absolute links to it are internal")
    p.add_argument("--max-per-page", type=int, default=3, help="suggestions per source post (default 3)")
    p.add_argument("--min-score", type=float, default=0.1, help="minimum similarity 0-1 (default 0.1)")
    p.add_argument("--only", help="only suggest links FROM this file (substring match)")
    p.add_argument("--csv", dest="csv_out", help="write suggestions to this CSV file")
    p.add_argument("--force", action="store_true", help="overwrite --csv file")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.add_argument("--fail-on-orphans", action="store_true", help="exit 1 when orphan posts exist")
    args = p.parse_args(argv)
    try:
        files = collect(args.paths)
        if len(files) < 2:
            raise ValueError("need at least two posts")
        docs = [load_doc(f, root) for f, root in files]
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    hosts = {host_of(re.sub(r"^https?://", "", s, flags=re.I).split("/")[0]) for s in args.site}
    result = analyze(docs, hosts, args.max_per_page, args.min_score)
    if args.only:
        result["suggestions"] = [s for s in result["suggestions"] if args.only in s["source"]]
    if args.csv_out:
        if os.path.exists(args.csv_out) and not args.force:
            print(f"error: {args.csv_out} exists; pass --force", file=sys.stderr)
            return 2
        buf = io.StringIO()
        fields = ["source", "target", "target_url", "anchor", "anchor_hint", "score", "context"]
        w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(result["suggestions"])
        with open(args.csv_out, "w", encoding="utf-8", newline="") as fh:
            fh.write(buf.getvalue())
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(
            f"{result['posts']} posts, {result['existing_internal_links']} existing internal links, "
            f"{len(result['suggestions'])} suggestions, {len(result['orphans'])} orphans"
        )
        current = None
        for s in result["suggestions"]:
            if s["source"] != current:
                current = s["source"]
                print(f"\n{current}  ({s['source_title']})")
            if s["anchor"]:
                print(f'  -> {s["target_url"]}  anchor "{s["anchor"]}"  score {s["score"]}')
                print(f"     in: {s['context']}")
            else:
                print(
                    f'  -> {s["target_url"]}  no matching phrase; write one around "{s["anchor_hint"]}"  '
                    f"score {s['score']}"
                )
        if result["orphans"]:
            print("\nOrphans (no internal links point here):")
            for o in result["orphans"]:
                print(f"  {o['url']}  {o['title']}  ({o['file']})")
    return 1 if args.fail_on_orphans and result["orphans"] else 0


if __name__ == "__main__":
    sys.exit(main())
