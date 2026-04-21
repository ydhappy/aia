# Redis Setup

AIA can now use Redis as the shared state store.

## Enable Redis mode
Set:
- `STATE_STORE_MODE=redis`
- `REDIS_URL=redis://your-redis-host:6379/0`

## What is stored
- latest robot state
- robot profile
- recent robot events
- latest trace
- local process metrics counters

## Recommended use
- multiple AIA instances
- restart resilience
- shared robot knowledge across world servers
- large bot groups

## Note
Metrics are still process-local counters in the current implementation. Shared global metrics can be added later if needed.
