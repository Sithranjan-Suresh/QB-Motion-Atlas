"""Unit tests for pipeline/video_licensing.py (task A2)."""

from pipeline.video_licensing import is_video_overlay_eligible


def test_creator_channel_is_eligible():
    assert is_video_overlay_eligible("YouTube coaching channel (@qbperformancelab); non-commercial research/portfolio use")


def test_fan_reupload_is_eligible():
    assert is_video_overlay_eligible("YouTube fan re-upload (@billsbunker) of Bills sideline footage; non-commercial research/portfolio use")


def test_nfl_official_channel_is_not_eligible():
    assert not is_video_overlay_eligible("NFL official YouTube channel; non-commercial research/portfolio use")


def test_team_official_channel_is_not_eligible():
    assert not is_video_overlay_eligible("Baltimore Ravens official YouTube channel; non-commercial research/portfolio use")


def test_case_insensitive():
    assert not is_video_overlay_eligible("NFL Official Youtube Channel")


def test_kill_switch_disables_everything(monkeypatch):
    monkeypatch.setenv("REFERENCE_VIDEO_OVERLAY_ENABLED", "false")
    assert not is_video_overlay_eligible("YouTube coaching channel (@qbperformancelab)")


def test_kill_switch_default_is_enabled(monkeypatch):
    monkeypatch.delenv("REFERENCE_VIDEO_OVERLAY_ENABLED", raising=False)
    assert is_video_overlay_eligible("YouTube coaching channel (@qbperformancelab)")
