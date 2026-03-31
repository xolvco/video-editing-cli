# `trim`

## Purpose

Create a clipped section of a video file.

## Usage

```bash
video-edit trim input.mp4 output.mp4 --start 00:00:03 --duration 12
```

## Options

- `--start`: seek position before reading
- `--end`: stop time in the input timeline
- `--duration`: output duration
- `--reencode`: re-encode instead of stream copy
- `--no-overwrite`: fail if the output file already exists
