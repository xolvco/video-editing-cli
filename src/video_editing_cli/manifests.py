from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .assembly import parse_timecode


@dataclass(frozen=True)
class SourceAsset:
    id: str
    path: Path


@dataclass(frozen=True)
class CutDefinition:
    id: str
    source: str
    start_seconds: float = 0.0
    end_seconds: float | None = None
    duration_seconds: float | None = None
    label: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class TimelineDefaults:
    gap_after_seconds: float = 0.0
    audio_fade_in_seconds: float = 0.0
    audio_fade_out_seconds: float = 0.0


@dataclass(frozen=True)
class TimelineSectionDefinition:
    cut: str
    title: str | None = None
    gap_after_seconds: float | None = None
    audio_fade_in_seconds: float | None = None
    audio_fade_out_seconds: float | None = None


@dataclass(frozen=True)
class OutputDefinition:
    path: Path | None = None


@dataclass(frozen=True)
class ConcatDefaults:
    spacer_mode: str = "black"
    spacer_seconds: float = 0.0
    audio_fade_in_seconds: float = 0.0
    audio_fade_out_seconds: float = 0.0


@dataclass(frozen=True)
class ConcatItemDefinition:
    path: Path
    start: str | None = None
    end: str | None = None
    duration: str | None = None
    marker: str | None = None
    audio_fade_in_seconds: float | None = None
    audio_fade_out_seconds: float | None = None
    spacer_seconds: float | None = None


@dataclass(frozen=True)
class CutListManifest:
    version: int
    sources: dict[str, SourceAsset]
    cuts: dict[str, CutDefinition]


@dataclass(frozen=True)
class TimelineManifest:
    version: int
    sources: dict[str, SourceAsset]
    cuts: dict[str, CutDefinition]
    sections: list[TimelineSectionDefinition]
    defaults: TimelineDefaults = field(default_factory=TimelineDefaults)
    output: OutputDefinition = field(default_factory=OutputDefinition)


@dataclass(frozen=True)
class ConcatPlaylistManifest:
    version: int
    items: list[ConcatItemDefinition]
    defaults: ConcatDefaults = field(default_factory=ConcatDefaults)
    output: OutputDefinition = field(default_factory=OutputDefinition)


def load_json_document(path: Path | str) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    with resolved.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be a JSON object")
    return payload


def _require_version(payload: dict[str, Any]) -> int:
    version = payload.get("version")
    if version != 1:
        raise ValueError("Manifest must declare version 1")
    return 1


def _require_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Manifest must contain a non-empty '{key}' list")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"Every item in '{key}' must be an object")
        result.append(item)
    return result


def _parse_sources(payload: dict[str, Any]) -> dict[str, SourceAsset]:
    sources: dict[str, SourceAsset] = {}
    for item in _require_list(payload, "sources"):
        source_id = item.get("id")
        source_path = item.get("path")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("Each source must define a non-empty string 'id'")
        if not isinstance(source_path, str) or not source_path.strip():
            raise ValueError("Each source must define a non-empty string 'path'")
        if source_id in sources:
            raise ValueError(f"Duplicate source id: {source_id}")
        sources[source_id] = SourceAsset(id=source_id, path=Path(source_path))
    return sources


def _parse_cuts(payload: dict[str, Any], sources: dict[str, SourceAsset]) -> dict[str, CutDefinition]:
    cuts: dict[str, CutDefinition] = {}
    for item in _require_list(payload, "cuts"):
        cut_id = item.get("id")
        source = item.get("source")
        if not isinstance(cut_id, str) or not cut_id.strip():
            raise ValueError("Each cut must define a non-empty string 'id'")
        if not isinstance(source, str) or source not in sources:
            raise ValueError(f"Cut '{cut_id}' references unknown source '{source}'")
        if cut_id in cuts:
            raise ValueError(f"Duplicate cut id: {cut_id}")

        start_seconds = parse_timecode(item.get("start")) or 0.0
        end_seconds = parse_timecode(item.get("end"))
        duration_seconds = parse_timecode(item.get("duration"))
        if end_seconds is not None and duration_seconds is not None:
            raise ValueError(f"Cut '{cut_id}' cannot define both 'end' and 'duration'")

        label = item.get("label")
        if label is not None and not isinstance(label, str):
            raise ValueError(f"Cut '{cut_id}' has a non-string 'label'")

        raw_tags = item.get("tags", [])
        if not isinstance(raw_tags, list) or not all(isinstance(tag, str) for tag in raw_tags):
            raise ValueError(f"Cut '{cut_id}' has invalid 'tags'")

        cuts[cut_id] = CutDefinition(
            id=cut_id,
            source=source,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            duration_seconds=duration_seconds,
            label=label,
            tags=tuple(raw_tags),
        )
    return cuts


def parse_cut_list_manifest(payload: dict[str, Any]) -> CutListManifest:
    version = _require_version(payload)
    sources = _parse_sources(payload)
    cuts = _parse_cuts(payload, sources)
    return CutListManifest(version=version, sources=sources, cuts=cuts)


