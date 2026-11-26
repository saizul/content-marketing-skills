import csv
import json

from conftest import FIXTURES, load_script, run_script

SKILL = "internal-linking"
SCRIPT = "suggest_links.py"
m = load_script(SKILL, SCRIPT)
POSTS = FIXTURES / "internal-linking" / "posts"


def result():
    docs = [m.load_doc(f, root) for f, root in m.collect([str(POSTS)])]
    return m.analyze(docs, {"example.com"})


def test_loads_markdown_and_html():
    docs = {d["file"]: d for d in (m.load_doc(f, r) for f, r in m.collect([str(POSTS)]))}
    assert set(docs) == {
        "content-brief.md",
        "content-calendar.md",
        "topic-clusters.md",
        "repurposing.html",
        "guides/linkedin-hooks.md",
    }
    html = docs["repurposing.html"]
    assert html["title"] == "Content Repurposing Playbook" and html["keywords"] == ["content repurposing"]
    assert html["url"] == "https://example.com/content-repurposing/"
    assert "Privacy" not in html["body"] and "/privacy/" not in html["raw_links"]  # footer and nav skipped
    assert docs["content-calendar.md"]["url"] == "/content-calendar/"
    assert docs["guides/linkedin-hooks.md"]["url"] == "/guides/linkedin-hooks/"


def test_existing_links_resolved_and_orphans():
    r = result()
    assert r["existing_internal_links"] == 3  # relative .md, root-relative, absolute same-site
    assert r["inbound"]["content-calendar.md"] == 1 and r["inbound"]["topic-clusters.md"] == 1
    assert {o["file"] for o in r["orphans"]} == {"repurposing.html", "guides/linkedin-hooks.md"}


def test_suggestions_have_anchors_and_skip_existing():
    r = result()
    pairs = {(s["source"], s["target"]) for s in r["suggestions"]}
    assert ("content-calendar.md", "content-brief.md") not in pairs  # already linked
    assert ("topic-clusters.md", "content-calendar.md") not in pairs
    brief = [s for s in r["suggestions"] if s["source"] == "content-brief.md" and s["target"] == "content-calendar.md"]
    assert brief and brief[0]["anchor"].lower() == "content calendar" and "pillar page" in brief[0]["context"]
    hooks = [s for s in r["suggestions"] if s["source"] == "repurposing.html" and s["target"].endswith("hooks.md")]
    assert hooks and hooks[0]["anchor"] == "LinkedIn hooks"
    assert all(s["source"] != s["target"] for s in r["suggestions"])


def test_max_per_page_and_min_score():
    docs = [m.load_doc(f, root) for f, root in m.collect([str(POSTS)])]
    r = m.analyze(docs, set(), max_per_page=1, min_score=0.0)
    sources = [s["source"] for s in r["suggestions"]]
    assert len(sources) == len(set(sources))
    r = m.analyze([m.load_doc(f, root) for f, root in m.collect([str(POSTS)])], set(), min_score=0.99)
    assert r["suggestions"] == []


def test_norm_url_and_path_url():
    assert m.norm_url("https://www.example.com/a/b", {"example.com"}) == "/a/b/"
    assert m.norm_url("https://other.com/a", {"example.com"}) is None
    assert m.norm_url("mailto:x@example.com", set()) is None
    assert m.norm_url("/blog/post.md#x", set()) == "/blog/post/"
    assert m.path_url("blog/2026-01-05-my-post.md") == "/blog/my-post/"
    assert m.path_url("docs/index.md") == "/docs/"


def test_anchor_candidates_prefer_keywords_and_long_phrases():
    doc = {"keywords": ["topic clusters"], "title": "How to Build Topic Clusters for SEO in 2026"}
    cands = m.anchor_candidates(doc)
    assert cands[0] == "topic clusters" or "Build Topic Clusters" in cands[:2]
    assert not any(c.lower().startswith("how ") for c in cands)


def test_cli(tmp_path):
    r = run_script(SKILL, SCRIPT, str(POSTS), "--site", "example.com")
    assert r.returncode == 0 and "Orphans" in r.stdout
    fail = run_script(SKILL, SCRIPT, str(POSTS), "--site", "https://example.com/", "--fail-on-orphans", "--json")
    assert fail.returncode == 1 and json.loads(fail.stdout)["posts"] == 5
    out = tmp_path / "links.csv"
    run_script(SKILL, SCRIPT, str(POSTS), "--csv", str(out), "--only", "content-brief")
    rows = list(csv.DictReader(out.open()))
    assert rows and all(row["source"] == "content-brief.md" for row in rows)
    assert run_script(SKILL, SCRIPT, str(POSTS), "--csv", str(out)).returncode == 2
    assert run_script(SKILL, SCRIPT, str(POSTS / "content-brief.md")).returncode == 2  # need two posts
    assert run_script(SKILL, SCRIPT, str(tmp_path / "missing")).returncode == 2
