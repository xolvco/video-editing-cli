"""Reusable FFmpeg-backed video editing helpers."""

from .operations import concat_videos, extract_audio, probe_media, trim_video
from .operations import assemble_from_manifest
from .service import FFmpegTools, VideoEditingService

__all__ = [
    "FFmpegTools",
    "VideoEditingService",
    "assemble_from_manifest",
    "concat_videos",
    "extract_audio",
    "probe_media",
    "trim_video",
]

__version__ = "0.1.0"
