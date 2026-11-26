import csv
import json

import pytest

from conftest import fixture, load_script, run_script

SKILL = "content-refresh"
SCRIPT = "find_decay.py"
m = load_script(SKILL, SCRIPT)


def compare():
    return m.from_compare(m.read_csv(str(fixture(SKILL, "gsc-compare.csv"))))


def test_compare_export_parsed():
    data = compare()
    rec = data["https://example.com/blog/content-calendar/"]
    assert rec["clicks"] == (1020.0, 1850.0) and rec["impressions"] == (40100.0, 41000.0)
    assert rec["ctr"] == (2.54, 4.51) and rec["position"] == (6.1, 5.8)


def test_diagnoses():
    r = m.analyze(compare())
    by = {d["page"].rsplit("/", 2)[-2]: d for d in r["decaying"]}
    assert set(by) == {"content-calendar", "seo-copywriting", "black-friday-email-ideas", "old-tool-review"}
    assert by["content-calendar"]["diagnosis"] == "ctr_fell"
    assert by["seo-copywriting"]["diagnosis"] == "rankings_slipped"
    assert by["black-friday-email-ideas"]["diagnosis"] == "demand_fell"
    assert by["old-tool-review"]["diagnosis"] == "collapsed"
    assert [d["clicks_lost"] for d in r["decaying"]] == sorted((d["clicks_lost"] for d in r["decaying"]), reverse=True)
    assert r["clicks_previous"] == 4277


def test_thresholds_exclude_small_pages():
    assert not any("tiny-page" in d["page"] for d in m.analyze(compare())["decaying"])  # 9 previous clicks < 10
    r = m.analyze(compare(), min_clicks=5)
    assert any("tiny-page" in d["page"] for d in r["decaying"])  # 9 -> 4: -55%, 5 clicks lost
    r = m.analyze(compare(), min_clicks=5, min_loss=6)
    assert not any("tiny-page" in d["page"] for d in r["decaying"])
    r = m.analyze(compare(), min_drop=60)
    assert {d["diagnosis"] for d in r["decaying"]} == {"demand_fell", "collapsed"}


def test_opportunities():
    r = m.analyze(compare(), min_impressions=5000)
    pages = [o["page"] for o in r["opportunities"]]
    assert "https://example.com/blog/striking-distance/" in pages
    assert all(4 <= o["position"] <= 20 for o in r["opportunities"])


def test_two_files():
    data = m.from_two(m.read_csv(str(fixture(SKILL, "current.csv"))), m.read_csv(str(fixture(SKILL, "previous.csv"))))
    assert data["https://example.com/blog/gone/"]["clicks"] == (0.0, 60.0)
    assert data["https://example.com/blog/new/"]["clicks"] == (30.0, 0.0)
    r = m.analyze(data)
    assert [d["page"].split("/")[-2] for d in r["decaying"]] == ["a", "gone"]


def test_daily_rows_split_at_midpoint_and_date():
    data, periods = m.from_daily(m.read_csv(str(fixture(SKILL, "daily.csv"))), None)
    assert periods["current"].startswith("2026-10-01")
    rec = data["https://example.com/blog/decaying/"]
    assert rec["clicks"] == (240.0, 600.0) and round(rec["position"][0], 1) == 7.5
    import datetime as dt

    data2, _ = m.from_daily(m.read_csv(str(fixture(SKILL, "daily.csv"))), dt.date(2026, 10, 21))
    assert data2["https://example.com/blog/steady/"]["clicks"] == (100.0, 500.0)


@pytest.mark.parametrize(
    "raw,expected",
    [("1,234", 1234.0), ("3.5%", 3.5), ("12,5", 12.5), ("1,234.5", 1234.5), ("", 0.0), ("<10", 10.0), ("n/a", 0.0)],
)
def test_num(raw, expected):
    assert m.num(raw) == expected


def test_labels_override_and_order_fallback(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text("Page,Oct Clicks,Sep Clicks\n/a,10,50\n")
    data = m.from_compare(m.read_csv(str(f)))
    assert data["/a"]["clicks"] == (10.0, 50.0)
    data = m.from_compare(m.read_csv(str(f)), cur_label="Sep", prev_label="Oct")
    assert data["/a"]["clicks"] == (50.0, 10.0)


def test_tab_separated_with_bom(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("﻿Top pages\tLast 28 days Clicks\tPrevious 28 days Clicks\n/x\t5\t40\n", encoding="utf-8")
    assert m.from_compare(m.read_csv(str(f)))["/x"]["clicks"] == (5.0, 40.0)


def test_cli(tmp_path):
    src = str(fixture(SKILL, "gsc-compare.csv"))
    r = run_script(SKILL, SCRIPT, src)
    assert r.returncode == 1 and "4 decaying" in r.stdout
    assert run_script(SKILL, SCRIPT, src, "--exit-zero").returncode == 0
    js = run_script(SKILL, SCRIPT, src, "--json", "--opportunities")
    data = json.loads(js.stdout)
    assert len(data["decaying"]) == 4 and data["opportunities"]
    out = tmp_path / "decay.csv"
    run_script(SKILL, SCRIPT, src, "--csv-out", str(out))
    rows = list(csv.DictReader(out.open()))
    assert rows[0]["page"].endswith("/content-calendar/") and "diagnosis" in rows[0]
    assert run_script(SKILL, SCRIPT, src, "--csv-out", str(out)).returncode == 2
    two = run_script(
        SKILL, SCRIPT, str(fixture(SKILL, "current.csv")), "--previous", str(fixture(SKILL, "previous.csv"))
    )
    assert two.returncode == 1 and "2 decaying" in two.stdout
    daily = run_script(SKILL, SCRIPT, str(fixture(SKILL, "daily.csv")), "--split-date", "2026-10-01")
    assert daily.returncode == 1 and "periods:" in daily.stdout
    single = run_script(SKILL, SCRIPT, str(fixture(SKILL, "current.csv")))
    assert single.returncode == 2 and "Compare" in single.stderr
    empty = tmp_path / "e.csv"
    empty.write_text("")
    assert run_script(SKILL, SCRIPT, str(empty)).returncode == 2
