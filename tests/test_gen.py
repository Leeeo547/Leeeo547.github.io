import copy
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gen_from_bank as g  # noqa: E402

MINI_BANK = yaml.safe_load("""
profile:
  name: Test Person
  tagline: Tagline
  email: t@example.edu
  location: Nowhere
  links: {github: https://github.com/t}
  research_statement: One sentence.
  bio_long: Para.
  interests: [A]
education:
  - {school: U, degree: MSc, field: Robotics, start: 2025-08, end: 2027-05, expected: true, gpa: "4.0", location: X, notes: ["note"]}
publications:
  - id: p1
    title: "Paper One"
    authors: ["Test Person*", "et al."]
    me: Test Person
    author_note: "*Equal contribution."
    venue: Venue
    status: under_review
    status_text: "Under review, Venue"
    category: manuscripts
    date: 2026-10-01
    links: {}
    abstract_short: Abstract.
    highlights: ["H1"]
    my_role:
      - {text: "Led X.", own: lead}
    selected: true
    visibility: public
  - id: p2
    title: "Paper Two"
    authors: ["A", "Test Person", "B"]
    me: Test Person
    author_note: ""
    venue: arXiv preprint
    status: preprint
    status_text: "arXiv preprint"
    category: preprints
    date: 2026-09-29
    links: {arxiv: https://arxiv.org/abs/0000.00000}
    abstract_short: Abstract two.
    highlights: []
    my_role: []
    selected: false
    visibility: public
experiences:
  - id: e1
    org: Org
    role: Role
    start: 2026-06
    end: present
    location: L
    pi: ""
    kind: internship
    tags: [data]
    bullets:
      - {text: "Public ok bullet.", tags: [data], own: lead, visibility: public, status: ok}
      - {text: "Pending bullet.", tags: [data], own: lead, visibility: public, status: TBD}
      - {text: "Secret bullet.", tags: [data], own: lead, visibility: private, status: ok}
    project_page:
      slug: proj-one
      order: 1
      title: "Project One"
      teaser: /images/placeholders/proj-one.svg
      excerpt: "Excerpt."
      body_md: "Body **md**."
    visibility: public
  - id: e2
    org: Hidden Org
    role: Role
    start: 2026-01
    end: present
    location: L
    pi: ""
    kind: project
    tags: [VLA]
    bullets:
      - {text: "HIDDEN_MARKER", tags: [VLA], own: lead, visibility: private, status: ok}
    visibility: hold
skills:
  ml: [PyTorch]
  robotics: [ROS 2]
  perception_3d: [OpenCV]
  tools: [Python]
""")


@pytest.fixture
def site(tmp_path: Path) -> Path:
    (tmp_path / "images" / "placeholders").mkdir(parents=True)
    (tmp_path / "images" / "placeholders" / "proj-one.svg").write_text("<svg/>")
    for d in ("_publications", "_portfolio", "_pages", "_data"):
        (tmp_path / d).mkdir()
    return tmp_path


def test_check_valid_bank_has_no_errors(site):
    assert g.check_bank(copy.deepcopy(MINI_BANK), site) == []


def test_check_reports_missing_teaser(site):
    (site / "images" / "placeholders" / "proj-one.svg").unlink()
    errs = g.check_bank(copy.deepcopy(MINI_BANK), site)
    assert any("teaser" in e and "proj-one.svg" in e for e in errs)


