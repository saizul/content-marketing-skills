import json

from conftest import fixture, load_script, run_script

SKILL = "newsletter-writer"
SCRIPT = "check_newsletter.py"
m = load_script(SKILL, SCRIPT)


def checks(result):
    return {f["check"] for f in result["findings"]}


def test_good_issue_passes():
    r = m.check(fixture(SKILL, "good-issue.md").read_text())
    assert r["findings"] == []
    assert r["subject"].startswith("The 20-minute brief") and r["stats"]["links"] == 1


def test_bad_issue_findings():
    r = m.check(fixture(SKILL, "bad-issue.md").read_text())
    c = checks(r)
    for expected in (
        "subject.fake_reply",
        "subject.caps",
        "subject.punctuation",
        "subject.spam_phrases",
        "preview.boilerplate",
        "preview.short",
        "merge_tag.broken",
        "images.missing_alt",
        "compliance.unsubscribe",
        "cta.vague_anchor",
        "body.spam_phrases",
    ):
        assert expected in c, expected


def test_missing_subject_and_preview():
    c = checks(m.check("Just a body with [a link](https://example.com). Unsubscribe here."))
    assert {"subject.missing", "preview.missing"} <= c


def test_preview_repeats_subject():
    r = m.check("Body [x](https://example.com) unsubscribe", subject="Big news today", preview="Big news today")
    assert "preview.repeats_subject" in checks(r)


def test_merge_tag_fallbacks():
    r = m.check("Hi {{first_name}}, *|FNAME|* [x](https://example.com) unsubscribe", subject="Hello there friends")
    infos = [f for f in r["findings"] if f["check"] == "merge_tag.no_fallback"]
    assert len(infos) == 2 and all(f["severity"] == "info" for f in infos)
    ok = m.check("Hi {{ first_name | default: 'there' }} [x](https://example.com) unsubscribe", subject="Hello")
    assert "merge_tag.no_fallback" not in checks(ok)


def test_no_emoji_flag():
    r = m.check(
        "Body \U0001f525 [x](https://example.com) unsubscribe", subject="Hot \U0001f525", preview="ok", no_emoji=True
    )
    assert {"emoji.subject", "emoji.body"} <= checks(r)


def test_unsubscribe_merge_tags_recognised():
    for tag in ("*|UNSUB|*", "{{ unsubscribe_url }}", "Manage preferences", "%unsubscribe%"):
        r = m.check(f"Body [x](https://example.com)\n\n{tag}", subject="A clear subject line", preview="x" * 50)
        assert "compliance.unsubscribe" not in checks(r), tag


def test_cli(tmp_path):
    good = run_script(SKILL, SCRIPT, str(fixture(SKILL, "good-issue.md")))
    assert good.returncode == 0 and "No findings" in good.stdout
    bad = run_script(SKILL, SCRIPT, str(fixture(SKILL, "bad-issue.md")), "--json")
    assert bad.returncode == 1 and json.loads(bad.stdout)["subject"].startswith("RE:")
    subject_only = run_script(
        SKILL,
        SCRIPT,
        "--subject",
        "Five hooks we stole this week",
        "--preview",
        "Plus the one we will never use again, and why it failed.",
    )
    assert subject_only.returncode == 0, subject_only.stdout
    assert run_script(SKILL, SCRIPT).returncode == 2
    assert run_script(SKILL, SCRIPT, str(tmp_path / "missing.md")).returncode == 2
