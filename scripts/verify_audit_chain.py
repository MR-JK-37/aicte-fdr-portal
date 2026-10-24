#!/usr/bin/env python3
"""Auditor Verification Tool for Hash-Chained Audit Log and Signed Checkpoints.

Usage:
    python scripts/verify_audit_chain.py [--db-url DATABASE_URL]

Verifies:
1. Complete SHA-256 hash chaining of audit_log from GENESIS_HASH to latest row.
2. Every audit_checkpoint's Ed25519 signature.
3. Alignment between audit_checkpoint chain_root_hash and audit_log row_hash.
"""

import argparse
import os
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Ensure services/api is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "services", "api")
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from app.audit import DEV_PUBLIC_KEY, verify_chain, verify_checkpoint
from app.models.audit import AuditCheckpoint, AuditLog


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify audit chain tamper-evidence and checkpoint signatures")
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL",
            os.environ.get("SUPERUSER_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"),
        ),
        help="Postgres connection string",
    )
    args = parser.parse_args()

    print("=================================================================")
    print("AICTE FDR Portal — Audit Chain & Checkpoint Integrity Verifier")
    print("=================================================================")

    try:
        engine = create_engine(args.db_url, future=True)
        Session = sessionmaker(bind=engine, future=True)
        session = Session()
    except Exception as e:
        print(f"[ERROR] Could not connect to database: {e}", file=sys.stderr)
        return 1

    try:
        # Step 1: Verify hash chain in audit_log
        total_events = session.execute(select(AuditLog)).scalars().all()
        event_count = len(total_events)
        print(f"[*] Total audit entries in log: {event_count}")

        chain_result = verify_chain(session)
        if not chain_result.ok:
            print(f"[FAIL] Audit hash chain broken at record ID {chain_result.broken_at_id}: {chain_result.reason}")
            return 1
        print("[PASS] Audit log hash-chain integrity verified: 0 tamper points detected.")

        # Step 2: Verify signed checkpoints
        checkpoints = session.execute(
            select(AuditCheckpoint).order_by(AuditCheckpoint.checkpoint_index.asc())
        ).scalars().all()
        print(f"[*] Total signed checkpoints found: {len(checkpoints)}")

        for cp in checkpoints:
            sig_ok = verify_checkpoint(cp, DEV_PUBLIC_KEY)
            if not sig_ok:
                print(f"[FAIL] Checkpoint #{cp.checkpoint_index} Ed25519 signature invalid!")
                return 1

            # Verify that the last event row_hash equals the checkpoint's chain_root_hash
            if cp.last_event_id:
                ev = session.get(AuditLog, cp.last_event_id)
                if not ev or ev.row_hash != cp.chain_root_hash:
                    print(
                        f"[FAIL] Checkpoint #{cp.checkpoint_index} root hash ({cp.chain_root_hash}) "
                        f"does not match actual event #{cp.last_event_id} hash ({ev.row_hash if ev else 'None'})"
                    )
                    return 1

            print(
                f"  -> Checkpoint #{cp.checkpoint_index} (events {cp.first_event_id}..{cp.last_event_id}): "
                f"Signature VALID, root {cp.chain_root_hash[:16]}... OK"
            )

        print("=================================================================")
        print("[SUCCESS] All audit chain links and checkpoint signatures VERIFIED.")
        print("=================================================================")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
