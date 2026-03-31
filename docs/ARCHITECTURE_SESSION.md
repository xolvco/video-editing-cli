# Architecture Session

This document captures the current architecture direction for `video-editing-cli` after the initial scaffold phase.

## Problem statement

The project is not trying to be a general-purpose NLE. It is trying to make fast-beating music video assembly easier to automate.

The main pain points it should solve are:

- cutting many short moments out of source footage
- expressing those cuts in human-readable data
- rearranging the resulting moments quickly
- normalizing mismatched inputs so they can be assembled together
- combining audio and video pieces in pipeline-friendly ways
- rendering timeline experiments without hand-writing FFmpeg commands
- exposing the workflow to other applications through a stable Python API
- preparing outputs for different publishing channels without rebuilding everything by hand

## Product thesis

FFmpeg is the engine. `video-editing-cli` should be the orchestration layer that turns music-video editorial intent into validated, reusable render plans.

It should also be designed as a production backend for a future UI. The UI should decide what the editor wants to do. This library should perform the hard work reliably and repeatably.

That means the project should center on:

- timeline data models
- cut-list and assembly manifests
- normalization and composition planning
- render planning
- predictable CLI automation
- repeatable workflows for experimentation
- preview-to-final production workflows

## Primary user workflow

The core workflow should be:

1. Inspect source footage and audio.
2. Define cuts from one or more source files.
3. Store those cuts in readable JSON.
4. Assemble a new timeline from those cuts.
5. Normalize clips or audio when needed for compatibility.
6. Add gaps, fades, markers, and optional overlays.
7. Render a fast preview when needed.
8. Render the final deliverable for the target channel.

## Core domain model

The project should standardize around these concepts.

### `SourceAsset`

Represents an input media file.

Fields:

- `id`
- `path`
- `media_type`
- `duration_seconds`
- `metadata`

### `Cut`

Represents a selected moment from a source asset.

Fields:

- `id`
- `source_asset_id`
- `start`
- `end` or `duration`
- `label`
- `tags`

### `TimelineSection`

Represents a positioned unit in an assembled output.

Fields:

- `cut_id` or inline source reference
- `title`
- `gap_after_seconds`
- `audio_fade_in_seconds`
- `audio_fade_out_seconds`
- `marker`
- `overlay`

### `TimelineManifest`

Represents the full editorial plan for one output.

Fields:

- `version`
- `sources`
- `cuts`
- `sections`
- `defaults`
- `output`

### `RenderPreset`

Represents a target publishing or canvas configuration.

Fields:

- `id`
- `width`
- `height`
- `fps`
- `audio_sample_rate`
- `audio_channels`
- `fit_strategy`
- `codec_profile`

### `RenderMode`

Represents whether the output is optimized for speed or quality.

Fields:

- `preview`
- `final`

## Architectural stance

The project should be library-first and data-first.

### Library-first

All important behavior should live in reusable Python services before it appears in the CLI.

### Data-first

The primary artifact should be a human-readable JSON manifest, not ad hoc command flags alone.

### Pipeline-first

Commands should compose into workflows instead of acting like isolated utilities.

## Recommended layers

### Layer 1: Media adapters

Responsibility:

- run `ffmpeg` and `ffprobe`
- normalize process execution
- parse low-level metadata

Examples:

- `ffmpeg.py`

### Layer 2: Domain models

Responsibility:

- define source assets, cuts, sections, manifests, and render plans
- validate data
- convert timecode formats

Examples:

- manifest models
- timecode parsing
- cut validation

### Layer 3: Planning services

Responsibility:

- build cut plans
- build timeline plans
- resolve render presets
- compute chapter markers
- compute transitions, gaps, fades, and overlays
- optionally nudge cuts for cue-aligned timing later

Examples:

- `CutService`
- `TimelinePlanner`
- `RenderPlanner`

### Layer 4: Rendering services

Responsibility:

- convert plans into FFmpeg command graphs
- support preview and final render modes
- optionally create prepared intermediate assets
- render output
- optionally dry-run and print plans

### Layer 5: CLI

Responsibility:

- parse arguments
- load manifest files
- call library services
- print results

The CLI should stay intentionally thin.

## Command strategy

The current commands are useful building blocks, but the product should move toward a clearer workflow-oriented command set.

### Keep as low-level utilities

- `probe`
- `trim`
- `extract-audio`

### Reframe or evolve

- `concat`
  It is useful, but not central to the product vision. It should remain a utility, not the main orchestration primitive.

- `assemble`
  This should become the central render command for timeline manifests.

### Add next

- `plan`
  Load a manifest and print the resolved timeline without rendering.

- `cuts validate`
  Validate a cut list or timeline manifest.

- `normalize`
  Prepare clips so different media can be assembled safely.

- `render`
  Build preview or final outputs from a resolved timeline and preset.

- `cuts render`
  Materialize cut files if a workflow needs explicit intermediates.

- `timeline render`
  Potential long-term rename of `assemble` if the manifest model grows.

## Manifest strategy

The project likely needs two related JSON forms.

### 1. Cut list manifest

