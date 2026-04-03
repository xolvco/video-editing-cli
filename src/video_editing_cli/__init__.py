"""Compatibility wrapper for the unified videoedit backend."""

from ._videoedit_bootstrap import ensure_videoedit_on_path

ensure_videoedit_on_path()

from videoedit import *  # noqa: F401,F403
