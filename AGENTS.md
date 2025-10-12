# FastBunkai Agent Handbook

## Overview
FastBunkai is a Rust + Python hybrid implementation of the bunkai sentence boundary disambiguation pipeline. It mirrors the `bunkai.Bunkai` public API, so `from fast_bunkai import FastBunkai as Bunkai` works as a drop-in replacement. The Rust core (PyO3 with abi3 bindings) performs the heavy segmentation work while the Python layer keeps compatibility annotations aligned with bunkai.

Refer to `README.md` for quick-start instructions, CLI examples, current benchmarks (≈40–285× faster than pure-Python bunkai on the bundled corpora), and acknowledgements to [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai).

## Architecture Snapshot
- **Rust core (`src/lib.rs`)** — Implements face-mark detection, emotion expressions, emoji detection, punctuation rules, dot/number exceptions, line-break handling, and indirect quote filtering. Operates on Unicode character indices, exposes `segment(text)` through PyO3, and releases the GIL via `py.allow_threads`.
- **Emoji metadata (`src/emoji_data.rs`)** — Auto-generated with `scripts/generate_emoji_data.py` (uses `emoji` and `emojis`). Regenerate whenever upstream emoji datasets change.
- **Python layer (`fast_bunkai/`)** — `core.py` wraps the Rust function and builds Janome-based morphological spans; `annotations.py` mirrors bunkai dataclasses.

## Test & Benchmark Checklist
- **Pytest suite** (`tests/test_compatibility.py`): compares sentence splits, EOS indices, and morphological tokens with bunkai across diverse texts, including threaded and asyncio execution. Run via `uv run pytest`.
- **Rust unit tests**: targeted checks such as `cargo test face_mark_detection_matches_reference`.
- **Benchmarks** (`scripts/benchmark.py`): times FastBunkai vs. bunkai on Japanese, English, and long-text corpora, validating correctness before timing. Example:
  ```bash
  uv run python scripts/benchmark.py --repeats 3 --jp-loops 100 --en-loops 100 --custom-loops 10
  ```
  Benchmarks are time-consuming; CI executes them, while release flows usually skip unless numbers need refreshing.

## Development Workflow
1. Install dependencies / editable wheel
   ```bash
   uv sync --reinstall
   ```
2. Regenerate emoji data (only if needed)
   ```bash
   uv run python scripts/generate_emoji_data.py
   ```
3. Run tests
   ```bash
   uv run pytest
   cargo test face_mark_detection_matches_reference
   ```
4. (Optional) Run benchmarks using the command above when validating performance changes.

## Release Workflow
1. Branch from the latest main: `git checkout -b release/vX.Y.Z origin/main`.
2. Bump versions in `pyproject.toml`, `Cargo.toml`, `Cargo.lock`, and `uv.lock`; add a new entry to `CHANGELOG.md`.
3. Update public docs (e.g., `README.md`) if the release introduces user-visible changes.
4. Run the full tox matrix: `uv run tox`. Execute benchmarks when refreshed numbers are required.
5. Before opening a PR, inspect the actual diff (`git diff`, `git diff origin/main...`) and ensure the changelog and PR description match the code changes. Never rely solely on commit messages.
6. Create the release PR with `gh pr create --base main --head release/vX.Y.Z --title "Release vX.Y.Z" --body "<summary/tests>"`. If `gh` is unavailable, open the PR manually and include the diff summary.
7. After merge, return to `main`, tag, and push: `git tag vX.Y.Z && git push origin vX.Y.Z`. Trusted Publishing triggers `.github/workflows/publish.yml` to build and publish wheels (Linux x86_64/aarch64, macOS universal2, Windows x86_64-msvc).
8. Optionally publish GitHub release notes with `gh release create vX.Y.Z --generate-notes`.

## Tooling & Quality Gates
- **tox environments**: `pytests`, `lint`, `format-check`, `typecheck`, `rust-fmt`, `rust-clippy` (see `tox.ini`). Example:
  ```bash
  uv run tox -e pytests,lint,typecheck,rust-fmt,rust-clippy
  ```
- **Linters & formatters**: Ruff handles linting/formatting; Pyright performs type checking; Cargo covers rustfmt and clippy.
- **CI workflows**: `.github/workflows/ci.yml` runs the tox matrix and lightweight benchmarks on PRs; `.github/workflows/publish.yml` builds wheels (Linux, macOS, Windows) and uploads to PyPI after a tag push.

## Concurrency Notes
`segment_impl` keeps all state local, so multiple threads can call into the pipeline safely. The Python wrapper stores no mutable shared state, allowing reuse of a `FastBunkai` instance across threads or asyncio tasks.

## Additional Tips
- Minimum supported CPython version: 3.10 (extension built with abi3-py310).
- Import FastBunkai as a bunkai replacement: `from fast_bunkai import FastBunkai as Bunkai`.
- Regenerate emoji metadata whenever the underlying datasets or packages update.
- Benchmark results are hardware-dependent; rerun them on release targets before quoting numbers.
