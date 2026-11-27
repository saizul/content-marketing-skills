import json

from conftest import fixture, load_script, run_script

SKILL = "headline-testing"
SCRIPT = "score_headlines.py"
m = load_script(SKILL, SCRIPT)


def lines():
    return fixture(SKILL, "headlines.txt").read_text().splitlines()


def test_ranking_prefers_specific_headlines():
    results = m.rank([h for h in lines() if not h.startswith("#")], "seo", "content calendar")
    assert results[0]["headline"].startswith("7 Content Calendar Mistakes")
    worst = results[-1]["headline"]
    assert worst.startswith("Some Things")
    by = {r["headline"]: r for r in results}
    bait = by["You Won't Believe This SHOCKING Content Calendar Trick!!!"]
    assert any("clickbait" in f for f in bait["flags"]) and any("ALL CAPS" in f for f in bait["flags"])
    assert bait["score"] < results[0]["score"] - 30


def test_parts_and_formulas():
    r = m.score_headline("How to Build a Content Calendar Your Team Will Actually Use", "seo", "content calendar")
    assert "how-to" in r["formulas"] and r["parts"]["keyword"] == 15 and r["parts"]["length"] == 25
    r = m.score_headline("Seven Lessons from 100 Client Newsletters", "email")
    assert r["has_number"] and "list" in r["formulas"] and "mistakes" in r["formulas"]


def test_keyword_position_and_missing():
    late = m.score_headline(
        "A Practical Guide for Busy Founders Planning Their Content Calendar", "seo", "content calendar"
    )
    assert late["parts"]["keyword"] == 10
    missing = m.score_headline("A Practical Guide for Busy Founders", "seo", "content calendar")
    assert missing["parts"]["keyword"] == 0 and any("missing keyword" in f for f in missing["flags"])


def test_types_change_length_targets():
    h = "How We Doubled Newsletter Signups Without Paid Ads or Giveaways"
    assert any("long" in f for f in m.score_headline(h, "email")["flags"])
    assert not any("long" in f for f in m.score_headline(h, "social")["flags"])


def test_fake_reply_prefix_in_email():
    r = m.score_headline("Re: your content calendar", "email")
    assert any("deceptive" in f for f in r["flags"])


def test_duplicates_removed():
    assert len(m.rank(["Same headline here", "same headline here ", ""])) == 1


def test_cli(tmp_path):
    ok = run_script(SKILL, SCRIPT, "--file", str(fixture(SKILL, "headlines.txt")), "--keyword", "content calendar")
    assert ok.returncode == 0 and "7 Content Calendar Mistakes" in ok.stdout.splitlines()[1]
    js = run_script(SKILL, SCRIPT, "--json", "--type", "email", "Weekly notes", "Five subject lines that work")
    data = json.loads(js.stdout)
    assert data["type"] == "email" and len(data["results"]) == 2
    weak = run_script(SKILL, SCRIPT, "stuff", "--min-score", "90")
    assert weak.returncode == 1
    piped = run_script(SKILL, SCRIPT, "--file", "-", stdin="How to Write Better Headlines in 10 Minutes\n")
    assert piped.returncode == 0
    assert run_script(SKILL, SCRIPT, "--file", str(tmp_path / "none.txt")).returncode == 2
    assert run_script(SKILL, SCRIPT, "--file", "-", stdin="").returncode == 2


def test_suffix_counts_towards_length():
    head = "How to Build a Content Calendar That Works"  # 42 chars
    plain = m.score_headline(head, "seo")
    branded = m.score_headline(head, "seo", suffix=" | Acme Marketing Blog")
    assert plain["chars"] == len(head) and plain["parts"]["length"] == 25
    assert branded["chars"] == len(head) + len(" | Acme Marketing Blog")
    assert branded["title"] == head + " | Acme Marketing Blog"
    assert branded["parts"]["length"] < 25
    assert any("suffix '| Acme Marketing Blog' pushes it over 60" in f for f in branded["flags"])


def test_suffix_already_in_headline_is_not_doubled():
    r = m.score_headline("Content Calendar Mistakes | Acme", "seo", suffix=" | Acme")
    assert r["chars"] == len("Content Calendar Mistakes | Acme")
    assert r["title"] == "Content Calendar Mistakes | Acme"


def test_suffix_does_not_move_keyword_position():
    r = m.score_headline(
        "Why Every Team Needs a Content Calendar", "seo", "content calendar", suffix=" | A Very Long Brand"
    )
    assert r["parts"]["keyword"] == 10
    r = m.score_headline(
        "Content Calendar Basics for Small Teams", "seo", "content calendar", suffix=" | A Very Long Brand"
    )
    assert r["parts"]["keyword"] == 15


def test_suffix_cli_json():
    res = run_script(
        SKILL, SCRIPT, "--json", "--suffix", " | Acme", "--min-score", "0", "7 Content Calendar Mistakes to Avoid"
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["suffix"] == " | Acme"
    assert data["results"][0]["title"] == "7 Content Calendar Mistakes to Avoid | Acme"
