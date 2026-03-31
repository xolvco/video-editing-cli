# `concat`

## Purpose

Build one linear output from multiple videos.

`concat` supports two usage styles:

- quick file-list mode for fast playlist-style outputs
- playlist JSON mode for refined per-clip timing and marker control

## Usage

```bash
video-edit concat output.mp4 clip1.mp4 clip2.mp4 clip3.mp4
```

Planned refined mode:

```bash
video-edit concat output.mp4 --playlist playlist.json
```

## Notes

- Requires at least two input files
- Stream copy is the default when compatible
- Use `--reencode` if the inputs do not concatenate cleanly
- In v1 planning, quick mode may grow support for:
  - optional black spacers between clips
  - optional clip-start markers derived from normalized filenames
  - simple global trim and audio fade defaults
- Playlist mode is intended to support:
  - source-relative per-clip `start` and `end`
  - per-clip markers
  - simple per-clip audio fade overrides
  - future interstitial and title controls
