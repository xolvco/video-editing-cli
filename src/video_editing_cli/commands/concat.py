from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..operations import concat_videos

COMMAND_NAME = "concat"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(COMMAND_NAME, help="Concatenate multiple video files")
    parser.add_argument("output", type=str)
    parser.add_argument("inputs", nargs="*", type=str)
    parser.add_argument("--input-dir", type=str)
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
    input_paths = _resolve_input_paths(args.inputs, args.input_dir)
    if args.json_preview:
        payload = _build_json_preview_payload(
            input_paths=input_paths,
            output=args.output,
            start=args.start,
            end=args.end,
            spacer_seconds=args.spacer_seconds,
            audio_fade_seconds=args.audio_fade_seconds,
            markers=args.markers,
            full=args.full_preview,
        )
        print(json.dumps(payload, indent=2))
        return 0

    concat_videos(
        input_paths=input_paths,
        output_path=args.output,
        start=args.start,
        end=args.end,
        spacer_seconds=args.spacer_seconds,
        audio_fade_seconds=args.audio_fade_seconds,
        markers=args.markers,
        reencode=args.reencode,
        overwrite=not args.no_overwrite,
    )
    print(args.output)
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
