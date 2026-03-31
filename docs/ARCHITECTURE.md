# Architecture

`video-editing-cli` is designed as a reusable library with a CLI on top, aimed at fast-beating music video assembly workflows.

## Stack

1. FFmpeg and ffprobe do the actual media work.
2. `VideoEditingService` provides a stable Python API for applications.
3. CLI command modules translate terminal arguments into service calls.

## Why this adds value

The value of this project should come from the layer above FFmpeg:

- friendlier interfaces for Python applications
- reusable workflows and conventions
- validation and safer defaults
- documentation, examples, and tests that make integration easier
- human-readable JSON manifests for cut lists and timeline assembly
- tooling that makes rapid music-video iteration easier than working with raw FFmpeg commands alone

## Design rule

Prefer putting reusable behavior in the service layer first. The CLI should stay thin and call into library code rather than owning the real logic.
