# Contributing

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,rembg]"
```

## Gates

```powershell
ruff check .
pytest
```

## Branching

Use small feature branches:

```powershell
git checkout -b feat/short-description
```

## Commit style

Prefer clear conventional-style messages:

```text
feat: add watch folder processor
fix: preserve alpha during canvas fitting
chore: update docs
```
