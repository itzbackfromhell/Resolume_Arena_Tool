# AGENTS.md

## Project mission

Build a professional local-first asset-preparation tool for Resolume Arena/Avenue users. The current app creates one clean transparent 1920x1080 PNG from one normal image without paid cloud APIs.

## Non-negotiables

- Do not modify, patch, crack, inject into, or reverse-engineer Resolume binaries.
- Keep the core processing pipeline usable without Resolume installed.
- Keep paid APIs optional and disabled by default. Current default: no paid APIs at all.
- Prefer deterministic, testable image-processing code over hidden side effects.
- GUI must never block during long processing work.
- All exported assets must preserve alpha correctly.
- Avoid destructive operations. Never overwrite user files unless explicitly requested.

## Tech stack

- Python 3.11+
- Pillow for deterministic image/alpha operations
- optional rembg for local AI background removal
- Tkinter for the first desktop GUI
- pytest for tests
- ruff for linting
- PyInstaller for Windows builds

## Code style

- Keep domain logic in `src/resolume_alpha_tool/core/`.
- Keep UI thin; UI calls services, never performs heavy processing inline.
- Use dataclasses for configuration and result objects.
- Raise project-specific exceptions from `exceptions.py`.
- Type-hint public functions.
- Write tests for every core change.

## UX principles

- Make the default path stupidly simple: image in -> alpha PNG out.
- Show clear actionable errors.
- Use safe Resolume-oriented defaults: transparent PNG, 1920x1080 canvas, clean edges.
- Prefer safe defaults over maximum knobs.

## Future improvements

- Drag/drop support using an optional dependency.
- Better preview/compare UX.
- Installer packaging.
- Optional advanced controls only after the single-image path is stable.
