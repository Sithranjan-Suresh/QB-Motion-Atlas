"""Renders the shareable results card (task 133-134) as a PNG, per
docs/share_card_design.md. Pillow-only -- no headless browser, since the
layout is plain typography and shapes over a solid background.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont

CARD_WIDTH = 1200
CARD_HEIGHT = 630
BACKGROUND_COLOR = (17, 24, 39)  # matches the web UI's bg-gray-900
TEXT_COLOR = (255, 255, 255)
MUTED_COLOR = (156, 163, 175)  # matches text-gray-400/500

CONFIDENCE_COLORS = {
    "high": (34, 197, 94),  # green-500
    "medium": (234, 179, 8),  # yellow-500
    "low": (156, 163, 175),  # gray-400
}

_FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"{_FONT_DIR}/{name}", size)


def _centered_text(draw: ImageDraw.ImageDraw, y: int, text: str, font: ImageFont.FreeTypeFont, fill) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (CARD_WIDTH - (bbox[2] - bbox[0])) / 2
    draw.text((x, y), text, font=font, fill=fill)


def render_share_card(
    matched_qb_name: str | None,
    overall_similarity_score: float,
    confidence_level: str,
    phase_results: dict[str, dict],
) -> bytes:
    """Returns a PNG's raw bytes. matched_qb_name=None (task 70's "no
    reference data yet" state) still produces a valid, honest card rather
    than failing -- same gap-handling convention as everywhere else."""
    image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    draw.text((48, 40), "QB MOTION ATLAS", font=_font(22, bold=True), fill=MUTED_COLOR)

    if matched_qb_name is None:
        _centered_text(draw, 260, "No reference match yet", _font(48, bold=True), TEXT_COLOR)
        _centered_text(draw, 330, "check back once the reference database grows", _font(24), MUTED_COLOR)
    else:
        display_name = matched_qb_name.replace("_", " ").title()
        _centered_text(draw, 140, "Your closest match", _font(26), MUTED_COLOR)
        _centered_text(draw, 180, display_name, _font(64, bold=True), TEXT_COLOR)
        _centered_text(draw, 280, f"{round(overall_similarity_score * 100)}%", _font(120, bold=True), TEXT_COLOR)

        badge_color = CONFIDENCE_COLORS.get(confidence_level, MUTED_COLOR)
        badge_text = f"{confidence_level} confidence"
        badge_font = _font(24, bold=True)
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w, badge_h = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 20
        badge_x = (CARD_WIDTH - badge_w) / 2
        badge_y = 420
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=badge_h / 2, fill=badge_color
        )
        draw.text((badge_x + 20, badge_y + 10), badge_text, font=badge_font, fill=BACKGROUND_COLOR)

        if phase_results:
            stats_font = _font(20)
            stats_text = "  |  ".join(
                f"{phase.replace('_', ' ').title()}: {data['matched_qb_name'].replace('_', ' ').title()}"
                for phase, data in list(phase_results.items())[:3]
            )
            _centered_text(draw, 500, stats_text, stats_font, MUTED_COLOR)

    # No fabricated domain here -- this project isn't deployed yet (V1
    # deployment tasks 90-95 are blocked on the user's own cloud accounts,
    # per research_log.md), so a fake-looking live URL would be misleading.
    # Swap in the real deployed URL once one exists.
    draw.text((CARD_WIDTH - 260, CARD_HEIGHT - 50), "QB Motion Atlas", font=_font(18), fill=MUTED_COLOR)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
