import json

import pytest

from conftest import fixture, load_script, run_script

SKILL = "blog-post-writer"
SCRIPT = "score_draft.py"
m = load_script(SKILL, SCRIPT)


def checks(result):
    return {f["check"] for f in result["findings"]}


def test_good_post_scores_high():
    r = m.analyze(fixture(SKILL, "good-post.md").read_text(), min_words=250)
    assert r["score"] >= 90
    assert r["keyword"]["in_title"] and r["keyword"]["in_first_100_words"] and r["keyword"]["in_slug"]
    assert all(r["eeat_signals"].values())
    assert not [f for f in r["findings"] if f["severity"] in ("high", "medium")]


def test_bad_post_findings():
    r = m.analyze(fixture(SKILL, "bad-post.md").read_text(), keyword="marketing strategy")
    c = checks(r)
    for expected in (
        "structure.multiple_h1",
        "structure.skipped_level",
        "meta.title_length",
        "meta.no_description",
        "keyword.intro",
        "media.missing_alt",
        "links.no_internal",
        "readability.passive_voice",
        "hook.generic_opening",
        "eeat.author",
        "eeat.experience",
    ):
        assert expected in c, expected
    assert r["score"] < 40
    assert r["metrics"]["passive_sentences"] >= 3


def test_findings_sorted_by_severity():
    r = m.analyze(fixture(SKILL, "bad-post.md").read_text())
    order = [m.SEVERITY_ORDER[f["severity"]] for f in r["findings"]]
    assert order == sorted(order, reverse=True)


def test_keyword_stuffing():
    body = "# SEO tips\n\n" + "SEO tips are SEO tips. " * 30
    r = m.analyze(body, keyword="seo tips")
    assert "keyword.stuffing" in checks(r)
    assert r["keyword"]["density_pct"] > 2.5


def test_no_keyword_is_info_only():
    r = m.analyze("# Title here\n\nShort text.\n")
    assert any(f["check"] == "keyword.none" and f["severity"] == "info" for f in r["findings"])


def test_code_blocks_ignored():
    text = "# T\n\n```python\n# not a heading\nx = 1\n```\n\nReal sentence here.\n"
    doc = m.parse_markdown(text)
    assert [h["text"] for h in doc["headings"]] == ["T"]
    assert doc["paragraphs"] == ["Real sentence here."]


def test_html_img_without_alt_and_links():
    text = '# T\n\n<img src="a.png"> and <img src="b.png" alt="Chart">\n\n[a](/x/) [b](https://other.org/)\n'
    doc = m.parse_markdown(text)
    assert [i["alt"] for i in doc["images"]] == ["", "Chart"]
    internal, external = m.classify_links(doc["links"], None)
    assert internal == ["/x/"] and external == ["https://other.org/"]


def test_site_links_count_as_internal():
    internal, external = m.classify_links(["https://www.example.com/a/", "https://example.org/"], "example.com")
    assert internal == ["https://www.example.com/a/"] and external == ["https://example.org/"]


@pytest.mark.parametrize(
    "sentence,expected",
    [
        ("The report was written by the team.", True),
        ("Mistakes were made.", True),
        ("The page is being updated quickly.", True),
        ("We wrote the report.", False),
        ("You need to feed the cat.", False),
        ("Results are indeed good.", False),
    ],
)
def test_passive(sentence, expected):
    assert m.is_passive(sentence) is expected


def test_syllables_and_sentences():
    assert m.count_syllables("cat") == 1
    assert m.count_syllables("calendar") == 3
    assert m.split_sentences("Use tools, e.g. a sheet. Then publish! Done?") == [
        "Use tools, e.g. a sheet.",
        "Then publish!",
        "Done?",
    ]


def test_frontmatter_lists():
    fm, body = m.parse_frontmatter("---\ntitle: 'A'\ntags:\n  - one\n  - two\nk: [x, y]\n---\nBody\n")
    assert fm == {"title": "A", "tags": ["one", "two"], "k": ["x", "y"]} and body == "Body"


def test_cli_exit_codes(tmp_path):
    good = run_script(SKILL, SCRIPT, str(fixture(SKILL, "good-post.md")), "--min-words", "250")
    assert good.returncode == 0 and "Draft score" in good.stdout
    bad = run_script(SKILL, SCRIPT, str(fixture(SKILL, "bad-post.md")), "--json")
    assert bad.returncode == 1
    data = json.loads(bad.stdout)
    assert data["score"] < 70 and data["findings"]
    stdin = run_script(SKILL, SCRIPT, "-", "--min-score", "0", stdin="# Hi\n\nText.\n")
    assert stdin.returncode == 0
    missing = run_script(SKILL, SCRIPT, str(tmp_path / "nope.md"))
    assert missing.returncode == 2
