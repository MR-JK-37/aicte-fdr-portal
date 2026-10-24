"""Entry point for the `worker` docker-compose process.

Runs the outbox consumer loop (app.outbox.worker) in the foreground
thread and the DB-leased scheduler loop (app.outbox.scheduler) in a
background daemon thread of the same process.

Multiple replicas of this same container are safe to run side by side:
every replica runs its own outbox consumer (safe under `FOR UPDATE SKIP
LOCKED` — see app.outbox.worker.claim_batch), but only one replica's
scheduler thread will hold the Postgres advisory-lock lease at a time
(app.outbox.scheduler) — the rest just poll for it and otherwise do
nothing on the scheduler side.

Run with: `uv run python -m app.outbox.run_worker`
"""

import logging
import threading

from app.outbox import scheduler, worker

logging.basicConfig(level=logging.INFO)


def main() -> None:
    scheduler_thread = threading.Thread(
        target=scheduler.run_forever, name="scheduler-loop", daemon=True
    )
    scheduler_thread.start()
    worker.run_forever()


if __name__ == "__main__":
    main()
