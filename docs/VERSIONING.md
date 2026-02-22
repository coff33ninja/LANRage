# Versioning Strategy

This project uses Semantic Versioning (`MAJOR.MINOR.PATCH`) and Keep a Changelog.

## Current Reality
- Up to this point, version bumps/releases were handled informally and did not consistently follow this exact workflow.
- This document defines the process to follow from now on.

## Goals
- Keep releases predictable.
- Make change impact obvious to users and contributors.
- Reduce release anxiety by using a repeatable flow.

## Version Rules

### PATCH (`x.y.Z`)
Use for bug fixes and low-risk improvements.
- UI alignment fixes
- Logging/telemetry tweaks
- Doc-only corrections (optional patch if you ship docs)
- Internal refactors with no user-facing behavior change

### MINOR (`x.Y.z`)
Use for backward-compatible features.
- New tabs/views/workflows in Web UI
- New API endpoints that do not break old clients
- New supported game profiles/mod sync capabilities
- New tooling/automation that changes contributor workflow

### MAJOR (`X.y.z`)
Use for breaking changes.
- Removed/renamed API endpoints
- Behavior changes that require user migration
- Config format changes requiring manual intervention
- Compatibility breaks in party/network/control flows

## Release Cadence
- Patch: as needed (can be same-day).
- Minor: feature batches (recommended weekly/biweekly).
- Major: explicitly planned with migration notes.

## Source of Truth
- `CHANGELOG.md` is the release history source of truth.
- `pyproject.toml` is the runtime/package version source of truth.
- `README.md` should display the current released version.

## Release Flow (Manual)
1. Ensure working tree is clean.
2. Confirm quality checks:
   - `python tools/run_code_quality.py --check`
   - `python -m pytest`
3. Decide bump type (`patch`/`minor`/`major`) using the rules above.
4. Update version in `pyproject.toml`.
5. Move key entries from `## [Unreleased]` into a new version section in `CHANGELOG.md` with date.
6. Update any version mentions in docs (`README.md`, release docs).
7. Commit with message:
   - `release: vX.Y.Z`
8. Create tag:
   - `git tag vX.Y.Z`
9. Push branch + tag:
   - `git push`
   - `git push --tags`

## Changelog Policy
- Write user-facing changes first.
- Keep sections grouped under `Added`, `Changed`, `Fixed`, `Removed`, `Deprecated`, `Security`.
- Avoid duplicate detail across README and CHANGELOG; README summarizes, changelog details.

## Practical Decision Matrix
- “Did users gain a new capability?” -> `MINOR`
- “Did we break anything intentionally?” -> `MAJOR`
- “Did we fix or polish existing behavior?” -> `PATCH`

## Versioning Assistant Skill Template

If you want Codex to run this flow consistently every release, create a skill with this behavior:
- Read `CHANGELOG.md` and `pyproject.toml`.
- Propose bump type from unreleased entries.
- Apply version bump and changelog sectioning.
- Update README version references.
- Run quality checks.
- Prepare commit/tag commands.

Suggested skill name:
- `versioning-release-assistant`

Suggested trigger phrases:
- "prepare release"
- "bump version"
- "cut patch/minor/major release"
