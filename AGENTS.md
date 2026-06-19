# AGENTS.md

## Project mission

Build a professional local-first asset-preparation tool for Resolume Arena/Avenue users. The tool creates clean transparent PNG/WebP visual assets from normal images without paid cloud APIs.

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
- Show clear logs and actionable errors.
- Use sane Resolume-oriented presets: transparent PNG, 1920x1080 canvas, clean edges.
- Prefer safe defaults over maximum knobs.

## Future improvements

- Drag/drop support using an optional dependency.
- OSC triggering.
- Resolume local REST/WebSocket sync.
- Project/session files.
- GPU-specific rembg profiles.
- Installer packaging.
