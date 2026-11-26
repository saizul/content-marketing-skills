import json

from conftest import fixture, load_script, run_script

SKILL = "linkedin-post-writer"
SCRIPT = "check_post.py"
m = load_script(SKILL, SCRIPT)


def checks(result):
    return {f["check"] for f in result["findings"]}


def test_good_post_has_no_findings():
    r = m.check(fixture(SKILL, "good-post.txt").read_text(encoding="utf-8"), no_emoji=True)
    assert r["findings"] == []
    assert r["stats"]["hashtags"] == 3 and r["stats"]["links"] == 0
    assert r["hook"].startswith("We cut")


def test_bad_post_findings():
    r = m.check(fixture(SKILL, "bad-post.txt").read_text(encoding="utf-8"), no_emoji=True)
    c = checks(r)
    for expected in (
        "emoji.present",
        "hook.too_long",
        "hook.weak_opener",
        "format.wall_of_text",
        "hashtags.too_many",
        "hashtags.duplicate",
        "links.in_post",
        "format.unicode_bold",
        "format.shouting",
        "cta.missing",
    ):
        assert expected in c, expected


def test_over_limit():
    r = m.check("Hook line.\n\n" + "word " * 700)
    assert "length.over_limit" in checks(r)


def test_emoji_allowed_without_flag():
    r = m.check("Short hook \U0001f680\n\nWhat do you think?")
    assert "emoji.present" not in checks(r) and r["stats"]["emoji"] == 1


def test_arrows_and_symbols_are_not_emoji():
    assert not m.is_emoji("→")
    assert not m.is_emoji("©")
    assert m.is_emoji("\U0001f525")


def test_allow_links_and_cta_before_hashtags():
    text = "Hook.\n\nRead it at https://example.com/post\n\nWhat would you add?\n\n#Content"
    assert "links.in_post" in checks(m.check(text))
    r = m.check(text, allow_links=True)
    assert "links.in_post" not in checks(r) and "cta.missing" not in checks(r)


def test_markdown_heading_is_not_hashtag():
    r = m.check("# Title\n\nBody #one #two")
    assert r["stats"]["hashtags"] == 2


def test_empty_post():
    assert checks(m.check("   \n")) == {"post.empty"}


def test_cli(tmp_path):
    ok = run_script(SKILL, SCRIPT, str(fixture(SKILL, "good-post.txt")), "--no-emoji")
    assert ok.returncode == 0 and "No findings" in ok.stdout
    bad = run_script(SKILL, SCRIPT, str(fixture(SKILL, "bad-post.txt")), "--json")
    assert bad.returncode == 1 and json.loads(bad.stdout)["stats"]["hashtags"] == 8
    low_only = run_script(SKILL, SCRIPT, "--text", "Hook\n\nno ask here", "--fail-on", "high")
    assert low_only.returncode == 0
    piped = run_script(SKILL, SCRIPT, "-", stdin="Hook.\n\nThoughts?")
    assert piped.returncode == 0
    assert run_script(SKILL, SCRIPT, str(tmp_path / "missing.txt")).returncode == 2
