# video-editing-cli

`video-editing-cli` is now a deprecated compatibility wrapper around `videoedit`.

Use `videoedit` for all new work:

- repo: `https://github.com/xolvco/videoedit`
- package: `videoedit`
- primary CLI: `video-edit`

## What this repo is now

This repo exists to keep older imports and scripts working during the migration.
It is no longer the canonical implementation.

Current role:

- re-export the old `video_editing_cli` Python surface from `videoedit`
- preserve compatibility for the old module and CLI entrypoints
- run smoke tests only, not the full behavioral suite

## What to use instead

Old import:

```python
from video_editing_cli import VideoEditingService
```

Preferred import:

```python
from videoedit import VideoEditingService
```

Shell usage stays the same:

```bash
video-edit probe input.mp4
```

For canonical docs, tests, and examples, use the `videoedit` repo.

## Compatibility policy

- compatibility is still maintained for now
- new behavior should land in `videoedit`, not here
- docs and tests in this repo should stay minimal and wrapper-focused

## License

MIT. See [LICENSE](LICENSE).
