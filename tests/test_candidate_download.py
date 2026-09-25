"""Unit tests for pipeline/run_candidate_download.py's parsing/selection
logic (no network, no yt-dlp/ffmpeg calls -- those are exercised manually
against a real cookies.txt, not in CI)."""

from pipeline.run_candidate_download import Candidate, _slugify, parse_candidates, select_candidates

FIXTURE_DOC = """\
# QB Motion Atlas — Candidate Clip Research (Agent 1)

## Buffalo Bills — Josh Allen

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=aaa111 | Mechanics channel | "Josh Allen Mechanics" | High | short |
| https://www.youtube.com/watch?v=bbb222 | Combine footage | "Josh Allen Combine" | Medium | long, needs isolation |
| https://www.youtube.com/shorts/ccc333 | Mechanics channel | "Josh Allen Shorts breakdown" | Medium-high | short |

## Houston Texans — C.J. Stroud

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=ddd444 | Mechanics channel | "CJ Stroud Mechanics" | High | short |

## Washington Commanders — Marcus Mariota (current starter; see ambiguity note above)

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=eee555 | Performance Lab | "Mariota Breakdown" | High | short |
"""


def test_slugify_handles_periods_and_apostrophes():
    assert _slugify("C.J. Stroud") == "cj_stroud"
    assert _slugify("Ja'Marr Chase") == "jamarr_chase"


def test_parse_candidates_extracts_all_rows(tmp_path):
    doc = tmp_path / "candidates.md"
    doc.write_text(FIXTURE_DOC)

    candidates = parse_candidates(doc)

    assert len(candidates) == 5
    assert candidates[0] == Candidate(
        qb_name="josh_allen",
        url="https://www.youtube.com/watch?v=aaa111",
        source="Mechanics channel",
        description='"Josh Allen Mechanics"',
        confidence="High",
        clip_type="short",
    )
    assert {c.qb_name for c in candidates} == {"josh_allen", "cj_stroud", "marcus_mariota"}


def test_parse_candidates_strips_starter_ambiguity_parenthetical(tmp_path):
    doc = tmp_path / "candidates.md"
    doc.write_text(FIXTURE_DOC)

    candidates = parse_candidates(doc)

    mariota_rows = [c for c in candidates if c.qb_name == "marcus_mariota"]
    assert len(mariota_rows) == 1


def test_select_candidates_filters_by_tier_and_type(tmp_path):
    doc = tmp_path / "candidates.md"
    doc.write_text(FIXTURE_DOC)
    candidates = parse_candidates(doc)

    selected = select_candidates(
        candidates, confidence_tiers={"High", "Medium-high"}, clip_types={"short"}, limit_per_qb=2
    )

    urls = {c.url for c in selected}
    assert "https://www.youtube.com/watch?v=aaa111" in urls  # High, short
    assert "https://www.youtube.com/shorts/ccc333" in urls  # Medium-high, short
    assert "https://www.youtube.com/watch?v=bbb222" not in urls  # long, needs isolation -- excluded
    assert "https://www.youtube.com/watch?v=ddd444" in urls
    assert "https://www.youtube.com/watch?v=eee555" in urls


def test_select_candidates_respects_limit_per_qb(tmp_path):
    doc = tmp_path / "candidates.md"
    doc.write_text(FIXTURE_DOC)
    candidates = parse_candidates(doc)

    selected = select_candidates(
        candidates, confidence_tiers={"High", "Medium-high"}, clip_types={"short"}, limit_per_qb=1
    )

    josh_allen_rows = [c for c in selected if c.qb_name == "josh_allen"]
    assert len(josh_allen_rows) == 1
    assert josh_allen_rows[0].url == "https://www.youtube.com/watch?v=aaa111"  # first match wins


def test_real_candidates_doc_parses_without_error():
    """Sanity check against the actual docs/qb_candidate_clips.md -- catches
    a format drift between this parser and the real document."""
    candidates = parse_candidates()
    assert len(candidates) > 100
    qb_names = {c.qb_name for c in candidates}
    assert "josh_allen" in qb_names
    assert "patrick_mahomes" in qb_names
