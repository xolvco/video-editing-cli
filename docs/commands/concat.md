# `concat`

## Purpose

Join multiple video files into one output file.

## Usage

```bash
video-edit concat output.mp4 clip1.mp4 clip2.mp4 clip3.mp4
```

## Notes

- Requires at least two input files
- Stream copy is the default when compatible
- Use `--reencode` if the inputs do not concatenate cleanly
