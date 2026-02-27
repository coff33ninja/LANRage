# Root Layout Policy

This project keeps root-level folders focused on runtime code, tests, tooling, and repo metadata.

## Root Directory Rules

- Keep application/runtime folders in root:
  - `api/`, `core/`, `servers/`, `static/`, `game_profiles/`, `tests/`, `tools/`
- Keep repository/automation folders in root:
  - `.github/`, `.kiro/`
- Keep documentation in `docs/` and its subfolders.

## Documentation Placement

- Canonical docs live in `docs/*.md`.
- Project planning/status docs live in `docs/project/`.
- Diagram docs live in `docs/diagrams/`.

## Completed Cleanup

- Used temporary external research content to evolve canonical docs.
- Removed temporary research source folders from root and docs after merge.
- Removed empty `ci_logs/` from root.
