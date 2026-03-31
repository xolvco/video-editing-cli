from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..operations import concat_playlist, concat_videos
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

    if resolved["playlist_items"] is not None:
        concat_playlist(
            items=resolved["playlist_items"],
            output_path=Path(str(resolved["output_path"])),
            spacer_seconds=float(resolved["spacer_seconds"]),
            audio_fade_seconds=float(resolved["audio_fade_seconds"]),
            overwrite=not args.no_overwrite,
        )
    else:
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
        "playlist_items": None,
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
    resolved_items: list[dict[str, object]] = []
    item_markers = False
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each playlist item must be an object")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Each playlist item must define a non-empty string 'path'")
        input_paths.append(path)
        resolved_item: dict[str, object] = {"path": path}
        if "marker" in item and item.get("marker") is not None:
            item_markers = True
            resolved_item["marker"] = str(item["marker"])
        if item.get("start") is not None:
            resolved_item["start"] = str(item["start"])
        if item.get("end") is not None:
            resolved_item["end"] = str(item["end"])
        if item.get("duration") is not None:
            resolved_item["duration"] = str(item["duration"])
        if item.get("audio_fade_in_seconds") is not None:
            resolved_item["audio_fade_in_seconds"] = float(item["audio_fade_in_seconds"])
        if item.get("audio_fade_out_seconds") is not None:
            resolved_item["audio_fade_out_seconds"] = float(item["audio_fade_out_seconds"])
        if item.get("spacer_seconds") is not None:
            resolved_item["spacer_seconds"] = float(item["spacer_seconds"])
        resolved_items.append(resolved_item)

    return {
        "input_paths": input_paths,
        "playlist_items": resolved_items,
        "output_path": str(output_payload.get("path") or cli_output),
        "start": None,
        "end": None,
        "spacer_seconds": float(defaults.get("spacer_seconds", 0.0)),
        "audio_fade_seconds": float(defaults.get("audio_fade_in_seconds", 0.0)),
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
