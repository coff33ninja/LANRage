# User Guide

Operator and player workflows for day-to-day LANrage usage.

## Core Workflows

### Create party

1. Open UI.
2. Create party.
3. Share party ID.

### Join party

1. Enter party ID and name.
2. Join.
3. Verify peer states.

### Leave party

- use leave action to cleanly disconnect and clear session state.

## Server Browser Workflow

- browse active servers
- apply filters (game/capacity/search/tags)
- favorite frequently used servers
- use latency measurement before joining

## Settings Workflow

- review current settings
- update required values
- save and activate named config sets
- reset to defaults when diagnosing misconfiguration

## Discord Workflow (Optional)

- configure webhook and invite
- test notification delivery
- optionally enable Rich Presence with app ID

## Health Workflow

When session quality drops:
1. check party/peer status
2. inspect metrics summary
3. confirm direct vs relay path
4. review troubleshooting runbook

## Safety Notes

- treat webhook URLs and similar integration values as sensitive
- avoid force-closing app during active reconfiguration if possible

## Next Reading

- [Server Browser](/docs/core/gameplay/SERVER_BROWSER.md)
- [Settings](/docs/core/control_plane/SETTINGS.md)
- [Metrics](/docs/core/observability/METRICS.md)
- [Troubleshooting](TROUBLESHOOTING.md)
