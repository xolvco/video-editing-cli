from pathlib import Path

import pytest

from video_editing_cli.cli import build_parser
from video_editing_cli.operations import concat_videos


def test_concat_parser_collects_multiple_inputs() -> None:
    parser = build_parser()
    args = parser.parse_args(["concat", "joined.mp4", "a.mp4", "b.mp4"])

    assert args.command == "concat"
    assert args.output == "joined.mp4"
    assert args.inputs == ["a.mp4", "b.mp4"]


def test_concat_requires_two_inputs(tmp_path: Path) -> None:
    clip = tmp_path / "clip.mp4"
    clip.write_text("placeholder", encoding="utf-8")

    with pytest.raises(ValueError):
        concat_videos([clip], tmp_path / "out.mp4")
