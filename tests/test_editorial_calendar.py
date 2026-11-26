import csv
import datetime as dt
import io
import json

import pytest

from conftest import fixture, load_script, run_script

SKILL = "editorial-calendar"
SCRIPT = "build_calendar.py"
m = load_script(SKILL, SCRIPT)
MON = dt.date(2026, 1, 5)


def topics_csv():
    return m.load_topics(fixture(SKILL, "topics.csv").read_text(), "csv")


def test_load_csv_and_json():
    t = topics_csv()
    assert len(t) == 10 and sum(1 for x in t if x["type"] == "pillar") == 3
    j = m.load_topics(fixture(SKILL, "topics.json").read_text(), "json")
    assert [x["title"] for x in j][:2] == ["Email Newsletter Guide for Founders", "Subject Lines That Get Opened"]
    assert j[0]["type"] == "pillar" and j[3]["type"] == "pillar" and j[2]["title"] == "Preview Text Explained"


def test_pillars_first_and_clusters_interleaved():
    rows, _ = m.build(topics_csv(), MON, [1, 3])
    assert [r["type"] for r in rows[:3]] == ["pillar"] * 3
    clusters = [r["cluster"] for r in rows]
    assert all(a != b for a, b in zip(clusters, clusters[1:8]))
    spokes = [r for r in rows if r["cluster"] == "Content planning" and r["type"] == "spoke"]
    assert spokes[0]["title"] == "Free Content Calendar Template"  # priority 1
    assert all(r["links_to"] == "Content Calendar: The Complete Guide for Small Teams" for r in spokes)


def test_dates_cadence_skip_and_brief():
    rows, _ = m.build(topics_csv(), MON, [1, 3], skip={dt.date(2026, 1, 8)}, lead_days=5)
    dates = [r["date"] for r in rows]
    assert dates[:3] == ["2026-01-06", "2026-01-13", "2026-01-15"]
    assert rows[0]["brief_due"] == "2026-01-01" and rows[0]["weekday"] == "Tue" and rows[0]["week"] == 1


def test_interval_weeks():
    rows, _ = m.build(topics_csv(), MON, [0], interval_weeks=2)
    assert [r["date"] for r in rows[:3]] == ["2026-01-05", "2026-01-19", "2026-02-02"]


def test_start_midweek_skips_earlier_days():
    rows, _ = m.build(topics_csv(), dt.date(2026, 1, 7), [0, 4])
    assert rows[0]["date"] == "2026-01-09"


def test_weeks_limit_and_warnings():
    rows, warnings = m.build(topics_csv(), MON, [1, 3], weeks=2)
    assert len(rows) == 4
    text = "\n".join(warnings)
    assert "did not fit" in text
    assert "'content repurposing' targeted by 2 topics" in text
    assert "have no keyword" in text


def test_owners_and_repurpose_columns():
    rows, _ = m.build(topics_csv(), MON, [4], owners=["Ana", "Ben"], repurpose=True, newsletter_day=4)
    assert [r["owner"] for r in rows[:3]] == ["Ana", "Ben", "Ana"]
    assert rows[0]["date"] == "2026-01-09" and rows[0]["linkedin_date"] == "2026-01-12"
    assert rows[0]["newsletter_date"] == "2026-01-16"


def test_cluster_without_pillar_and_funnel_mix():
    t = [m.norm_topic({"cluster": "X", "title": f"T{i}", "keyword": f"k{i}", "funnel": "awareness"}) for i in range(6)]
    _, warnings = m.build(t, MON, [1])
    assert any("no pillar" in w for w in warnings) and any("6 of 6 topics are tofu" in w for w in warnings)


@pytest.mark.parametrize(
    "text,fmt,message",
    [
        ("name,x\na,b\n", "csv", "title"),
        ("{bad", "json", "invalid JSON"),
        ('{"clusters": 3}', "json", "must be"),
        ("title\n", "csv", "no topics"),
    ],
)
def test_bad_input(text, fmt, message):
    with pytest.raises(m.InputError, match=message):
        m.load_topics(text, fmt)


def test_parse_days():
    assert m.parse_days("Tuesday, thu") == [1, 3]
    with pytest.raises(m.InputError):
        m.parse_days("funday")


def test_cli_csv_json_and_out(tmp_path):
    src = str(fixture(SKILL, "topics.csv"))
    r = run_script(SKILL, SCRIPT, src, "--start", "2026-01-05", "--weeks", "4", "--skip", "2026-01-08")
    assert r.returncode == 0
    rows = list(csv.DictReader(io.StringIO(r.stdout)))
    assert len(rows) == 7 and rows[0]["date"] == "2026-01-06" and "warning:" in r.stderr
    strict = run_script(SKILL, SCRIPT, src, "--start", "2026-01-05", "--strict")
    assert strict.returncode == 1
    js = run_script(
        SKILL, SCRIPT, str(fixture(SKILL, "topics.json")), "--start", "2026-01-05", "--json", "--days", "mon,wed,fri"
    )
    data = json.loads(js.stdout)
    assert [r["weekday"] for r in data["rows"][:3]] == ["Mon", "Wed", "Fri"]
    out = tmp_path / "cal.csv"
    assert run_script(SKILL, SCRIPT, src, "--start", "2026-01-05", "--out", str(out)).returncode == 0
    assert out.read_text().startswith("date,weekday")
    assert run_script(SKILL, SCRIPT, src, "--out", str(out)).returncode == 2
    assert run_script(SKILL, SCRIPT, src, "--out", str(out), "--force").returncode == 0
    assert run_script(SKILL, SCRIPT, src, "--start", "05/01/2026").returncode == 2
    assert run_script(SKILL, SCRIPT, str(tmp_path / "missing.csv")).returncode == 2


def test_template_asset_builds():
    from conftest import SKILLS

    text = (SKILLS / SKILL / "assets" / "topics-template.csv").read_text()
    rows, warnings = m.build(m.load_topics(text, "csv"), MON, [1, 3])
    assert len(rows) == 7 and rows[0]["type"] == "pillar" and rows[1]["type"] == "pillar"
    assert not any("cannibalisation" in w for w in warnings)
