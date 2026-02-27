# Versioning

Versioning and release discipline for LANrage.

## Version Semantics

- use semantic versioning style for release communication
- classify changes by impact (breaking/feature/fix)

## Release Inputs

Before release:
- required CI checks green
- targeted regression tests complete
- changelog/docs updated for user-visible behavior

## Release Outputs

Each release should provide:
- version tag
- changelog entry
- artifact set (as applicable)
- post-release verification notes

## Changelog Commit IDs

To include commit IDs for each release iteration, generate a commit trace from git:

```bash
python tools/docs/changelog_commits.py --since 1.4.0
```

The command prints markdown-ready lines (`short_sha`, date, subject) you can paste into
`CHANGELOG.md` under `Unreleased` or a version section.

## Compatibility Guidance

When introducing behavior changes:
- call out migration/compat notes in docs
- preserve endpoint/config compatibility where practical
- document explicit breakages early

## References

- [CI/CD](CI_CD.md)
- [Production Ready](PRODUCTION_READY.md)
