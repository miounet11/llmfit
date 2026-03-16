# Contributing

Thanks for contributing to LLMFit.

## Development

```sh
cargo build
cargo test
make site-preview
```

## Pull requests

1. Keep changes focused and easy to review.
2. Run `cargo fmt`, `cargo clippy --all-targets --all-features`, and `cargo test`.
3. Update docs when the user-facing behavior changes.
4. Include screenshots or terminal output for TUI or site changes when useful.

## Project areas

- `llmfit-core/`: hardware detection, model data, fit and planning logic
- `llmfit-tui/`: TUI, CLI, and REST API entrypoints
- `llmfit-desktop/`: macOS desktop app
- `site/`: static product site
- `deploy/`: isolated deployment assets for the site

## Release model

Tagged releases (`v*`) build binaries and publish GitHub release assets. Docker
images publish to GHCR through the dedicated Docker workflow.