def parse_timeline_manifest(payload: dict[str, Any]) -> TimelineManifest:
    version = _require_version(payload)
    sources = _parse_sources(payload)
    cuts = _parse_cuts(payload, sources)

    defaults_payload = payload.get("defaults", {})
    if not isinstance(defaults_payload, dict):
        raise ValueError("'defaults' must be an object when provided")
    defaults = TimelineDefaults(
        gap_after_seconds=float(defaults_payload.get("gap_after_seconds", 0.0)),
        audio_fade_in_seconds=float(defaults_payload.get("audio_fade_in_seconds", 0.0)),
        audio_fade_out_seconds=float(defaults_payload.get("audio_fade_out_seconds", 0.0)),
    )

    sections_payload = _require_list(payload, "sections")
    sections: list[TimelineSectionDefinition] = []
    for item in sections_payload:
        cut_id = item.get("cut")
        if not isinstance(cut_id, str) or cut_id not in cuts:
            raise ValueError(f"Timeline section references unknown cut '{cut_id}'")
        title = item.get("title")
        if title is not None and not isinstance(title, str):
            raise ValueError(f"Timeline section '{cut_id}' has a non-string 'title'")
        sections.append(
            TimelineSectionDefinition(
                cut=cut_id,
                title=title,
                gap_after_seconds=(
                    float(item["gap_after_seconds"]) if "gap_after_seconds" in item else None
                ),
                audio_fade_in_seconds=(
                    float(item["audio_fade_in_seconds"]) if "audio_fade_in_seconds" in item else None
                ),
                audio_fade_out_seconds=(
                    float(item["audio_fade_out_seconds"]) if "audio_fade_out_seconds" in item else None
                ),
            )
        )

    output_payload = payload.get("output", {})
    if not isinstance(output_payload, dict):
        raise ValueError("'output' must be an object when provided")
    output_path = output_payload.get("path")
    output = OutputDefinition(path=Path(output_path) if isinstance(output_path, str) else None)

    return TimelineManifest(
        version=version,
        sources=sources,
        cuts=cuts,
        sections=sections,
        defaults=defaults,
        output=output,
    )


def parse_concat_playlist_manifest(payload: dict[str, Any]) -> ConcatPlaylistManifest:
    version = _require_version(payload)

    defaults_payload = payload.get("defaults", {})
    if not isinstance(defaults_payload, dict):
        raise ValueError("'defaults' must be an object when provided")
    spacer_mode = defaults_payload.get("spacer_mode", "black")
    if not isinstance(spacer_mode, str) or not spacer_mode.strip():
        raise ValueError("'defaults.spacer_mode' must be a non-empty string when provided")
    defaults = ConcatDefaults(
        spacer_mode=spacer_mode,
        spacer_seconds=float(defaults_payload.get("spacer_seconds", 0.0)),
        audio_fade_in_seconds=float(defaults_payload.get("audio_fade_in_seconds", 0.0)),
        audio_fade_out_seconds=float(defaults_payload.get("audio_fade_out_seconds", 0.0)),
    )

    items_payload = _require_list(payload, "items")
    items: list[ConcatItemDefinition] = []
    for item in items_payload:
        item_path = item.get("path")
        if not isinstance(item_path, str) or not item_path.strip():
            raise ValueError("Each concat playlist item must define a non-empty string 'path'")
        start = item.get("start")
        end = item.get("end")
        duration = item.get("duration")
        if start is not None:
            parse_timecode(start)
        if end is not None:
            parse_timecode(end)
        if duration is not None:
            parse_timecode(duration)
        if end is not None and duration is not None:
            raise ValueError("Concat playlist item cannot define both 'end' and 'duration'")

        marker = item.get("marker")
        if marker is not None and not isinstance(marker, str):
            raise ValueError("Concat playlist item 'marker' must be a string when provided")

        items.append(
            ConcatItemDefinition(
                path=Path(item_path),
                start=str(start) if start is not None else None,
                end=str(end) if end is not None else None,
                duration=str(duration) if duration is not None else None,
                marker=marker,
                audio_fade_in_seconds=(
                    float(item["audio_fade_in_seconds"]) if "audio_fade_in_seconds" in item else None
                ),
                audio_fade_out_seconds=(
                    float(item["audio_fade_out_seconds"]) if "audio_fade_out_seconds" in item else None
                ),
                spacer_seconds=float(item["spacer_seconds"]) if "spacer_seconds" in item else None,
            )
        )

    output_payload = payload.get("output", {})
    if not isinstance(output_payload, dict):
        raise ValueError("'output' must be an object when provided")
    output_path = output_payload.get("path")
    output = OutputDefinition(path=Path(output_path) if isinstance(output_path, str) else None)

    return ConcatPlaylistManifest(
        version=version,
        items=items,
        defaults=defaults,
        output=output,
    )
