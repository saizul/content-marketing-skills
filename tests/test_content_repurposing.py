import json

from conftest import fixture, load_script, run_script

SKILL = "content-repurposing"
SCRIPT = "repurpose.py"
m = load_script(SKILL, SCRIPT)
POST = fixture("blog-post-writer", "good-post.md")


def post():
    return m.parse_post(POST.read_text())


def test_parse_post():
    p = post()
    assert p["title"] == "Content Calendar for Small Teams: A Simple System"
    headings = [x["heading"] for x in p["points"]]
    assert headings[0] == "Start with three topic clusters"
    assert "What to do next" not in headings  # wrap-up sections are not points
    assert p["stats"] and "38%" in p["stats"][0]


def test_linkedin_within_limits_no_emoji():
    text = m.linkedin(post(), None, 5)
    assert len(text) <= m.LINKEDIN_LIMIT
    assert text.splitlines()[0].startswith("We tested this with 14 client sites")
    assert not any(0x1F300 <= ord(c) <= 0x1FAFF for c in text)
    assert text.rstrip().endswith("?")


def test_linkedin_trims_points_when_too_long():
    p = post()
    p["points"] = [{"heading": f"Point {i}", "point": "word " * 30} for i in range(40)]
    assert len(m.linkedin(p, None, 40)) <= m.LINKEDIN_LIMIT


def test_x_thread_lengths_and_numbering():
    p = post()
    p["url"] = "https://example.com/" + "a" * 200
    thread = m.x_thread(p, None, 5)
    n = len(thread)
    assert all(m.x_length(t) <= m.X_LIMIT for t in thread)
    assert thread[0].endswith(f"1/{n}") and thread[-1].endswith(f"{n}/{n}")
    assert "https://example.com/" in thread[-1]


def test_long_section_split_across_posts():
    p = post()
    p["points"] = [{"heading": "Long", "point": " ".join(["This sentence has quite a few words in it."] * 12)}]
    thread = m.x_thread(p, None, 5)
    assert len(thread) >= 4 and all(m.x_length(t) <= m.X_LIMIT for t in thread)


def test_x_length_counts_urls_as_23():
    assert m.x_length("see https://example.com/" + "x" * 100) == 4 + 23


def test_newsletter_and_video():
    p = post()
    nl = m.newsletter(p, "Get the template", 3)
    assert all(len(s) <= 50 for s in nl["subjects"]) and len(nl["preview"]) <= 110
    assert "[Get the template]({{post_url}})" in nl["body"] and "unsubscribe" in nl["body"].lower()
    v = m.video(p, None, 5, 60)
    beats = [b["beat"] for b in v["beats"]]
    assert beats[0] == "HOOK" and beats[-1] == "CTA" and beats.count("POINT") <= 3
    assert v["words"] <= 150 and any("hook is" in n for n in v["notes"])
    short = m.video(p, None, 5, 10)
    assert [b["beat"] for b in short["beats"]].count("POINT") == 1


def test_post_without_sections():
    p = m.parse_post("# Just a title\n\nOne short intro sentence here. Another sentence follows it.\n")
    out = m.render(p, list(m.CHANNELS), None, 5, 60)
    assert out["source_points"] == 0 and out["linkedin"]["text"] and out["x"]["posts"]


def test_cli(tmp_path):
    r = run_script(SKILL, SCRIPT, str(POST), "--channels", "linkedin,x")
    assert r.returncode == 0 and "===== linkedin.md" in r.stdout and "===== x-thread.md" in r.stdout
    js = run_script(SKILL, SCRIPT, str(POST), "--json", "--url", "https://example.com/p/")
    data = json.loads(js.stdout)
    assert set(data) >= {"linkedin", "x", "newsletter", "video"}
    assert "https://example.com/p/" in data["x"]["posts"][-1]
    out = tmp_path / "drafts"
    assert run_script(SKILL, SCRIPT, str(POST), "--out", str(out)).returncode == 0
    assert sorted(f.name for f in out.iterdir()) == ["linkedin.md", "newsletter.md", "video-script.md", "x-thread.md"]
    assert (out / "newsletter.md").read_text().startswith("---\nsubject:")
    assert run_script(SKILL, SCRIPT, str(POST), "--out", str(out)).returncode == 2
    assert run_script(SKILL, SCRIPT, str(POST), "--out", str(out), "--force").returncode == 0
    assert run_script(SKILL, SCRIPT, str(POST), "--channels", "tiktok").returncode == 2
    assert run_script(SKILL, SCRIPT, str(tmp_path / "missing.md")).returncode == 2


def test_channel_templates_exist_without_emoji():
    from conftest import SKILLS

    folder = SKILLS / SKILL / "assets" / "templates"
    names = sorted(p.name for p in folder.iterdir())
    assert names == ["linkedin.md", "newsletter.md", "video-script.md", "x-thread.md"]
    for p in folder.iterdir():
        assert not any(0x1F300 <= ord(c) <= 0x1FAFF for c in p.read_text(encoding="utf-8"))
