# Manifests

`video-editing-cli` uses versioned JSON manifests as its main data interface.

## Why manifests

They are:

- readable by humans
- easy to generate from other tools
- easy to diff in git
- easier to validate than ad hoc command strings

## Manifest types

Version `1` currently defines two manifest shapes:

- cut list manifests
- timeline manifests

## Cut list manifest v1

Use this to define reusable moments cut from source footage.

```json
{
  "version": 1,
  "sources": [
    { "id": "session", "path": "session.mp4" }
  ],
  "cuts": [
    {
      "id": "intro-look",
      "source": "session",
      "start": "00:00:05.000",
      "end": "00:00:06.200",
      "label": "Intro glance",
      "tags": ["closeup", "beat"]
    }
  ]
}
```

## Timeline manifest v1

Use this to assemble a final output from reusable cuts.

```json
{
  "version": 1,
  "sources": [
    { "id": "session", "path": "session.mp4" },
    { "id": "closing", "path": "closing.mp4" }
  ],
  "cuts": [
    {
      "id": "intro-look",
      "source": "session",
      "start": "00:00:05.000",
      "end": "00:00:06.200"
    },
    {
      "id": "main-hit",
      "source": "session",
      "start": "00:03:10",
      "duration": "00:00:18.000"
    },
    {
      "id": "closing-shot",
      "source": "closing"
    }
  ],
  "defaults": {
    "gap_after_seconds": 2.0,
    "audio_fade_in_seconds": 0.5,
    "audio_fade_out_seconds": 0.5
  },
  "sections": [
    { "cut": "intro-look", "title": "Intro" },
    { "cut": "main-hit", "title": "Main Segment" },
    { "cut": "closing-shot", "title": "Closing" }
  ],
  "output": {
    "path": "output.mp4"
  }
}
```

## Notes

- `version` is required and currently must be `1`
- time values may be numeric seconds or `HH:MM:SS(.sss)` strings
- cuts should use either `end` or `duration`, not both
- timeline sections reference cuts by id
