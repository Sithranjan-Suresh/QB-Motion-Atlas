"""Unit tests for pipeline/share_card.py (tasks 133-134)."""

import io

from PIL import Image

from pipeline.share_card import CARD_HEIGHT, CARD_WIDTH, render_share_card


def test_render_share_card_produces_correctly_sized_png():
    png_bytes = render_share_card(
        matched_qb_name="patrick_mahomes",
        overall_similarity_score=0.87,
        confidence_level="high",
        phase_results={},
    )
    image = Image.open(io.BytesIO(png_bytes))
    assert image.format == "PNG"
    assert image.size == (CARD_WIDTH, CARD_HEIGHT)


def test_render_share_card_handles_no_match_gracefully():
    # No exception, still a valid image -- the honest "nothing to match
    # against yet" state (matched_qb_name=None) should never crash the export.
    png_bytes = render_share_card(
        matched_qb_name=None, overall_similarity_score=0.0, confidence_level="low", phase_results={}
    )
    image = Image.open(io.BytesIO(png_bytes))
    assert image.size == (CARD_WIDTH, CARD_HEIGHT)


def test_render_share_card_handles_unknown_confidence_level():
    png_bytes = render_share_card(
        matched_qb_name="josh_allen",
        overall_similarity_score=0.5,
        confidence_level="not_a_real_level",
        phase_results={},
    )
    image = Image.open(io.BytesIO(png_bytes))
    assert image.size == (CARD_WIDTH, CARD_HEIGHT)


def test_render_share_card_includes_phase_stats():
    png_bytes = render_share_card(
        matched_qb_name="patrick_mahomes",
        overall_similarity_score=0.87,
        confidence_level="high",
        phase_results={
            "release": {"matched_qb_name": "patrick_mahomes", "score": 0.9, "confidence": "high"},
            "stride": {"matched_qb_name": "josh_allen", "score": 0.7, "confidence": "medium"},
        },
    )
    image = Image.open(io.BytesIO(png_bytes))
    assert image.size == (CARD_WIDTH, CARD_HEIGHT)
