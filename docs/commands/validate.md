# `validate`

## Purpose

Validate a manifest before planning or rendering.

The command auto-detects whether the file is a cut-list manifest or a timeline manifest and checks:

- manifest structure and version
- basic semantic rules such as cut and section references
- referenced source files exist

## Usage

```bash
video-edit validate manifest.json
```

## Output

On success, the command prints a short summary and exits with code `0`.

Example:

```text
Valid timeline manifest: manifest.json (sources=2, cuts=3, sections=3)
```

If validation fails, the command exits with a non-zero status and prints the error.

## Notes

- Validation does not render media
- Validation does not probe media duration
- Use this command before `assemble` or future planning workflows
