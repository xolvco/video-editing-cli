# CLI Usage

This page is the general usage guide for `video-edit`.

The current workflow is centered on preparing and assembling footage for fast-beating music videos using readable cut lists and timeline manifests.

## Install for local development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

For Git Bash or WSL2:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Basic command pattern

```bash
video-edit <command> [arguments] [options]
```

Portable alternative:

```bash
python -m video_editing_cli <command> [arguments] [options]
```

## Included commands

- `probe`: print media metadata as JSON
- `trim`: create a clip from a source file
- `concat`: join multiple clips into one output
- `extract-audio`: write an audio-only output from a media file
- `assemble`: render a manifest-driven timeline with gaps, fades, and chapter markers

## Examples

### Inspect a file

```bash
video-edit probe input.mp4
```

### Trim a clip

```bash
video-edit trim input.mp4 clip.mp4 --start 00:00:05 --duration 15
```

### Concatenate clips

```bash
video-edit concat merged.mp4 intro.mp4 main.mp4 outro.mp4
```

### Extract audio

```bash
video-edit extract-audio input.mp4 audio.wav
```

### Assemble a timeline from a manifest

```bash
video-edit assemble examples/manifests/playlist.json output.mp4
```

The manifest can describe cuts from longer source files with versioned `sources`, `cuts`, and `sections`.
For the versioned manifest schema, see `docs/MANIFESTS.md`.

## Command reference

Detailed command pages live in `docs/commands/`.

- `docs/commands/probe.md`
- `docs/commands/trim.md`
- `docs/commands/concat.md`
- `docs/commands/extract_audio.md`
