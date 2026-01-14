# Release Notes - v2.2.1 (2026-01-14)

## Highlights
- Transfer tuning flags across cp/mv/sync
- Resumable ranged downloads with robust retry/backoff
- Safer ranged reads preventing truncation
- Updated documentation and examples

## New Features
- `--part-size`: Control per-part size for multipart uploads and ranged downloads (e.g., `8MB`, `64MB`).
- `--max-retries`, `--retry-backoff`, `--retry-backoff-max`: Exponential backoff retry for each part/range.
- `--resume/--no-resume`: Resume interrupted ranged downloads (enabled by default).
- `mv` (local→COS) uses multipart with streaming progress when progress is enabled.

## Improvements
- Ranged downloads now fully consume response bodies per range and advance offsets by actual bytes read to avoid truncation.
- `cp` checks object existence/size via HEAD → ListObjects → 0–0 range fallback and warns when missing.
- `sync` keeps legacy behavior under `--no-progress`; advanced streaming is used only when progress is enabled.

## Documentation
- Added a Transfer Tuning section with a cheat sheet table in README.
- Examples added for cp/mv/sync showing tuning flags and resume.

## Compatibility
- No breaking changes. Existing scripts using `--no-progress` continue to use SDK upload/download paths.

## Acknowledgements
Thanks to contributors and users who reported issues and suggested enhancements.
