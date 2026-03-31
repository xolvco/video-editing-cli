from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .assembly import (
    AssemblyManifest,
    AssemblyPlan,
    TimelineSection,
    build_filter_complex,
    normalize_title,
    parse_duration_from_probe,
    resolve_section_duration,
    write_metadata_file,
)
from .ffmpeg import run_ffmpeg, run_ffprobe, validate_existing_file
from .manifests import load_json_document, parse_cut_list_manifest, parse_timeline_manifest


@dataclass(frozen=True)
class FFmpegTools:
    ffmpeg: str = "ffmpeg"
    ffprobe: str = "ffprobe"


@dataclass(frozen=True)
class ManifestValidationResult:
    manifest_type: str
    manifest_path: Path
    source_count: int
    cut_count: int
    section_count: int | None = None


class VideoEditingService:
    """Reusable high-level interface for FFmpeg-backed workflows."""

    def __init__(self, tools: FFmpegTools | None = None) -> None:
        self.tools = tools or FFmpegTools()

    def validate_manifest(self, manifest_path: Path | str) -> ManifestValidationResult:
        resolved_manifest_path = Path(manifest_path).expanduser().resolve()
        payload = load_json_document(resolved_manifest_path)

        if "sections" in payload:
            manifest = parse_timeline_manifest(payload)
            manifest_type = "timeline"
            section_count = len(manifest.sections)
        elif "cuts" in payload and "sources" in payload:
            manifest = parse_cut_list_manifest(payload)
            manifest_type = "cut-list"
            section_count = None
        else:
            raise ValueError("Could not determine manifest type. Expected a cut-list or timeline manifest.")

        base_dir = resolved_manifest_path.parent
        for source in manifest.sources.values():
            source_path = source.path if source.path.is_absolute() else base_dir / source.path
            validate_existing_file(source_path)

        return ManifestValidationResult(
            manifest_type=manifest_type,
            manifest_path=resolved_manifest_path,
            source_count=len(manifest.sources),
            cut_count=len(manifest.cuts),
            section_count=section_count,
        )

    def probe_media(self, input_path: Path | str) -> dict:
        source = validate_existing_file(Path(input_path))
        result = run_ffprobe(
            [
                self.tools.ffprobe,
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(source),
            ]
        )
        return json.loads(result.stdout)

    def trim_video(
        self,
        input_path: Path | str,
        output_path: Path | str,
        start: str | None = None,
        end: str | None = None,
        duration: str | None = None,
        reencode: bool = False,
        overwrite: bool = True,
    ) -> Path:
        source = validate_existing_file(Path(input_path))
        target = Path(output_path).expanduser().resolve()

        args = [self.tools.ffmpeg, "-hide_banner"]
        args.append("-y" if overwrite else "-n")
        if start:
            args.extend(["-ss", start])
        args.extend(["-i", str(source)])
        if end:
            args.extend(["-to", end])
        if duration:
            args.extend(["-t", duration])
        if reencode:
            args.extend(["-c:v", "libx264", "-c:a", "aac"])
        else:
            args.extend(["-c", "copy"])
        args.append(str(target))

        run_ffmpeg(args)
        return target

    def concat_videos(
        self,
        input_paths: Iterable[Path | str],
        output_path: Path | str,
        reencode: bool = False,
        overwrite: bool = True,
    ) -> Path:
        sources = [validate_existing_file(Path(path)) for path in input_paths]
        if len(sources) < 2:
            raise ValueError("concat requires at least two input files")

        target = Path(output_path).expanduser().resolve()
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            for source in sources:
                normalized = source.as_posix().replace("'", "'\\''")
                handle.write(f"file '{normalized}'\n")
            list_path = Path(handle.name)

        try:
            args = [
                self.tools.ffmpeg,
                "-hide_banner",
                "-y" if overwrite else "-n",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
            ]
            if reencode:
                args.extend(["-c:v", "libx264", "-c:a", "aac"])
            else:
                args.extend(["-c", "copy"])
            args.append(str(target))
            run_ffmpeg(args)
            return target
        finally:
            list_path.unlink(missing_ok=True)

    def extract_audio(
        self,
        input_path: Path | str,
        output_path: Path | str,
        codec: str | None = None,
        overwrite: bool = True,
    ) -> Path:
        source = validate_existing_file(Path(input_path))
        target = Path(output_path).expanduser().resolve()

        args = [
            self.tools.ffmpeg,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source),
            "-vn",
        ]
        if codec:
            args.extend(["-c:a", codec])
        args.append(str(target))

        run_ffmpeg(args)
        return target

    def build_assembly_manifest(
        self,
        manifest_path: Path | str,
        gap_seconds: float | None = None,
        audio_fade_seconds: float | None = None,
    ) -> AssemblyManifest:
        payload = load_json_document(manifest_path)
        timeline_manifest = parse_timeline_manifest(payload)
        sections: list[TimelineSection] = []
        for item in timeline_manifest.sections:
            cut = timeline_manifest.cuts[item.cut]
            source_asset = timeline_manifest.sources[cut.source]
            input_path = validate_existing_file(source_asset.path)
            title = normalize_title(item.title or cut.label, input_path)
            source_duration_seconds = parse_duration_from_probe(self.probe_media(input_path))
            duration_seconds = resolve_section_duration(
                source_duration_seconds=source_duration_seconds,
                start_seconds=cut.start_seconds,
                end_value=cut.end_seconds,
                duration_value=cut.duration_seconds,
            )
            resolved_gap = timeline_manifest.defaults.gap_after_seconds
            if item.gap_after_seconds is not None:
                resolved_gap = item.gap_after_seconds
            resolved_fade_in = timeline_manifest.defaults.audio_fade_in_seconds
            if item.audio_fade_in_seconds is not None:
                resolved_fade_in = item.audio_fade_in_seconds
            resolved_fade_out = timeline_manifest.defaults.audio_fade_out_seconds
            if item.audio_fade_out_seconds is not None:
                resolved_fade_out = item.audio_fade_out_seconds
            sections.append(
                TimelineSection(
                    input_path=input_path,
                    title=title,
                    duration_seconds=duration_seconds,
                    start_seconds=cut.start_seconds,
                    gap_after_seconds=resolved_gap,
                    audio_fade_in_seconds=resolved_fade_in,
                    audio_fade_out_seconds=resolved_fade_out,
                )
            )
        if gap_seconds is not None or audio_fade_seconds is not None:
            override_gap = gap_seconds if gap_seconds is not None else None
            override_fade = audio_fade_seconds if audio_fade_seconds is not None else None
            sections = [
                TimelineSection(
                    input_path=section.input_path,
                    title=section.title,
                    duration_seconds=section.duration_seconds,
                    start_seconds=section.start_seconds,
                    gap_after_seconds=section.gap_after_seconds if override_gap is None else override_gap,
                    audio_fade_in_seconds=(
                        section.audio_fade_in_seconds if override_fade is None else override_fade
                    ),
                    audio_fade_out_seconds=(
                        section.audio_fade_out_seconds if override_fade is None else override_fade
                    ),
                )
                for section in sections
            ]
        return AssemblyManifest(sections=sections)

    def build_assembly_plan(
        self,
        manifest_path: Path | str,
        output_path: Path | str,
        gap_seconds: float | None = None,
        audio_fade_seconds: float | None = None,
        overwrite: bool = True,
        ) -> AssemblyPlan:
        manifest = self.build_assembly_manifest(
            manifest_path=manifest_path,
            gap_seconds=gap_seconds,
            audio_fade_seconds=audio_fade_seconds,
        )
        target = Path(output_path).expanduser().resolve()
        metadata_path = write_metadata_file(manifest.sections)
        ffmpeg_args = [self.tools.ffmpeg, "-hide_banner", "-y" if overwrite else "-n"]

        for section in manifest.sections:
            ffmpeg_args.extend(["-i", str(section.input_path)])

        ffmpeg_args.extend(["-i", str(metadata_path)])
        ffmpeg_args.extend(
            [
                "-filter_complex",
                build_filter_complex(manifest.sections),
                "-map",
                "[outv]",
                "-map",
                "[outa]",
                "-map_metadata",
                str(len(manifest.sections)),
                "-movflags",
                "use_metadata_tags",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                str(target),
            ]
        )
        return AssemblyPlan(ffmpeg_args=ffmpeg_args, metadata_path=metadata_path)

    def assemble_from_manifest(
        self,
        manifest_path: Path | str,
        output_path: Path | str,
        gap_seconds: float | None = None,
        audio_fade_seconds: float | None = None,
        overwrite: bool = True,
    ) -> Path:
        plan = self.build_assembly_plan(
            manifest_path=manifest_path,
            output_path=output_path,
            gap_seconds=gap_seconds,
            audio_fade_seconds=audio_fade_seconds,
            overwrite=overwrite,
        )
        try:
            run_ffmpeg(plan.ffmpeg_args)
            return Path(output_path).expanduser().resolve()
        finally:
            plan.metadata_path.unlink(missing_ok=True)


DEFAULT_SERVICE = VideoEditingService()
