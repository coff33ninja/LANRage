# Games and Profiles

Game detection and profile-driven optimization behavior.

## Scope

Covers how LANrage recognizes games and applies profile metadata.

Related docs:
- [Supported Games](/docs/SUPPORTED_GAMES.md)
- [Settings](/docs/core/control_plane/SETTINGS.md)

## Profile Sources

- built-in profiles
- custom/community profiles

## Detection Model

Typical signals:
- process identity
- known ports/protocol hints
- configured profile metadata

## Optimization Use

Profiles can influence:
- transport expectations
- port handling
- broadcast/multicast behavior
- compatibility hints for session setup

## Custom Profile Guidance

- start from closest known game profile
- validate process/port assumptions in your environment
- keep names/version notes clear for future maintenance

## Validation

After adding/updating profile:
1. run session with game active
2. confirm detection status
3. verify peer connectivity and stability

## Acceptance Criteria

This doc is complete when profile sources, detection intent, and validation workflow are explicit.
