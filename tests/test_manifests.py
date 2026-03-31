import pytest

from video_editing_cli.manifests import parse_cut_list_manifest, parse_timeline_manifest


def test_parse_cut_list_manifest_v1() -> None:
    manifest = parse_cut_list_manifest(
        {
            "version": 1,
            "sources": [{"id": "session", "path": "session.mp4"}],
            "cuts": [
                {
                    "id": "intro-look",
                    "source": "session",
                    "start": "00:00:05.000",
                    "end": "00:00:06.200",
                    "label": "Intro glance",
                    "tags": ["closeup", "beat"],
                }
            ],
        }
    )

    assert manifest.version == 1
    assert manifest.sources["session"].path.as_posix() == "session.mp4"
    assert manifest.cuts["intro-look"].start_seconds == 5.0
    assert manifest.cuts["intro-look"].end_seconds == 6.2
    assert manifest.cuts["intro-look"].tags == ("closeup", "beat")


def test_parse_timeline_manifest_v1() -> None:
    manifest = parse_timeline_manifest(
        {
            "version": 1,
            "sources": [{"id": "session", "path": "session.mp4"}],
            "cuts": [
                {
                    "id": "intro-look",
                    "source": "session",
                    "start": "00:00:05.000",
                    "duration": "1.5",
                }
            ],
            "defaults": {
                "gap_after_seconds": 0.15,
                "audio_fade_in_seconds": 0.04,
                "audio_fade_out_seconds": 0.05,
            },
            "sections": [{"cut": "intro-look", "title": "Intro", "gap_after_seconds": 0.25}],
            "output": {"path": "out.mp4"},
        }
    )

    assert manifest.defaults.gap_after_seconds == 0.15
    assert manifest.sections[0].cut == "intro-look"
    assert manifest.sections[0].gap_after_seconds == 0.25
    assert manifest.output.path.as_posix() == "out.mp4"


def test_parse_manifest_requires_version_1() -> None:
    with pytest.raises(ValueError):
        parse_cut_list_manifest({"version": 2, "sources": [], "cuts": []})


def test_parse_timeline_manifest_rejects_unknown_cut() -> None:
    with pytest.raises(ValueError):
        parse_timeline_manifest(
            {
                "version": 1,
                "sources": [{"id": "session", "path": "session.mp4"}],
                "cuts": [{"id": "intro-look", "source": "session"}],
                "sections": [{"cut": "missing"}],
            }
        )
