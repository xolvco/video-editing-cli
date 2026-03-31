"""Command registry for the video-edit CLI."""

from . import assemble, concat, extract_audio, probe, trim

COMMAND_MODULES = [probe, trim, concat, extract_audio, assemble]

__all__ = ["COMMAND_MODULES"]
