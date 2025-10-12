# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2025-10-12

### Added
- Emit a `ResourceWarning` when processing very large (≈10 MiB+) texts and reuse a
  thread-local Janome tokenizer to reduce per-call overhead.

### Packaging
- Build and publish `x86_64-pc-windows-msvc` wheels alongside existing Linux and
  macOS artifacts in the release workflow.

### Documentation & CI
- Refreshed README benchmarks and compatibility guidance, tuned PR/CI
  workflows for documentation-only changes, and documented the release
  checklist stressing full diff reviews before publishing.

## [0.1.0] - 2025-10-10

- Initial release.
