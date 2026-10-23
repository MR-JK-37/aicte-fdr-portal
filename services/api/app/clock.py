"""Injectable clock (CLAUDE.md #10 / MASTER_PROMPT §17.4): "the server
clock is the only clock (injectable `Clock` so tests can time-travel;
prod rejects the test clock)."

`RealClock` is the only `Clock` implementation allowed to exist outside
`services/api/tests/`. Anything that needs to time-travel for a test
(e.g. "advance by 300 simulated days to walk the full reminder ladder")
must define its own fake clock as a pytest fixture inside the tests
package — never import one from here, because there isn't one to
import. This file intentionally has no notion of an offset/override.
"""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Anything with a `now()` that returns an aware UTC datetime."""

    def now(self) -> datetime: ...


class RealClock:
    """The only production clock. Always real wall-clock time."""

    def now(self) -> datetime:
        return datetime.now(UTC)