Purpose:

- define reusable moments extracted from source footage

Example shape:

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
      "label": "Intro glance"
    }
  ]
}
```

### 2. Timeline manifest

Purpose:

- define how cuts are assembled into one output

Example shape:

```json
{
  "version": 1,
  "defaults": {
    "gap_after_seconds": 0.15,
    "audio_fade_in_seconds": 0.04,
    "audio_fade_out_seconds": 0.04
  },
  "sections": [
    {
      "cut": "intro-look",
      "title": "Intro"
    }
  ],
  "output": {
    "path": "output.mp4"
  }
}
```

## Key design decisions

### Decision 1

The main product artifact should be JSON manifests, not only imperative CLI flags.

Reason:

- easier for humans to read
- easier for apps to generate
- easier to diff in git
- easier to validate

### Decision 2

The system should prefer references to reusable cuts over duplicating inline source declarations everywhere.

Reason:

- supports experimentation
- reduces repeated timing edits
- creates cleaner timelines

### Decision 3

Rendering and planning should be separate modes.

Reason:

- users need to inspect timeline decisions before long renders
- other tools may want the resolved plan without rendering

### Decision 4

Overlays and beat-aware features should build on the manifest layer, not bypass it.

Reason:

- keeps the product coherent
- prevents feature sprawl

### Decision 8

Timing alignment should not be treated as music-only.

Reason:

- music beats, narration beats, sentence timing, emphasis points, and demo moments are all timing cues
- the same cut list may need to be tried against different timing tracks
- cue-aligned editing is a broader and more valuable capability than music-only beat matching

### Decision 5

The library should optimize for production reliability because it is expected to sit behind a user-facing UI.

Reason:

- UI features are only trustworthy if the backend behavior is predictable
- users should be able to describe hard edits without manually fixing every render
- packaging as a reusable artifact requires stable library boundaries

### Decision 6

The library should support both preview and final rendering workflows.

Reason:

- users need fast iteration while deciding on cuts and assembly
- final renders may require heavier normalization, quality, or downstream enhancement
- preview-to-final flow fits a UI-driven production workflow much better than single-pass rendering

### Decision 7

Publishing targets should begin as named presets.

Reason:

- presets are easier for users and future UI flows
- presets help keep pipeline behavior consistent
- explicit raw output settings can be added later as an advanced escape hatch

## Output contract

Recommended primary outputs:

- rendered video
- resolved plan JSON
- job/output manifest for the next pipeline step

Recommended optional outputs:

- prepared intermediate clips
- chapter or marker metadata
- preview renders

V1 should treat the primary outputs above as the default contract. Optional outputs can be enabled when a workflow or downstream pipeline step needs them, but they should not define the first public interface.

## Initial preset direction

The first preset strategy should prefer named outputs rather than fully raw technical settings.

Examples:

- `standard_16_9`
- `vertical_9_16`
- `custom_wide_20_9`

The custom wide preset is especially important because it reflects the intended visual language of the product rather than only standard platform formats.

## Scoped roadmap

### V1

V1 should focus on the production backbone for repetitive assembly work.

Goals:

- accept reviewed JSON manifests as the main public interface
- normalize clips enough that mismatched media can be assembled safely
- assemble whole clips and cut segments into a final sequence
- support repeated editorial structure like gaps, fades, and markers
- support preview and final render modes
- produce the v1 output contract:
  - rendered video
  - resolved plan JSON
  - job/output manifest
- support named render presets, including:
  - `standard_16_9`
  - `vertical_9_16`
  - `custom_wide_20_9`
  - cinema-wide presets

V1 is not trying to replace an editor. It is trying to make repetitive, structured assembly much faster and more reliable.

### V2

V2 should extend the backbone into more differentiated composition and timing capabilities.

Goals:

- large-scale clip recombination
- split-screen and multi-panel composition
- uneven panel sizing and sliced layouts
- richer audio combination workflows
- optional prepared intermediates for safer editing and reuse
- cue-aligned cut resolution

Cue alignment means:

- a user provides a proposed cut list and reassembly
- another tool provides a list of timing cues
- the library resolves or nudges cuts so the edit aligns more naturally with those cues

Timing cues can include:

- music beats
- narration beats
- sentence boundaries
- emphasis points in spoken script
- product demo moments

This should eventually let users try alternate edits against alternate music or narration tracks without rebuilding the whole sequence by hand.

## Risks

### Risk: too generic

If the project keeps adding generic FFmpeg helpers, it will lose focus.

Mitigation:

- prioritize music-video editorial workflows
- treat generic commands as utilities, not the product center

### Risk: too much rendering logic in CLI commands

Mitigation:

- move real behavior into planning and service layers

### Risk: manifest drift

Mitigation:

- version the manifest format
- add explicit validators
- add dry-run inspection output

## Recommended next milestone

The next architecture milestone should be:

1. Define versioned manifest schemas.
2. Add `plan` and `validate` commands.
3. Split inline assembly logic into explicit planning objects.
4. Add one workflow example that starts from source clips and ends with a rendered music-video timeline.
