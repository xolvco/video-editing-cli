from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..operations import concat_videos
from ..manifests import load_json_document

COMMAND_NAME = "concat"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(COMMAND_NAME, help="Concatenate multiple video files")
    parser.add_argument("output", type=str)
    parser.add_argument("inputs", nargs="*", type=str)
    parser.add_argument("--input-dir", type=str)
    parser.add_argument("--playlist", type=str)
    parser.add_argument("--start", type=str)
    parser.add_argument("--end", type=str)
    parser.add_argument("--spacer-seconds", type=float, default=0.0)
    parser.add_argument("--audio-fade-seconds", type=float, default=0.0)
    parser.add_argument("--markers", action="store_true")
    parser.add_argument("--json-preview", action="store_true")
    parser.add_argument("--full-preview", action="store_true")
    parser.add_argument("--reencode", action="store_true")
    parser.add_argument("--no-overwrite", action="store_true")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    resolved = _resolve_concat_inputs(
        inputs=args.inputs,
        input_dir=args.input_dir,
        playlist=args.playlist,
        output=args.output,
        start=args.start,
        end=args.end,
        spacer_seconds=args.spacer_seconds,
        audio_fade_seconds=args.audio_fade_seconds,
        markers=args.markers,
    )
    if args.json_preview:
        print(json.dumps(resolved["preview_payload"], indent=2))
        return 0

    concat_videos(
        input_paths=resolved["input_paths"],
        output_path=resolved["output_path"],
        start=resolved["start"],
        end=resolved["end"],
        spacer_seconds=resolved["spacer_seconds"],
        audio_fade_seconds=resolved["audio_fade_seconds"],
        markers=resolved["markers"],
        reencode=args.reencode,
        overwrite=not args.no_overwrite,
    )
    print(resolved["output_path"])
    return 0


def _resolve_input_paths(inputs: list[str], input_dir: str | None) -> list[str]:
    if inputs and input_dir:
        raise ValueError("Use either explicit input files or --input-dir, not both.")
    if input_dir:
        directory = Path(input_dir).expanduser().resolve()
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        discovered = sorted(
            [
                str(path)
                for path in directory.iterdir()
                if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".mkv", ".avi", ".m4v"}
            ],
            key=lambda value: Path(value).name.lower(),
        )
        if len(discovered) < 2:
            raise ValueError("input directory must contain at least two supported video files")
        return discovered
    if len(inputs) < 2:
        raise ValueError("concat requires at least two input files")
    return inputs


def _resolve_concat_inputs(
    inputs: list[str],
    input_dir: str | None,
    playlist: str | None,
    output: str,
    start: str | None,
    end: str | None,
    spacer_seconds: float,
    audio_fade_seconds: float,
    markers: bool,
) -> dict[str, object]:
    selected_sources = sum(bool(value) for value in [bool(inputs), bool(input_dir), bool(playlist)])
    if selected_sources != 1:
        raise ValueError("Use exactly one input source: explicit files, --input-dir, or --playlist.")

    if playlist:
        return _resolve_playlist_inputs(Path(playlist), output)

    input_paths = _resolve_input_paths(inputs, input_dir)
    return {
        "input_paths": input_paths,
        "output_path": output,
        "start": start,
        "end": end,
        "spacer_seconds": spacer_seconds,
        "audio_fade_seconds": audio_fade_seconds,
        "markers": markers,
        "preview_payload": _build_json_preview_payload(
            input_paths=input_paths,
            output=output,
            start=start,
            end=end,
            spacer_seconds=spacer_seconds,
            audio_fade_seconds=audio_fade_seconds,
            markers=markers,
            full=False,
        ),
    }


def _resolve_playlist_inputs(playlist_path: Path, cli_output: str) -> dict[str, object]:
    payload = load_json_document(playlist_path)
    if payload.get("version") != 1:
        raise ValueError("Concat playlist manifest must declare version 1")

    items = payload.get("items")
    if not isinstance(items, list) or len(items) < 2:
        raise ValueError("Concat playlist manifest must contain at least two items")

    defaults = payload.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("'defaults' must be an object when provided")
    output_payload = payload.get("output", {})
    if not isinstance(output_payload, dict):
        raise ValueError("'output' must be an object when provided")

    input_paths: list[str] = []
    item_start: str | None = None
    item_end: str | None = None
    item_markers = False
    item_audio_fade_seconds = float(defaults.get("audio_fade_in_seconds", 0.0))
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each playlist item must be an object")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Each playlist item must define a non-empty string 'path'")
        input_paths.append(path)
        if "marker" in item and item.get("marker") is not None:
            item_markers = True
        if "start" in item and item.get("start") is not None:
            candidate = str(item["start"])
            if item_start is None:
                item_start = candidate
            elif item_start != candidate:
                raise ValueError("Playlist v1 currently requires one shared 'start' value across items")
        if "end" in item and item.get("end") is not None:
            candidate = str(item["end"])
            if item_end is None:
                item_end = candidate
            elif item_end != candidate:
                raise ValueError("Playlist v1 currently requires one shared 'end' value across items")
        fade_in = item.get("audio_fade_in_seconds")
        fade_out = item.get("audio_fade_out_seconds")
        if fade_in is not None or fade_out is not None:
            candidate = float(fade_in if fade_in is not None else fade_out)
            if item_audio_fade_seconds == float(defaults.get("audio_fade_in_seconds", 0.0)):
                item_audio_fade_seconds = candidate
            elif item_audio_fade_seconds != candidate:
                raise ValueError(
                    "Playlist v1 currently requires one shared audio fade value across items"
                )

    return {
        "input_paths": input_paths,
        "output_path": str(output_payload.get("path") or cli_output),
        "start": item_start,
        "end": item_end,
        "spacer_seconds": float(defaults.get("spacer_seconds", 0.0)),
        "audio_fade_seconds": item_audio_fade_seconds,
        "markers": item_markers,
        "preview_payload": payload,
    }


def _build_json_preview_payload(
    input_paths: list[str],
    output: str,
    start: str | None,
    end: str | None,
    spacer_seconds: float,
    audio_fade_seconds: float,
    markers: bool,
    full: bool,
) -> dict:
    items = []
    for input_path in input_paths:
        path = Path(input_path)
        item: dict[str, object] = {
            "path": str(path),
        }
        if full or start is not None:
            item["start"] = start
        if full or end is not None:
            item["end"] = end
        if markers:
            item["marker"] = _normalize_marker_text(path.stem)
        elif full:
            item["marker"] = None
        if full:
            item["audio_fade_in_seconds"] = audio_fade_seconds
            item["audio_fade_out_seconds"] = audio_fade_seconds
        items.append(item)

    payload = {
        "version": 1,
        "items": items,
        "output": {"path": output},
    }
    if full:
        payload["defaults"] = {
            "spacer_mode": "black",
            "spacer_seconds": spacer_seconds,
            "audio_fade_in_seconds": audio_fade_seconds,
            "audio_fade_out_seconds": audio_fade_seconds,
        }
    return payload


def _normalize_marker_text(raw_text: str) -> str:
    collapsed = raw_text.replace("_", " ").replace("-", " ")
    return " ".join(collapsed.split())
