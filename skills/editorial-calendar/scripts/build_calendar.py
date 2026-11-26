#!/usr/bin/env python3
"""Build an editorial calendar CSV from topic clusters and a publishing cadence.

Input: a CSV (columns: cluster, title, keyword, type, funnel, format, priority, owner;
only cluster and title are required) or JSON ({"clusters": [{"name", "pillar", "topics"}]}).

Scheduling: each cluster's pillar page goes first, then its spokes by priority; clusters
are interleaved so the same topic does not run back to back. Dates follow --per-week /
--days / --interval-weeks from --start, skipping --skip dates (holidays, launches).
Each row gets a brief due date (--lead-days before publishing), the pillar it should
link to, and optional repurposing dates (LinkedIn, newsletter).

Warnings: duplicate keywords (cannibalisation), topics without keywords, clusters
without a pillar, a funnel mix that is all one stage, topics that did not fit.

Read-only on inputs; writes only the --out file (refuses to overwrite without --force).

Exit codes: 0 = calendar built, 1 = warnings with --strict, 2 = error.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
from collections import Counter

WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
DEFAULT_DAYS = {1: ["tue"], 2: ["tue", "thu"], 3: ["mon", "wed", "fri"], 4: ["mon", "tue", "thu", "fri"]}
FIELDS = [
    "date",
    "weekday",
    "week",
    "cluster",
    "type",
    "title",
    "keyword",
    "funnel",
    "format",
    "owner",
    "status",
    "brief_due",
    "links_to",
]
FUNNEL_ALIASES = {
    "tofu": "tofu",
    "top": "tofu",
    "awareness": "tofu",
    "mofu": "mofu",
    "middle": "mofu",
    "consideration": "mofu",
    "bofu": "bofu",
    "bottom": "bofu",
    "decision": "bofu",
    "conversion": "bofu",
}


class InputError(Exception):
    pass


def norm_topic(raw: dict, cluster: str | None = None, default_type: str = "spoke") -> dict:
    get = {str(k).strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items() if k}
    title = get.get("title") or get.get("topic") or ""
    if not title:
        raise InputError(f"topic without a title: {raw}")
    kind = (get.get("type") or default_type or "spoke").lower()
    if kind in ("hub", "pillar", "pillar page", "cornerstone") or str(get.get("pillar", "")).lower() in (
        "yes",
        "true",
        "1",
    ):
        kind = "pillar"
    elif kind not in ("pillar", "spoke"):
        kind = "spoke"
    funnel = FUNNEL_ALIASES.get(str(get.get("funnel") or get.get("stage") or "").lower(), "")
    try:
        priority = int(get.get("priority") or 100)
    except ValueError:
        priority = 100
    return {
        "cluster": (cluster or get.get("cluster") or "General").strip(),
        "title": title,
        "keyword": get.get("keyword") or get.get("focus_keyword") or "",
        "type": kind,
        "funnel": funnel,
        "format": get.get("format") or "article",
        "owner": get.get("owner") or "",
        "priority": priority,
    }


def load_topics(text: str, fmt: str) -> list[dict]:
    topics: list[dict] = []
    if fmt == "json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InputError(f"invalid JSON: {exc}") from exc
        clusters = data.get("clusters") if isinstance(data, dict) else data
        if not isinstance(clusters, list):
            raise InputError("JSON must be {'clusters': [...]} or a list of clusters/topics")
        for c in clusters:
            if not isinstance(c, dict):
                raise InputError(f"cluster must be an object: {c!r}")
            if "topics" not in c and "pillar" not in c:
                topics.append(norm_topic(c))
                continue
            name = c.get("name") or c.get("cluster") or "General"
            pillar = c.get("pillar")
            if isinstance(pillar, str):
                pillar = {"title": pillar}
            if pillar:
                topics.append(norm_topic({**pillar, "type": "pillar"}, name))
            for t in c.get("topics") or []:
                topics.append(norm_topic({"title": t} if isinstance(t, str) else t, name))
    else:
        reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
        if not reader.fieldnames or not {f.strip().lower() for f in reader.fieldnames} & {"title", "topic"}:
            raise InputError("CSV needs a 'title' (or 'topic') column")
        for row in reader:
            if any((v or "").strip() for v in row.values()):
                topics.append(norm_topic(row))
    if not topics:
        raise InputError("no topics found")
    return topics


def order_topics(topics: list[dict]) -> list[dict]:
    """Pillar first per cluster, then by priority; interleave clusters round-robin."""
    clusters: dict[str, list[dict]] = {}
    for i, t in enumerate(topics):
        t["_i"] = i
        clusters.setdefault(t["cluster"], []).append(t)
    queues = [
        sorted(items, key=lambda t: (t["type"] != "pillar", t["priority"], t["_i"])) for items in clusters.values()
    ]
    ordered: list[dict] = []
    while any(queues):
        for q in queues:
            if q:
                ordered.append(q.pop(0))
    return ordered


def publish_dates(start: dt.date, days: list[int], interval_weeks: int, skip: set[dt.date]):
    """Yield publishing dates forever, starting with the week that contains start."""
    week_start = start - dt.timedelta(days=start.weekday())
    week = 0
    while True:
        if week % interval_weeks == 0:
            for d in sorted(days):
                day = week_start + dt.timedelta(days=d)
                if day >= start and day not in skip:
                    yield day
        week += 1
        week_start += dt.timedelta(days=7)
        if week > 520:
            return


def build(
    topics: list[dict],
    start: dt.date,
    days: list[int],
    interval_weeks: int = 1,
    weeks: int | None = None,
    skip: set[dt.date] | None = None,
    lead_days: int = 7,
    owners: list[str] | None = None,
    repurpose: bool = False,
    newsletter_day: int = 4,
) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    ordered = order_topics(topics)
    pillars = {t["cluster"]: t["title"] for t in ordered if t["type"] == "pillar"}
    end = start + dt.timedelta(weeks=weeks) if weeks else None
    gen = publish_dates(start, days, interval_weeks, skip or set())
    rows: list[dict] = []
    owner_i = 0
    first_monday = start - dt.timedelta(days=start.weekday())
    for t in ordered:
        day = next(gen, None)
        if day is None or (end and day >= end):
            break
        owner = t["owner"]
        if not owner and owners:
            owner = owners[owner_i % len(owners)]
            owner_i += 1
        row = {
            "date": day.isoformat(),
            "weekday": day.strftime("%a"),
            "week": (day - first_monday).days // 7 + 1,
            "cluster": t["cluster"],
            "type": t["type"],
            "title": t["title"],
            "keyword": t["keyword"],
            "funnel": t["funnel"],
            "format": t["format"],
            "owner": owner,
            "status": "planned",
            "brief_due": (day - dt.timedelta(days=lead_days)).isoformat(),
            "links_to": pillars.get(t["cluster"], "") if t["type"] == "spoke" else "",
        }
        if repurpose:
            row["linkedin_date"] = next_workday(day + dt.timedelta(days=1)).isoformat()
            delta = (newsletter_day - day.weekday()) % 7 or 7
            row["newsletter_date"] = (day + dt.timedelta(days=delta)).isoformat()
        rows.append(row)

    unscheduled = len(ordered) - len(rows)
    if unscheduled:
        warnings.append(f"{unscheduled} topic(s) did not fit in {weeks} week(s); extend --weeks or raise cadence")
    kw = Counter(t["keyword"].lower() for t in topics if t["keyword"])
    for k, n in sorted(kw.items()):
        if n > 1:
            titles = [t["title"] for t in topics if t["keyword"].lower() == k]
            warnings.append(f"keyword '{k}' targeted by {n} topics (cannibalisation risk): " + " | ".join(titles))
    missing_kw = [t["title"] for t in topics if not t["keyword"]]
    if missing_kw:
        warnings.append(f"{len(missing_kw)} topic(s) have no keyword: " + " | ".join(missing_kw[:5]))
    for cluster in sorted({t["cluster"] for t in topics}):
        n_pillars = sum(1 for t in topics if t["cluster"] == cluster and t["type"] == "pillar")
        if n_pillars == 0:
            warnings.append(f"cluster '{cluster}' has no pillar page; spokes have nothing to link up to")
        elif n_pillars > 1:
            warnings.append(f"cluster '{cluster}' has {n_pillars} pillar pages; keep one")
    stages = Counter(t["funnel"] for t in topics if t["funnel"])
    if sum(stages.values()) >= 5:
        top, count = stages.most_common(1)[0]
        if count / sum(stages.values()) > 0.8:
            warnings.append(f"{count} of {sum(stages.values())} topics are {top}; add some other funnel stages")
    return rows, warnings


def next_workday(day: dt.date) -> dt.date:
    while day.weekday() >= 5:
        day += dt.timedelta(days=1)
    return day


def parse_days(value: str) -> list[int]:
    out = []
    for part in re.split(r"[,\s]+", value.strip().lower()):
        if not part:
            continue
        if part[:3] not in WEEKDAYS:
            raise InputError(f"unknown weekday '{part}' (use mon,tue,...)")
        out.append(WEEKDAYS[part[:3]])
    if not out:
        raise InputError("no weekdays given")
    return sorted(set(out))


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError as exc:
        raise InputError(f"bad date '{value}' (use YYYY-MM-DD)") from exc


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    fields = FIELDS + [k for k in ("linkedin_date", "newsletter_date") if rows and k in rows[0]]
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Build an editorial calendar CSV from topic clusters and a cadence.",
        epilog="Example: build_calendar.py topics.csv --start 2026-01-05 --per-week 2 --weeks 12 --out calendar.csv",
    )
    p.add_argument("topics", help="topics CSV or JSON file (- for stdin)")
    p.add_argument("--format", choices=["auto", "csv", "json"], default="auto", help="input format (default: by name)")
    p.add_argument("--start", help="first possible publish date YYYY-MM-DD (default: next Monday)")
    p.add_argument("--per-week", type=int, default=2, help="posts per publishing week (default 2)")
    p.add_argument("--days", help="weekdays to publish, e.g. tue,thu (overrides --per-week)")
    p.add_argument("--interval-weeks", type=int, default=1, help="publish every Nth week (2 = fortnightly)")
    p.add_argument("--weeks", type=int, help="limit the calendar to this many weeks")
    p.add_argument("--skip", default="", help="comma-separated dates to skip (holidays), YYYY-MM-DD")
    p.add_argument("--lead-days", type=int, default=7, help="brief due this many days before publishing")
    p.add_argument("--owners", default="", help="comma-separated writers assigned round-robin when owner is empty")
    p.add_argument("--repurpose", action="store_true", help="add linkedin_date and newsletter_date columns")
    p.add_argument("--newsletter-day", default="fri", help="newsletter weekday for --repurpose (default fri)")
    p.add_argument("--out", help="write the CSV here instead of stdout")
    p.add_argument("--force", action="store_true", help="overwrite --out if it exists")
    p.add_argument("--json", action="store_true", help="print JSON (rows + warnings) instead of CSV")
    p.add_argument("--strict", action="store_true", help="exit 1 when there are warnings")
    args = p.parse_args(argv)
    try:
        if args.topics == "-":
            text = sys.stdin.read()
        else:
            with open(args.topics, encoding="utf-8-sig") as fh:
                text = fh.read()
        fmt = args.format
        if fmt == "auto":
            fmt = "json" if args.topics.lower().endswith(".json") or text.lstrip().startswith(("{", "[")) else "csv"
        topics = load_topics(text, fmt)
        if args.per_week < 1 or args.interval_weeks < 1:
            raise InputError("--per-week and --interval-weeks must be >= 1")
        if args.days:
            days = parse_days(args.days)
        elif args.per_week in DEFAULT_DAYS:
            days = [WEEKDAYS[d] for d in DEFAULT_DAYS[args.per_week]]
        else:
            days = list(range(min(args.per_week, 7)))
        if args.start:
            start = parse_date(args.start)
        else:
            today = dt.date.today()
            start = today + dt.timedelta(days=(7 - today.weekday()) % 7 or 7)
        skip = {parse_date(s) for s in args.skip.split(",") if s.strip()}
        owners = [o.strip() for o in args.owners.split(",") if o.strip()]
        newsletter_day = parse_days(args.newsletter_day)[0]
    except (OSError, UnicodeDecodeError, InputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rows, warnings = build(
        topics,
        start,
        days,
        args.interval_weeks,
        args.weeks,
        skip,
        args.lead_days,
        owners,
        args.repurpose,
        newsletter_day,
    )
    if args.json:
        output = json.dumps({"rows": rows, "warnings": warnings}, indent=2)
    else:
        output = to_csv(rows)
    if args.out:
        if os.path.exists(args.out) and not args.force:
            print(f"error: {args.out} exists; pass --force to overwrite", file=sys.stderr)
            return 2
        with open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(output)
        print(f"wrote {len(rows)} rows to {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(output if output.endswith("\n") else output + "\n")
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    return 1 if args.strict and warnings else 0


if __name__ == "__main__":
    sys.exit(main())
