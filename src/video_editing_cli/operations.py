from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .service import DEFAULT_SERVICE, ManifestValidationResult


def probe_media(input_path: Path) -> dict:
    return DEFAULT_SERVICE.probe_media(input_path)


def validate_manifest(manifest_path: Path) -> ManifestValidationResult:
    return DEFAULT_SERVICE.validate_manifest(manifest_path)


def plan_assembly(
    manifest_path: Path,
    output_path: Path,
    gap_seconds: float | None = None,
    audio_fade_seconds: float | None = None,
    overwrite: bool = True,
) -> object:
    return DEFAULT_SERVICE.summarize_assembly_plan(
        manifest_path=manifest_path,
        output_path=output_path,
        gap_seconds=gap_seconds,
        audio_fade_seconds=audio_fade_seconds,
        overwrite=overwrite,
    )


def trim_video(
    input_path: Path,
    output_path: Path,
    start: str | None = None,
    end: str | None = None,
    duration: str | None = None,
    reencode: bool = False,
    overwrite: bool = True,
) -> Path:
    return DEFAULT_SERVICE.trim_video(
        input_path=input_path,
        output_path=output_path,
        start=start,
        end=end,
        duration=duration,
        reencode=reencode,
        overwrite=overwrite,
    )


def concat_videos(
    input_paths: Iterable[Path],
    output_path: Path,
    reencode: bool = False,
    overwrite: bool = True,
) -> Path:
    return DEFAULT_SERVICE.concat_videos(
        input_paths=input_paths,
        output_path=output_path,
        reencode=reencode,
        overwrite=overwrite,
    )


def extract_audio(
    input_path: Path,
    output_path: Path,
    codec: str | None = None,
    overwrite: bool = True,
) -> Path:
    return DEFAULT_SERVICE.extract_audio(
        input_path=input_path,
        output_path=output_path,
        codec=codec,
        overwrite=overwrite,
    )


def assemble_from_manifest(
    manifest_path: Path,
    output_path: Path,
    gap_seconds: float | None = None,
    audio_fade_seconds: float | None = None,
    overwrite: bool = True,
) -> Path:
    return DEFAULT_SERVICE.assemble_from_manifest(
        manifest_path=manifest_path,
        output_path=output_path,
        gap_seconds=gap_seconds,
        audio_fade_seconds=audio_fade_seconds,
        overwrite=overwrite,
    )
