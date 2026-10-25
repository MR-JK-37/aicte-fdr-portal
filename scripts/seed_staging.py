#!/usr/bin/env python3
"""Staging seed script (AUTH §4 / R2.6).

Creates synthetic tenants, synthetic bank, and one user per role across all 12 human roles.
Pre-enrolls passwords and TOTP secrets, storing credentials in `./.local/staging-users.json`.
Refuses to run if APP_ENV=production or ENV=production.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path

# Refuse to run in production per AUTH §4
app_env = os.environ.get("APP_ENV", os.environ.get("ENV", "dev")).lower()
if app_env == "production":
    print("FATAL: seed-staging refused to run: APP_ENV/ENV is set to 'production'.", file=sys.stderr)
    sys.exit(1)

# Ensure services/api is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
API_DIR = REPO_ROOT / "services" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.auth.security import (
    encrypt_totp_secret,
    generate_recovery_codes,
    generate_totp_secret,
    hash_password,
    hash_recovery_code,
)
from app.models.core import AppUser, Bank, Branch, Institution
from app.models.enums import AppRole

DB_URL = os.environ.get(
    "MIGRATION_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://fdr:fdr@localhost:5434/fdr",
    ),
)


def main() -> int:
    print("=== AICTE FDR Portal — Staging Seed (AUTH §4) ===")
    engine = create_engine(DB_URL, future=True)
    Session = sessionmaker(bind=engine, future=True)

    with Session() as session:
        # 1. Synthetic Tenants (Institution A & Institution B)
        inst_a = session.execute(
            select(Institution).where(Institution.aicte_code == "1-1000000001")
        ).scalar_one_or_none()
        if not inst_a:
            inst_a = Institution(
                id=uuid.uuid4(),
                aicte_code="1-1000000001",
                name="Apex Institute of Technology (Synthetic Tenant A)",
            )
            session.add(inst_a)

        inst_b = session.execute(
            select(Institution).where(Institution.aicte_code == "1-1000000002")
        ).scalar_one_or_none()
        if not inst_b:
            inst_b = Institution(
                id=uuid.uuid4(),
                aicte_code="1-1000000002",
                name="Beacon College of Engineering (Synthetic Tenant B)",
            )
            session.add(inst_b)

        # 2. Synthetic Bank & Branch
        bank = session.execute(
            select(Bank).where(Bank.name == "State Bank of India (Synthetic Staging Bank)")
        ).scalar_one_or_none()
        if not bank:
            bank = Bank(
                id=uuid.uuid4(),
                name="State Bank of India (Synthetic Staging Bank)",
            )
            session.add(bank)
            session.flush()

        branch = session.execute(
            select(Branch).where(Branch.ifsc == "SBIN0099999")
        ).scalar_one_or_none()
        if not branch:
            branch = Branch(
                id=uuid.uuid4(),
                bank_id=bank.id,
                ifsc="SBIN0099999",
                name="AICTE Treasury Special Branch",
            )
            session.add(branch)

        session.flush()

        # 3. 12 Human Roles seed definitions
        # Format: (role, email, full_name, institution, delegation_limit, region_id)
        role_definitions = [
            # Institution A
            (AppRole.ORG_ADMIN, "admin.inst_a@staging.aicte.gov.in", "Dr. A. Sharma (Org Admin)", inst_a, None, None),
            (AppRole.INSTITUTION_SUBMITTER, "submitter.inst_a@staging.aicte.gov.in", "Prof. B. Verma (Submitter)", inst_a, None, None),
            (AppRole.INSTITUTION_VIEWER, "viewer.inst_a@staging.aicte.gov.in", "Mr. C. Patel (Viewer)", inst_a, None, None),
            # Institution B (for cross-tenant verification)
            (AppRole.ORG_ADMIN, "admin.inst_b@staging.aicte.gov.in", "Dr. X. Rao (Org Admin B)", inst_b, None, None),
            # AICTE Bureau roles
            (AppRole.INTAKE_OFFICER, "intake.officer@staging.aicte.gov.in", "Shri D. Kumar (Intake Officer)", None, None, None),
            (AppRole.SCRUTINY_OFFICER, "scrutiny.officer@staging.aicte.gov.in", "Smt. E. Nair (Scrutiny Officer)", None, None, None),
            (AppRole.FINANCE_VERIFIER, "finance.verifier@staging.aicte.gov.in", "Shri F. Menon (Finance Verifier)", None, None, None),
            (AppRole.REGIONAL_SUPERVISOR, "regional.supervisor@staging.aicte.gov.in", "Dr. G. Iyer (Regional Supervisor)", None, None, "south"),
            (AppRole.COMPETENT_AUTHORITY, "competent.authority@staging.aicte.gov.in", "Dr. H. Murthy (Competent Authority)", None, Decimal("50000000.00"), None),
            (AppRole.AUDIT_REVIEWER, "auditor@staging.aicte.gov.in", "Shri I. Das (Audit Reviewer)", None, None, None),
            (AppRole.IDENTITY_ADMIN, "iam.admin@staging.aicte.gov.in", "Smt. J. Mukherjee (IAM Admin)", None, None, None),
            (AppRole.PLATFORM_OPERATOR, "platform.operator@staging.aicte.gov.in", "Shri K. Reddy (Platform Operator)", None, None, None),
            # External Bank Verifier (must contain @sbi. for bank scope resolution)
            (AppRole.BANK_VERIFIER, "bank.verifier@sbi.staging.aicte.gov.in", "Mr. L. Swaminathan (Bank Verifier)", None, None, None),
        ]

        seeded_credentials = []

        for role, email, full_name, inst, delegation, region in role_definitions:
            user = session.execute(
                select(AppUser).where(AppUser.email == email)
            ).scalar_one_or_none()

            # Deterministic, memorable password for staging QA
            role_slug = role.value.replace("_", "").capitalize()
            password = f"Staging2026!{role_slug}"
            totp_secret = generate_totp_secret()
            recovery_codes = generate_recovery_codes(10)

            pwd_hash = hash_password(password)
            totp_enc = encrypt_totp_secret(totp_secret)
            recovery_hashed = [hash_recovery_code(c) for c in recovery_codes]

            if user:
                user.full_name = full_name
                user.role = role
                user.institution_id = inst.id if inst else None
                user.password_hash = pwd_hash
                user.totp_secret_encrypted = totp_enc
                user.recovery_codes_hashed = recovery_hashed
                user.mfa_enrolled = True
                user.is_active = True
                user.delegation_limit = delegation
                user.region_id = region
            else:
                user = AppUser(
                    id=uuid.uuid4(),
                    keycloak_sub=str(uuid.uuid4()),
                    email=email,
                    full_name=full_name,
                    role=role,
                    institution_id=inst.id if inst else None,
                    is_active=True,
                    mfa_enrolled=True,
                    password_hash=pwd_hash,
                    totp_secret_encrypted=totp_enc,
                    recovery_codes_hashed=recovery_hashed,
                    delegation_limit=delegation,
                    region_id=region,
                )
                session.add(user)

            seeded_credentials.append({
                "email": email,
                "role": role.value,
                "full_name": full_name,
                "password": password,
                "totp_secret": totp_secret,
                "recovery_codes": recovery_codes,
                "institution_id": str(inst.id) if inst else None,
                "institution_name": inst.name if inst else None,
                "region_id": region,
                "delegation_limit": str(delegation) if delegation else None,
            })

        # 4. Seed APH Regulatory Compliance Clauses
        from app.agents.seed_aph_clauses import seed as seed_aph
        aph_count = seed_aph(session)

        # 5. Seed Authentic FDR Mock Deposits (APH 2024-27 Clause 6.46)
        from datetime import datetime, timezone
        from app.instruments.router import compute_blind_index
        from app.models.core import Instrument
        from app.models.enums import EvidenceLevel, InstrumentStatus, InstrumentType

        inst_num_1 = "67394417821"
        if not session.execute(select(Instrument).where(Instrument.instrument_number == inst_num_1)).scalar_one_or_none():
            session.add(Instrument(
                id=uuid.uuid4(),
                institution_id=inst_a.id,
                branch_id=branch.id,
                type=InstrumentType.FDR,
                status=InstrumentStatus.EXPIRING,
                evidence_level=EvidenceLevel.L2_BANK_CONFIRMED,
                instrument_number=inst_num_1,
                blind_index=compute_blind_index(inst_num_1),
                amount=5000000.00,
                issue_date=datetime(2018, 12, 14, 9, 30, tzinfo=timezone.utc),
                maturity_date=datetime(2026, 12, 14, 9, 30, tzinfo=timezone.utc),
                tenor_months=96,
                utr="SBIN418349102847",
            ))

        inst_num_2 = "041210109021"
        if not session.execute(select(Instrument).where(Instrument.instrument_number == inst_num_2)).scalar_one_or_none():
            session.add(Instrument(
                id=uuid.uuid4(),
                institution_id=inst_b.id,
                branch_id=branch.id,
                type=InstrumentType.FDR,
                status=InstrumentStatus.ACTIVE,
                evidence_level=EvidenceLevel.L2_BANK_CONFIRMED,
                instrument_number=inst_num_2,
                blind_index=compute_blind_index(inst_num_2),
                amount=3500000.00,
                issue_date=datetime(2019, 3, 2, 11, 0, tzinfo=timezone.utc),
                maturity_date=datetime(2027, 3, 2, 11, 0, tzinfo=timezone.utc),
                tenor_months=96,
                utr="CNRB519204817293",
            ))

        session.commit()

    # 5. Output credentials to .local/staging-users.json (never printed to console logs)
    local_dir = REPO_ROOT / ".local"
    local_dir.mkdir(parents=True, exist_ok=True)
    out_file = local_dir / "staging-users.json"
    out_file.write_text(json.dumps(seeded_credentials, indent=2), encoding="utf-8")
    out_file.chmod(0o600)

    print(f"[PASS] Successfully seeded {len(seeded_credentials)} users across 2 synthetic tenants and 1 bank.")
    print(f"[PASS] Credentials securely written to {out_file} (mode 0600, gitignored).")
    print("[NOTE] All staging accounts are marked MFA enrolled with pre-generated TOTP secrets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
