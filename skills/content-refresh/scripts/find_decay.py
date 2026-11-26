#!/usr/bin/env python3
"""Find decaying pages (or queries) in a Google Search Console export and say why.

Accepted inputs (CSV, comma/tab/semicolon, UTF-8 with or without BOM):
  1. A Search Console "Compare" export (Performance > Date: Compare > Export > Pages.csv):
     one row per page with current and previous Clicks / Impressions / CTR / Position.
     The previous period is the column whose header contains "previous", "prior" or
     "before"; override with --current-label / --previous-label.
  2. Two single-period exports: CURRENT.csv --previous PREVIOUS.csv.
  3. Daily rows (page, date, clicks, impressions[, position]) from the Search Console API,
     BigQuery bulk export or Looker Studio; split at --split-date (default: midpoint).

A page decays when previous clicks >= --min-clicks, clicks fell by >= --min-drop percent
and by >= --min-loss clicks. Each one gets a diagnosis (rankings slipped, demand fell,
CTR fell, collapsed) and a refresh action. --opportunities also lists "striking
distance" pages (average position 4-20 with many impressions).

Read-only, offline. Writes only --csv-out when given.

Exit codes: 0 = no decaying pages, 1 = decaying pages found (unless --exit-zero), 2 = error.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import sys

PAGE_KEYS = ["top pages", "page", "pages", "url", "landing page", "address", "top queries", "query", "queries"]
PREV_WORDS = ("previous", "prior", "before", "prev")


class InputError(Exception):
    pass


def read_csv(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"{path}: {exc}") from exc
    if not text.strip():
        raise InputError(f"{path}: empty file")
    first = text.splitlines()[0]
    delim = max([",", "\t", ";"], key=first.count)
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delim))
    if not rows:
        raise InputError(f"{path}: no data rows")
    return rows


def num(value) -> float:
    """Parse '1,234', '3.5%', '12.3', '' and '<10' to float (CTR stays a percent)."""
    if value is None:
        return 0.0
    s = str(value).strip().replace(" ", "").replace(" ", "")
    if not s or s in ("-", "--"):
        return 0.0
    s = s.lstrip("<>~")
    if s.endswith("%"):
        s = s[:-1]
    if s.count(",") and s.count("."):
        s = s.replace(",", "")
    elif s.count(",") == 1 and len(s.split(",")[1]) != 3:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def find_col(headers: list[str], *needles: str, exclude: tuple[str, ...] = ()) -> list[str]:
    out = []
    for h in headers:
        low = h.strip().lower()
        if any(n in low for n in needles) and not any(e in low for e in exclude):
            out.append(h)
    return out


def page_col(headers: list[str]) -> str:
    lowered = {h.strip().lower(): h for h in headers}
    for key in PAGE_KEYS:
        if key in lowered:
            return lowered[key]
    for h in headers:
        if any(k in h.lower() for k in ("page", "url", "quer")):
            return h
    return headers[0]


def metric_pair(headers: list[str], metric: str, cur_label: str | None, prev_label: str | None):
    cols = find_col(headers, metric)
    if metric == "ctr":
        cols = [c for c in cols if "ctr" in c.lower()]
    if len(cols) < 2:
        return None, None
    if prev_label:
        prev = [c for c in cols if prev_label.lower() in c.lower()]
    else:
        prev = [c for c in cols if any(w in c.lower() for w in PREV_WORDS)]
    if cur_label:
        cur = [c for c in cols if cur_label.lower() in c.lower() and c not in prev]
    else:
        cur = [c for c in cols if c not in prev]
    if not prev:
        # No label says which is older: Search Console lists the newer period first.
        cur, prev = [cols[0]], [cols[1]]
    if not cur:
        return None, None
    return cur[0], prev[0]


def from_compare(rows: list[dict], cur_label=None, prev_label=None) -> dict:
    headers = list(rows[0].keys())
    pc = page_col(headers)
    pairs = {m: metric_pair(headers, m, cur_label, prev_label) for m in ("clicks", "impressions", "ctr", "position")}
    if not pairs["clicks"][0]:
        raise InputError("no current/previous Clicks columns found; is this a Compare export?")
    data = {}
    for r in rows:
        page = (r.get(pc) or "").strip()
        if not page:
            continue
        rec = {}
        for m, (c, p) in pairs.items():
            rec[m] = (num(r.get(c)) if c else 0.0, num(r.get(p)) if p else 0.0)
        data[page] = rec
    return data


def single_period(rows: list[dict]) -> dict:
    headers = list(rows[0].keys())
    pc = page_col(headers)
    cols = {m: (find_col(headers, m) or [None])[0] for m in ("clicks", "impressions", "ctr", "position")}
    if not cols["clicks"]:
        raise InputError("no Clicks column found")
    out = {}
    for r in rows:
        page = (r.get(pc) or "").strip()
        if page:
            out[page] = {m: num(r.get(c)) if c else 0.0 for m, c in cols.items()}
    return out


def from_two(cur_rows: list[dict], prev_rows: list[dict]) -> dict:
    cur, prev = single_period(cur_rows), single_period(prev_rows)
    zero = {"clicks": 0.0, "impressions": 0.0, "ctr": 0.0, "position": 0.0}
    return {
        page: {m: (cur.get(page, zero)[m], prev.get(page, zero)[m]) for m in zero}
        for page in sorted(set(cur) | set(prev))
    }


def from_daily(rows: list[dict], split: dt.date | None) -> tuple[dict, dict]:
    headers = list(rows[0].keys())
    dc = (find_col(headers, "date", "day") or [None])[0]
    if not dc:
        raise InputError("no date column")
    pc = page_col([h for h in headers if h != dc])
    cc = (find_col(headers, "clicks") or [None])[0]
    ic = (find_col(headers, "impressions") or [None])[0]
    poc = (find_col(headers, "position") or [None])[0]
    if not cc:
        raise InputError("no clicks column")
    parsed = []
    for r in rows:
        try:
            day = dt.date.fromisoformat((r.get(dc) or "").strip()[:10])
        except ValueError:
            continue
        parsed.append((day, (r.get(pc) or "").strip(), num(r.get(cc)), num(r.get(ic)), num(r.get(poc))))
    if not parsed:
        raise InputError("no rows with ISO dates (YYYY-MM-DD)")
    first, last = min(p[0] for p in parsed), max(p[0] for p in parsed)
    if split is None:
        split = first + (last - first) / 2 + dt.timedelta(days=1)
    agg: dict = {}
    for day, page, clicks, impr, pos in parsed:
        if not page:
            continue
        i = 0 if day >= split else 1
        a = agg.setdefault(page, {"clicks": [0.0, 0.0], "impressions": [0.0, 0.0], "posw": [0.0, 0.0]})
        a["clicks"][i] += clicks
        a["impressions"][i] += impr
        a["posw"][i] += pos * (impr or 1)
    data = {}
    for page, a in agg.items():
        rec = {"clicks": tuple(a["clicks"]), "impressions": tuple(a["impressions"])}
        rec["ctr"] = tuple(100 * c / i if i else 0.0 for c, i in zip(a["clicks"], a["impressions"]))
        rec["position"] = tuple(w / (i or 1) for w, i in zip(a["posw"], a["impressions"]))
        data[page] = rec
    periods = {
        "previous": f"{first.isoformat()}..{(split - dt.timedelta(days=1)).isoformat()}",
        "current": f"{split.isoformat()}..{last.isoformat()}",
    }
    return data, periods


def pct_change(cur: float, prev: float) -> float | None:
    if prev == 0:
        return None
    return round(100 * (cur - prev) / prev, 1)


def diagnose(rec: dict, min_drop: float) -> tuple[str, str]:
    c_cur, c_prev = rec["clicks"]
    i_cur, i_prev = rec["impressions"]
    p_cur, p_prev = rec["position"]
    ctr_cur = 100 * c_cur / i_cur if i_cur else 0.0
    ctr_prev = 100 * c_prev / i_prev if i_prev else 0.0
    impr_drop = (i_prev - i_cur) / i_prev * 100 if i_prev else 0.0
    pos_delta = (p_cur - p_prev) if p_cur and p_prev else 0.0
    if c_prev and c_cur <= c_prev * 0.1:
        return (
            "collapsed",
            "Clicks fell 90%+. Check URL Inspection (indexed? canonical?), redirects, noindex, and whether "
            "another of your URLs now ranks for its queries (cannibalisation).",
        )
    if pos_delta >= 1.0:
        return (
            "rankings_slipped",
            f"Average position worsened by {pos_delta:.1f}. Refresh: compare with the current top 3, update "
            "facts and examples, cover missing subtopics, add internal links from strong pages.",
        )
    if impr_drop >= min_drop and abs(pos_delta) < 1.0:
        return (
            "demand_fell",
            "Impressions fell while position held: fewer searches (seasonality, trend) or lost queries. "
            "Check the Queries tab and Google Trends before rewriting; update the year and angle if dated.",
        )
    if ctr_prev and ctr_cur < ctr_prev * 0.8:
        return (
            "ctr_fell",
            f"CTR fell from {ctr_prev:.1f}% to {ctr_cur:.1f}% at similar visibility: SERP features or AI "
            "answers above you, or a weaker snippet. Rewrite the title and meta description; add structured data.",
        )
    return "mixed", "Several small losses. Review the page's top queries and refresh the sections they map to."


def analyze(
    data: dict, min_clicks: float = 10, min_drop: float = 20, min_loss: float = 5, min_impressions: float = 100
) -> dict:
    decaying, opportunities = [], []
    for page, rec in data.items():
        c_cur, c_prev = rec["clicks"]
        i_cur, i_prev = rec["impressions"]
        p_cur, p_prev = rec["position"]
        change = pct_change(c_cur, c_prev)
        if c_prev >= min_clicks and change is not None and -change >= min_drop and c_prev - c_cur >= min_loss:
            reason, action = diagnose(rec, min_drop)
            decaying.append(
                {
                    "page": page,
                    "clicks_current": round(c_cur),
                    "clicks_previous": round(c_prev),
                    "clicks_lost": round(c_prev - c_cur),
                    "clicks_change_pct": change,
                    "impressions_current": round(i_cur),
                    "impressions_previous": round(i_prev),
                    "impressions_change_pct": pct_change(i_cur, i_prev),
                    "ctr_current": round(100 * c_cur / i_cur, 2) if i_cur else 0.0,
                    "ctr_previous": round(100 * c_prev / i_prev, 2) if i_prev else 0.0,
                    "position_current": round(p_cur, 1),
                    "position_previous": round(p_prev, 1),
                    "diagnosis": reason,
                    "action": action,
                }
            )
        if 4 <= p_cur <= 20 and i_cur >= min_impressions:
            opportunities.append(
                {
                    "page": page,
                    "position": round(p_cur, 1),
                    "impressions": round(i_cur),
                    "clicks": round(c_cur),
                    "ctr": round(100 * c_cur / i_cur, 2) if i_cur else 0.0,
                }
            )
    decaying.sort(key=lambda d: (-d["clicks_lost"], d["page"]))
    opportunities.sort(key=lambda o: (-o["impressions"], o["position"]))
    total_cur = sum(r["clicks"][0] for r in data.values())
    total_prev = sum(r["clicks"][1] for r in data.values())
    return {
        "pages": len(data),
        "clicks_current": round(total_cur),
        "clicks_previous": round(total_prev),
        "clicks_change_pct": pct_change(total_cur, total_prev),
        "decaying": decaying,
        "opportunities": opportunities,
    }


def write_csv(path: str, items: list[dict], force: bool) -> None:
    if os.path.exists(path) and not force:
        raise InputError(f"{path} exists; pass --force to overwrite")
    fields = list(items[0].keys()) if items else ["page"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(items)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Find decaying pages in a Search Console CSV export and suggest a refresh action.",
        epilog="Examples: find_decay.py Pages.csv | find_decay.py last-3m.csv --previous prev-3m.csv | "
        "find_decay.py daily.csv --split-date 2026-09-01 --json",
    )
    p.add_argument("csv", help="Search Console export (compare, single period with --previous, or daily rows)")
    p.add_argument("--previous", help="single-period export for the previous period")
    p.add_argument("--split-date", help="for daily rows: first day of the current period (YYYY-MM-DD)")
    p.add_argument("--current-label", help="substring identifying current-period columns in a compare export")
    p.add_argument("--previous-label", help="substring identifying previous-period columns")
    p.add_argument("--min-clicks", type=float, default=10, help="ignore pages with fewer previous clicks (10)")
    p.add_argument("--min-drop", type=float, default=20, help="minimum clicks drop in percent (20)")
    p.add_argument("--min-loss", type=float, default=5, help="minimum clicks lost (5)")
    p.add_argument("--min-impressions", type=float, default=100, help="for --opportunities (100)")
    p.add_argument("--opportunities", action="store_true", help="also list striking-distance pages (pos 4-20)")
    p.add_argument("--limit", type=int, default=25, help="rows to print in text mode (25)")
    p.add_argument("--csv-out", help="write decaying pages to this CSV")
    p.add_argument("--force", action="store_true", help="overwrite --csv-out")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.add_argument("--exit-zero", action="store_true", help="exit 0 even when decaying pages are found")
    args = p.parse_args(argv)
    try:
        rows = read_csv(args.csv)
        headers = [h.lower() for h in rows[0]]
        periods = {}
        if args.previous:
            data = from_two(rows, read_csv(args.previous))
        elif any(h.strip() == "date" or h.strip() in ("day", "data_date") for h in headers):
            split = dt.date.fromisoformat(args.split_date) if args.split_date else None
            data, periods = from_daily(rows, split)
        else:
            data = from_compare(rows, args.current_label, args.previous_label)
        result = analyze(data, args.min_clicks, args.min_drop, args.min_loss, args.min_impressions)
        result["periods"] = periods
        if not args.opportunities:
            result.pop("opportunities")
        if args.csv_out:
            write_csv(args.csv_out, result["decaying"], args.force)
    except (InputError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        ch = result["clicks_change_pct"]
        print(
            f"{result['pages']} rows; clicks {result['clicks_previous']} -> {result['clicks_current']}"
            f" ({'n/a' if ch is None else f'{ch:+.1f}%'}); {len(result['decaying'])} decaying"
        )
        if periods:
            print(f"periods: previous {periods['previous']}, current {periods['current']}")
        for d in result["decaying"][: args.limit]:
            print(
                f"\n-{d['clicks_lost']:>5} clicks ({d['clicks_change_pct']:+.0f}%)  {d['page']}\n"
                f"       impr {d['impressions_previous']} -> {d['impressions_current']}, "
                f"pos {d['position_previous']} -> {d['position_current']}, "
                f"CTR {d['ctr_previous']}% -> {d['ctr_current']}%  [{d['diagnosis']}]\n"
                f"       {d['action']}"
            )
        if args.opportunities:
            print("\nStriking distance (position 4-20):")
            for o in result["opportunities"][: args.limit]:
                print(f"  pos {o['position']:>4}  impr {o['impressions']:>6}  CTR {o['ctr']}%  {o['page']}")
        if args.csv_out:
            print(f"\nwrote {len(result['decaying'])} rows to {args.csv_out}")
    return 1 if result["decaying"] and not args.exit_zero else 0


if __name__ == "__main__":
    sys.exit(main())
