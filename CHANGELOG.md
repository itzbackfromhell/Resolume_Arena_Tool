# Changelog

## 0.2.1

### Added

- Added actionable user-facing error formatting for CLI and future GUI surfaces.
- Added project logging configuration with a per-user log file.
- Added CLI `--verbose` and `--no-log-file` runtime flags on commands.
- Added GUI worker message contract helpers for progress, success, error, and finished states.
- Added focused tests for error UX, logging configuration, and GUI worker lifecycle behavior.

### Changed

- CLI failures now keep the legacy `ERROR: ...` prefix while also printing a recovery hint.
- CLI export, batch, validation, and rembg-check flows now write structured package logs.
- GUI worker architecture is now documented as a queue-safe migration layer before the `app.py` UI split.

## 0.2.0

### Added

- CLI feature parity for professional single-image, batch, validation, and rembg-check workflows.
- Output Validation 2.0 for exported alpha PNG contracts.
- Batch Professional Mode with optional JSON reports.
- Project-local rembg model cache support.
