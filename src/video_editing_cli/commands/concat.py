from __future__ import annotations

import argparse

from ..operations import concat_videos

COMMAND_NAME = "concat"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(COMMAND_NAME, help="Concatenate multiple video files")
    parser.add_argument("output", type=str)
    parser.add_argument("inputs", nargs="+", type=str)
    parser.add_argument("--start", type=str)
    parser.add_argument("--end", type=str)
    parser.add_argument("--spacer-seconds", type=float, default=0.0)
    parser.add_argument("--audio-fade-seconds", type=float, default=0.0)
    parser.add_argument("--markers", action="store_true")
    parser.add_argument("--reencode", action="store_true")
    parser.add_argument("--no-overwrite", action="store_true")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    concat_videos(
        input_paths=args.inputs,
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
