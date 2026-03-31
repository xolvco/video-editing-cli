from __future__ import annotations

import argparse

from ..operations import concat_videos

COMMAND_NAME = "concat"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(COMMAND_NAME, help="Concatenate multiple video files")
    parser.add_argument("output", type=str)
    parser.add_argument("inputs", nargs="+", type=str)
    parser.add_argument("--reencode", action="store_true")
    parser.add_argument("--no-overwrite", action="store_true")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    concat_videos(
        input_paths=args.inputs,
        output_path=args.output,
        reencode=args.reencode,
        overwrite=not args.no_overwrite,
    )
    print(args.output)
    return 0
