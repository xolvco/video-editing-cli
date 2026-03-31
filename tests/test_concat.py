from pathlib import Path

import pytest

from video_editing_cli.cli import build_parser
from video_editing_cli.operations import concat_videos
from video_editing_cli.service import VideoEditingService


def test_concat_parser_collects_multiple_inputs() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "concat",
            "joined.mp4",
            "a.mp4",
            "b.mp4",
            "--start",
            "00:00:03",
            "--end",
            "00:00:10",
            "--spacer-seconds",
            "2",
            "--audio-fade-seconds",
            "0.5",
            "--markers",
        ]
    )

    assert args.command == "concat"
    assert args.output == "joined.mp4"
    assert args.inputs == ["a.mp4", "b.mp4"]
    assert args.start == "00:00:03"
    assert args.end == "00:00:10"
    assert args.spacer_seconds == 2.0
    assert args.audio_fade_seconds == 0.5
    assert args.markers is True


def test_concat_requires_two_inputs(tmp_path: Path) -> None:
    clip = tmp_path / "clip.mp4"
    clip.write_text("placeholder", encoding="utf-8")

    with pytest.raises(ValueError):
        concat_videos([clip], tmp_path / "out.mp4")


def test_concat_rejects_end_before_start(tmp_path: Path) -> None:
    clip_a = tmp_path / "clip-a.mp4"
    clip_b = tmp_path / "clip-b.mp4"
    clip_a.write_text("a", encoding="utf-8")
    clip_b.write_text("b", encoding="utf-8")

    with pytest.raises(ValueError):
        concat_videos([clip_a, clip_b], tmp_path / "out.mp4", start="10", end="5")


def test_concat_advanced_mode_builds_filtered_ffmpeg_graph(tmp_path: Path, monkeypatch) -> None:
    clip_a = tmp_path / "clip_one.mp4"
    clip_b = tmp_path / "clip_two.mp4"
    clip_a.write_text("a", encoding="utf-8")
    clip_b.write_text("b", encoding="utf-8")
    captured: dict[str, list[str]] = {}

    def fake_probe_media(self, input_path):  # type: ignore[no-untyped-def]
        return {"format": {"duration": "12.0"}}

    def fake_run_ffmpeg(args):  # type: ignore[no-untyped-def]
        captured["args"] = list(args)
        return None

    monkeypatch.setattr(VideoEditingService, "probe_media", fake_probe_media)
    monkeypatch.setattr("video_editing_cli.service.run_ffmpeg", fake_run_ffmpeg)

    concat_videos(
        [clip_a, clip_b],
        tmp_path / "out.mp4",
        start="00:00:01",
        end="00:00:05",
        spacer_seconds=2.0,
        audio_fade_seconds=0.5,
        markers=True,
    )

    command = captured["args"]
    command_text = " ".join(command)

    assert "-filter_complex" in command
    assert "trim=start=1.000:duration=4.000" in command_text
    assert "tpad=stop_mode=add:stop_duration=2.000" in command_text
    assert "afade=t=in:st=0:d=0.500" in command_text
    assert "use_metadata_tags" in command
    assert "libx264" in command