def test_check_rejects_bad_visibility_and_http_link(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["experiences"][0]["visibility"] = "sometimes"
    bank["publications"][1]["links"]["arxiv"] = "http://arxiv.org/abs/x"
    errs = g.check_bank(bank, site)
    assert any("visibility" in e for e in errs)
    assert any("https://" in e for e in errs)


def test_check_rejects_selected_hold_publication(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["publications"][0]["visibility"] = "hold"
    errs = g.check_bank(bank, site)
    assert any("selected" in e for e in errs)


def test_tbd_report_lists_pending_bullets():
    lines = g.tbd_report(MINI_BANK)
    assert any("e1" in l and "Pending bullet." in l for l in lines)
    assert not any("Public ok bullet." in l for l in lines)


def test_render_publication_front_matter_and_body():
    fname, content = g.render_publication(MINI_BANK["publications"][0])
    assert fname == "2026-10-01-p1.md"
    assert content.startswith("---\n")
    assert 'title: "Paper One"' in content
    assert "collection: publications" in content
    assert "category: manuscripts" in content
    assert "permalink: /publication/2026-10-01-p1" in content
    assert "Under review, Venue" in content
    assert "<b>Test Person*</b>" in content          # me is bolded in citation
    assert "- Led X." in content                     # my_role bullets rendered
    assert "GENERATED" in content


def test_render_publication_without_links_has_no_paperurl():
    _, content = g.render_publication(MINI_BANK["publications"][0])
    assert "paperurl" not in content
    _, content2 = g.render_publication(MINI_BANK["publications"][1])
    assert "paperurl: 'https://arxiv.org/abs/0000.00000'" in content2


def test_render_portfolio_body_only():
    fname, content = g.render_portfolio(MINI_BANK["experiences"][0])
    assert fname == "proj-one.md"
    assert "collection: portfolio" in content
    assert "permalink: /portfolio/proj-one" in content
    assert "order: 1" in content
    assert "/images/placeholders/proj-one.svg" in content
    assert "Body **md**." in content
    for b in ("Public ok bullet.", "Pending bullet.", "Secret bullet."):
        assert b not in content


def test_citation_unpublished_shows_status_not_venue_italic():
    _, content = g.render_publication(MINI_BANK["publications"][0])
    cit = [l for l in content.splitlines() if l.startswith("citation:")][0]
    assert "Under review, Venue" in cit
    assert "<i>Venue</i>" not in cit
    cv = g.render_cv(MINI_BANK)
    assert "<i>Venue</i>" not in cv


def test_citation_published_shows_italic_venue():
    pub = copy.deepcopy(MINI_BANK["publications"][1])
    pub["status"] = "published"
    pub["venue"] = "Venue"
    pub["status_text"] = "Published"
    _, content = g.render_publication(pub)
    cit = [l for l in content.splitlines() if l.startswith("citation:")][0]
    assert "<i>Venue</i>" in cit


def test_render_cv_skips_hold_and_private():
    cv = g.render_cv(MINI_BANK)
    assert cv.startswith("---\n")
    assert "permalink: /cv/" in cv
    assert "Education" in cv and "Publications" in cv and "Skills" in cv
    assert "Org" in cv and "Public ok bullet." in cv
    assert "Hidden Org" not in cv and "HIDDEN_MARKER" not in cv
    assert "Secret bullet." not in cv and "Pending bullet." not in cv
    assert "/files/cv.pdf" not in cv   # no real PDF -> no button (see test_cv_pdf_button_only_for_real_pdf)


def test_generate_writes_expected_files(site):
    paths = g.generate(copy.deepcopy(MINI_BANK), site)
    rel = sorted(str(p.relative_to(site)).replace("\\", "/") for p in paths)
    assert rel == [
        "_pages/cv.md",
        "_portfolio/proj-one.md",
        "_publications/2026-09-29-p2.md",
        "_publications/2026-10-01-p1.md",
    ]
    assert "HIDDEN_MARKER" not in (site / "_pages" / "cv.md").read_text(encoding="utf-8")


def test_generate_removes_stale_generated_files(site):
    stale = site / "_publications" / "1999-01-01-old.md"
    stale.write_text(f"---\n# {g.GENERATED_MARK}\n---\n", encoding="utf-8")
    g.generate(copy.deepcopy(MINI_BANK), site)
    assert not stale.exists()


def test_generate_keeps_handwritten_file_mentioning_generated(site):
    hand = site / "_publications" / "1999-01-01-hand.md"
    hand.write_text("---\ntitle: x\n---\nThis was GENERATED by hand.\n", encoding="utf-8")
    g.generate(copy.deepcopy(MINI_BANK), site)
    assert hand.exists()


def test_citation_title_with_quote_has_no_backslash():
    pub = copy.deepcopy(MINI_BANK["publications"][1])
    pub["title"] = 'A "Quoted" Title'
    _, content = g.render_publication(pub)
    cit = [l for l in content.splitlines() if l.startswith("citation:")][0]
    assert 'A "Quoted" Title' in cit
    assert "\\" not in cit


def test_author_match_is_exact():
    pub = {"me": "Test Person", "authors": ["Test Personson", "Test Person*"]}
    html = g._author_html(pub)
    assert "<b>Test Person*</b>" in html
    assert "<b>Test Personson</b>" not in html


def test_check_me_must_match_exactly(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["publications"][1]["authors"] = ["A", "Test Personson"]
    errs = g.check_bank(bank, site)
    assert any("'me'" in e for e in errs)


def test_no_double_period_after_et_al():
    _, content = g.render_publication(MINI_BANK["publications"][0])
    assert "et al. " in content and "et al.." not in content
    cv = g.render_cv(MINI_BANK)
    assert "et al. " in cv and "et al.." not in cv


def test_check_rejects_bad_category(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["publications"][0]["category"] = "books"
    errs = g.check_bank(bank, site)
    assert any("category" in e for e in errs)


def test_generate_skips_hold_publication(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["publications"][1]["visibility"] = "hold"
    paths = g.generate(bank, site)
    assert not any("p2" in p.name for p in paths)
    assert not (site / "_publications" / "2026-09-29-p2.md").exists()


def test_cv_orders_under_review_before_preprint():
    cv = g.render_cv(MINI_BANK)
    assert cv.index("Paper One") < cv.index("Paper Two")


def test_cli_check_mode_exit_codes(site):
    bank_path = site / "_data" / "bank.yml"
    bank_path.write_text(yaml.safe_dump(MINI_BANK, sort_keys=False), encoding="utf-8")
    assert g.main(["--check", "--bank", str(bank_path), "--root", str(site)]) == 0
    assert not list((site / "_publications").iterdir())   # check mode writes nothing
    bad = copy.deepcopy(MINI_BANK)
    bad["experiences"][0]["visibility"] = "nope"
    bank_path.write_text(yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")
    assert g.main(["--check", "--bank", str(bank_path), "--root", str(site)]) == 1


# ----------------------------------------------------------------------------- final-review fixes

def test_check_accepts_hold_stub(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["experiences"].append({"id": "x", "visibility": "hold"})
    bank["publications"].append({"id": "px", "visibility": "hold"})
    assert g.check_bank(bank, site) == []
    g.render_cv(bank)  # renderers tolerate stubs


def test_check_null_bullets_reports_error_not_exception(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["experiences"][0]["bullets"] = None
    errs = g.check_bank(bank, site)
    assert any("bullets" in e for e in errs)


def test_check_null_fields_no_crash(site):
    bank = copy.deepcopy(MINI_BANK)
    p = bank["publications"][0]
    p["my_role"] = None
    p["links"] = None
    p["highlights"] = None
    bank["education"][0]["notes"] = None
    del bank["education"][0]["gpa"]
    bank["skills"]["ml"] = None
    errs = g.check_bank(bank, site)
    assert any("skills" in e for e in errs)
    g.render_cv(bank)
    bank["publications"][1]["authors"] = None
    errs = g.check_bank(bank, site)
    assert any("authors" in e for e in errs)


def test_check_education_required_fields(site):
    bank = copy.deepcopy(MINI_BANK)
    del bank["education"][0]["school"]
    errs = g.check_bank(bank, site)
    assert any("education" in e and "school" in e for e in errs)


def test_render_publication_null_highlights():
    pub = copy.deepcopy(MINI_BANK["publications"][0])
    pub["highlights"] = None
    pub["my_role"] = None
    pub["links"] = None
    _, content = g.render_publication(pub)
    assert "Highlights" not in content


def test_category_derived_from_status():
    pub = copy.deepcopy(MINI_BANK["publications"][1])
    pub["status"] = "published"
    del pub["category"]
    _, content = g.render_publication(pub)
    assert "category: published" in content


def test_check_category_contradicting_status(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["publications"][1]["category"] = "manuscripts"   # status: preprint
    errs = g.check_bank(bank, site)
    assert any("category" in e for e in errs)
    bank = copy.deepcopy(MINI_BANK)
    for p in bank["publications"]:
        del p["category"]
    assert g.check_bank(bank, site) == []


def test_selected_flag_rendered():
    _, c1 = g.render_publication(MINI_BANK["publications"][0])
    assert "selected: true" in c1
    _, c2 = g.render_publication(MINI_BANK["publications"][1])
    assert "selected: false" in c2
    pub = copy.deepcopy(MINI_BANK["publications"][0])
    del pub["selected"]
    _, c3 = g.render_publication(pub)
    assert "selected: true" in c3


def test_denylist_hit_in_public_bullet(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["experiences"][0]["bullets"][0]["text"] = "Worked at a Hospital."
    errs = g.check_bank(bank, site)
    assert any("e1" in e and "hospital" in e.lower() for e in errs)


def test_denylist_ara_word_case_sensitive(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["experiences"][0]["project_page"]["body_md"] = "The ARA project."
    errs = g.check_bank(bank, site)
    assert any("ARA" in e for e in errs)
    bank["experiences"][0]["project_page"]["body_md"] = "SARM2 and para."
    assert g.check_bank(bank, site) == []


def test_denylist_skips_hold_items(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["experiences"][1]["bullets"][0]["text"] = "skill-loop hospital"
    assert g.check_bank(bank, site) == []


def test_lidar_percent_rule(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["experiences"][0]["bullets"][0]["text"] = "Reward model reaches 87% accuracy."
    assert g.check_bank(bank, site) == []          # id e1: allowed
    bank["experiences"][0]["id"] = "gim"
    assert g.check_bank(bank, site) == []
    bank["experiences"][0]["id"] = "lidar"
    errs = g.check_bank(bank, site)
    assert any("lidar" in e and "%" in e for e in errs)


def test_liquid_guard(site):
    for bad in ("a {{ x }}", "{% raw %}", "end %}", "b }}"):
        bank = copy.deepcopy(MINI_BANK)
        bank["publications"][0]["abstract_short"] = bad
        errs = g.check_bank(bank, site)
        assert any("Liquid" in e or "liquid" in e for e in errs), bad


def test_duplicate_ids_and_order(site):
    bank = copy.deepcopy(MINI_BANK)
    bank["publications"].append(copy.deepcopy(bank["publications"][0]))
    errs = g.check_bank(bank, site)
    assert any("duplicate publication id" in e for e in errs)

    bank = copy.deepcopy(MINI_BANK)
    dup = copy.deepcopy(bank["experiences"][0])
    bank["experiences"].append(dup)
    errs = g.check_bank(bank, site)
    assert any("duplicate experience id" in e for e in errs)

    bank = copy.deepcopy(MINI_BANK)
    other = copy.deepcopy(bank["experiences"][0])
    other["id"] = "e3"
    other["project_page"]["slug"] = "proj-two"
    bank["experiences"].append(other)
    errs = g.check_bank(bank, site)
    assert any("duplicate project order" in e for e in errs)


def test_cv_pdf_button_only_for_real_pdf(site):
    (site / "files").mkdir()
    pdf = site / "files" / "cv.pdf"
    assert "Download PDF" not in g.render_cv(MINI_BANK, site_root=site)
    pdf.write_bytes(b"x" * 100)
    assert "Download PDF" not in g.render_cv(MINI_BANK, site_root=site)
    pdf.write_bytes(b"x" * 5000)
    assert "Download PDF" in g.render_cv(MINI_BANK, site_root=site)
    assert "Download PDF" not in g.render_cv(MINI_BANK)
