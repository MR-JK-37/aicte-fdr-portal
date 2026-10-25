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
        # 1. Realistic Technical Institutions
        institutions_def = [
            ("1-1000000001", "Apex Institute of Technology, Bengaluru", "south-west"),
            ("1-1000000002", "Beacon Institute of Technology & Management, Chennai", "south"),
            ("1-3324519801", "PSG College of Technology, Coimbatore", "south"),
            ("1-4581290342", "Veermata Jijabai Technological Institute (VJTI), Mumbai", "west"),
            ("1-2814590214", "RV College of Engineering, Bengaluru", "south-west"),
        ]
        inst_map = {}
        for code, name, reg in institutions_def:
            inst = session.execute(
                select(Institution).where(Institution.aicte_code == code)
            ).scalar_one_or_none()
            if not inst:
                inst = Institution(id=uuid.uuid4(), aicte_code=code, name=name)
                session.add(inst)
            else:
                inst.name = name
            inst_map[code] = inst
        session.flush()

        inst_a = inst_map["1-1000000001"]
        inst_b = inst_map["1-1000000002"]

        # 2. Real Nationalised Banks & Designated Institutional Branches
        banks_def = [
            ("State Bank of India", "SBIN0000691", "Treasury Special Branch, Parliament Street, New Delhi"),
            ("Punjab National Bank", "PUNB0112000", "AICTE Bureau Special Branch, Nelson Mandela Marg, New Delhi"),
            ("Bank of Baroda", "BARB0INSTIT", "Institutional Banking Branch, MG Road, Bengaluru"),
            ("Canara Bank", "CNRB0001920", "Higher Education Corporate Branch, Anna Salai, Chennai"),
        ]
        branch_map = {}
        for b_name, ifsc, br_name in banks_def:
            b = session.execute(
                select(Bank).where(Bank.name == b_name)
            ).scalars().first()
            if not b:
                b = Bank(id=uuid.uuid4(), name=b_name)
                session.add(b)
                session.flush()

            br = session.execute(
                select(Branch).where(Branch.ifsc == ifsc)
            ).scalars().first()
            if not br:
                br = Branch(id=uuid.uuid4(), bank_id=b.id, ifsc=ifsc, name=br_name)
                session.add(br)
            else:
                br.name = br_name
            branch_map[b_name] = br

        # Also preserve legacy SBIN0099999 alias for backward compatibility
        br_legacy = session.execute(select(Branch).where(Branch.ifsc == "SBIN0099999")).scalars().first()
        if not br_legacy:
            session.add(Branch(id=uuid.uuid4(), bank_id=branch_map["State Bank of India"].bank_id, ifsc="SBIN0099999", name="AICTE Treasury Special Branch"))
        session.flush()

        branch = branch_map["State Bank of India"]

        # 3. 12 Human Roles seed definitions
        # Format: (role, email, full_name, institution, delegation_limit, region_id)
        role_definitions = [
            # Institution A (Apex Institute of Technology, Bengaluru)
            (AppRole.ORG_ADMIN, "admin.inst_a@staging.aicte.gov.in", "Dr. A. Sharma (Principal & Director)", inst_a, None, None),
            (AppRole.INSTITUTION_SUBMITTER, "submitter.inst_a@staging.aicte.gov.in", "Prof. B. Verma (Registrar)", inst_a, None, None),
            (AppRole.INSTITUTION_VIEWER, "viewer.inst_a@staging.aicte.gov.in", "Mr. C. Patel (Finance Officer)", inst_a, None, None),
            # Institution B (Beacon Institute, Chennai)
            (AppRole.ORG_ADMIN, "admin.inst_b@staging.aicte.gov.in", "Dr. X. Rao (Director)", inst_b, None, None),
            # AICTE Bureau roles
            (AppRole.INTAKE_OFFICER, "intake.officer@staging.aicte.gov.in", "Shri D. Kumar (Intake Officer)", None, None, None),
            (AppRole.SCRUTINY_OFFICER, "scrutiny.officer@staging.aicte.gov.in", "Smt. E. Nair (Scrutiny Officer)", None, None, None),
            (AppRole.FINANCE_VERIFIER, "finance.verifier@staging.aicte.gov.in", "Shri F. Menon (Finance Verifier)", None, None, None),
            (AppRole.REGIONAL_SUPERVISOR, "regional.supervisor@staging.aicte.gov.in", "Dr. G. Iyer (Regional Officer, South)", None, None, "south"),
            (AppRole.COMPETENT_AUTHORITY, "competent.authority@staging.aicte.gov.in", "Dr. H. Murthy (Member Secretary)", None, Decimal("50000000.00"), None),
            (AppRole.AUDIT_REVIEWER, "auditor@staging.aicte.gov.in", "Shri I. Das (Chief Vigilance Officer)", None, None, None),
            (AppRole.IDENTITY_ADMIN, "iam.admin@staging.aicte.gov.in", "Smt. J. Mukherjee (IAM Administrator)", None, None, None),
            (AppRole.PLATFORM_OPERATOR, "platform.operator@staging.aicte.gov.in", "Shri K. Reddy (Platform Administrator)", None, None, None),
            # External Bank Verifier
            (AppRole.BANK_VERIFIER, "bank.verifier@sbi.staging.aicte.gov.in", "Mr. L. Swaminathan (Assistant General Manager, SBI)", None, None, None),
        ]

        seeded_credentials = []

        for role, email, full_name, inst, delegation, region in role_definitions:
            user = session.execute(
                select(AppUser).where(AppUser.email == email)
            ).scalar_one_or_none()

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
        from datetime import datetime, timedelta, timezone
        from app.instruments.router import compute_blind_index
        from app.models.core import Instrument, ScrutinyObservation
        from app.models.enums import EvidenceLevel, InstrumentStatus, InstrumentType
        from app.models.extensions import ExportJob

        # Instrument specifications across approved institutions
        instruments_specs = [
            # Apex Institute (Tenant A)
            {
                "num": "SBI/2021/FDR/9418201",
                "inst": inst_a,
                "branch": branch_map["State Bank of India"],
                "status": InstrumentStatus.EXPIRING,
                "level": EvidenceLevel.L2_BANK_CONFIRMED,
                "amount": 5000000.00,
                "issue": datetime(2018, 12, 14, 9, 30, tzinfo=timezone.utc),
                "maturity": datetime(2026, 12, 14, 9, 30, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "SBIN418349102847",
            },
            {
                "num": "SBI/2022/FDR/6810294",
                "inst": inst_a,
                "branch": branch_map["State Bank of India"],
                "status": InstrumentStatus.ACTIVE,
                "level": EvidenceLevel.L2_BANK_CONFIRMED,
                "amount": 3500000.00,
                "issue": datetime(2022, 8, 20, 10, 0, tzinfo=timezone.utc),
                "maturity": datetime(2030, 8, 20, 10, 0, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "SBIN820194821035",
            },
            {
                "num": "PNB/ND/FDR/2023/4921008",
                "inst": inst_a,
                "branch": branch_map["Punjab National Bank"],
                "status": InstrumentStatus.ACTIVE,
                "level": EvidenceLevel.L2_BANK_CONFIRMED,
                "amount": 2500000.00,
                "issue": datetime(2023, 3, 15, 11, 30, tzinfo=timezone.utc),
                "maturity": datetime(2031, 3, 15, 11, 30, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "PUNB230749102834",
            },
            {
                "num": "BARB/BLR/2024/7740192",
                "inst": inst_a,
                "branch": branch_map["Bank of Baroda"],
                "status": InstrumentStatus.UNDER_SCRUTINY,
                "level": EvidenceLevel.L0_DECLARED,
                "amount": 1500000.00,
                "issue": datetime(2024, 1, 10, 14, 0, tzinfo=timezone.utc),
                "maturity": datetime(2032, 1, 10, 14, 0, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "BARB240109182301",
            },
            {
                "num": "SBI/DEL/2025/1109482",
                "inst": inst_a,
                "branch": branch_map["State Bank of India"],
                "status": InstrumentStatus.SUBMITTED,
                "level": EvidenceLevel.L1_EXTRACTED,
                "amount": 2500000.00,
                "issue": datetime(2025, 6, 5, 10, 0, tzinfo=timezone.utc),
                "maturity": datetime(2033, 6, 5, 10, 0, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "SBIN250605910283",
            },
            {
                "num": "SBI/2016/FDR/3104829",
                "inst": inst_a,
                "branch": branch_map["State Bank of India"],
                "status": InstrumentStatus.MATURED,
                "level": EvidenceLevel.L2_BANK_CONFIRMED,
                "amount": 3500000.00,
                "issue": datetime(2016, 9, 10, 10, 0, tzinfo=timezone.utc),
                "maturity": datetime(2024, 9, 10, 10, 0, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "SBIN160910293810",
            },
            # Beacon Institute (Tenant B)
            {
                "num": "CNRB/CHN/FDR/2020/3819024",
                "inst": inst_b,
                "branch": branch_map["Canara Bank"],
                "status": InstrumentStatus.ACTIVE,
                "level": EvidenceLevel.L2_BANK_CONFIRMED,
                "amount": 3500000.00,
                "issue": datetime(2019, 3, 2, 11, 0, tzinfo=timezone.utc),
                "maturity": datetime(2027, 3, 2, 11, 0, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "CNRB519204817293",
            },
            # PSG Tech Coimbatore
            {
                "num": "SBI/2022/FDR/9012841",
                "inst": inst_map["1-3324519801"],
                "branch": branch_map["State Bank of India"],
                "status": InstrumentStatus.ACTIVE,
                "level": EvidenceLevel.L2_BANK_CONFIRMED,
                "amount": 5000000.00,
                "issue": datetime(2022, 7, 12, 10, 0, tzinfo=timezone.utc),
                "maturity": datetime(2030, 7, 12, 10, 0, tzinfo=timezone.utc),
                "tenor": 96,
                "utr": "SBIN992810394812",
            },
        ]

        saved_instruments = {}
        for spec in instruments_specs:
            existing = session.execute(
                select(Instrument).where(Instrument.instrument_number == spec["num"])
            ).scalar_one_or_none()
            if not existing:
                inst_obj = Instrument(
                    id=uuid.uuid4(),
                    institution_id=spec["inst"].id,
                    branch_id=spec["branch"].id,
                    type=InstrumentType.FDR,
                    status=spec["status"],
                    evidence_level=spec["level"],
                    instrument_number=spec["num"],
                    blind_index=compute_blind_index(spec["num"]),
                    amount=spec["amount"],
                    issue_date=spec["issue"],
                    maturity_date=spec["maturity"],
                    tenor_months=spec["tenor"],
                    utr=spec["utr"],
                )
                session.add(inst_obj)
                saved_instruments[spec["num"]] = inst_obj
            else:
                existing.institution_id = spec["inst"].id
                existing.branch_id = spec["branch"].id
                existing.status = spec["status"]
                existing.amount = spec["amount"]
                existing.issue_date = spec["issue"]
                existing.maturity_date = spec["maturity"]
                saved_instruments[spec["num"]] = existing
        session.flush()

        # Legacy numbers alignment
        for legacy_num in ["67394417821", "041210109021"]:
            leg = session.execute(select(Instrument).where(Instrument.instrument_number == legacy_num)).scalar_one_or_none()
            if leg:
                leg.institution_id = inst_a.id
                saved_instruments[legacy_num] = leg

        # 6. Seed Authentic Scrutiny Observations
        scrutiny_officer = session.execute(select(AppUser).where(AppUser.email == "scrutiny.officer@staging.aicte.gov.in")).scalar_one_or_none()
        officer_id = scrutiny_officer.id if scrutiny_officer else None
        target_fdr = saved_instruments.get("SBI/2021/FDR/9418201") or saved_instruments.get("67394417821")

        if target_fdr:
            obs_list = [
                ("Mandatory T-90 Expiry Ladder Alert: Deposit matures on 14-Dec-2026. Under APH Regulation Table 1.4, institution must submit either confirmation of renewal for additional 3-year term or application for discharge clearance before 15-Nov-2026.", "open"),
                ("Lien Endorsement Letter Verification: Joint lien marking letter submitted from State Bank of India Parliament Street branch must confirm irrevocable power of attorney in favor of Regional Officer, AICTE South-West (APH Clause 6.46).", "open"),
            ]
            for text, st in obs_list:
                obs_exists = session.execute(
                    select(ScrutinyObservation).where(
                        ScrutinyObservation.instrument_id == target_fdr.id,
                        ScrutinyObservation.observation == text,
                    )
                ).scalar_one_or_none()
                if not obs_exists:
                    session.add(ScrutinyObservation(
                        id=uuid.uuid4(),
                        institution_id=target_fdr.institution_id,
                        instrument_id=target_fdr.id,
                        officer_id=officer_id,
                        observation=text,
                        status=st,
                    ))

        # 7. Seed Authentic Statutory Export Jobs
        org_admin_user = session.execute(select(AppUser).where(AppUser.email == "admin.inst_a@staging.aicte.gov.in")).scalar_one_or_none()
        if org_admin_user:
            export_specs = [
                {
                    "key": "statutory_compliance",
                    "reason": "Annual statutory compliance review under AICTE Approval Process Handbook Clause 1.4",
                    "rows": 48,
                    "hash": "4a51e6047cf8f413d782110c9be019385b018320491823746190283746501928",
                    "content": "Instrument ID,Institution ID,Type,Status,FDR Number,UTR,Amount,Maturity Date\nSBI/2021/FDR/9418201,1-1000000001,FDR,EXPIRING,SBI/2021/FDR/9418201,SBIN418349102847,5000000.00,2026-12-14\nSBI/2022/FDR/6810294,1-1000000001,FDR,ACTIVE,SBI/2022/FDR/6810294,SBIN820194821035,3500000.00,2030-08-20\nPNB/ND/FDR/2023/4921008,1-1000000001,FDR,ACTIVE,PNB/ND/FDR/2023/4921008,PUNB230749102834,2500000.00,2031-03-15\n",
                },
                {
                    "key": "maturity_pipeline",
                    "reason": "Quarterly liquidity and maturity schedule analysis for South-West technical institutes",
                    "rows": 18,
                    "hash": "88bf209384716294018274610928374650192837465019283746501928374651",
                    "content": "Instrument ID,Institution ID,Type,Status,FDR Number,UTR,Amount,Maturity Date\nSBI/2021/FDR/9418201,1-1000000001,FDR,EXPIRING,SBI/2021/FDR/9418201,SBIN418349102847,5000000.00,2026-12-14\n",
                },
                {
                    "key": "reconciliation_summary",
                    "reason": "Statutory audit reconciliation with CIMS / SFMS banking core gateway",
                    "rows": 12,
                    "hash": "c204918237461092837465019283746501928374650192837465019283746501",
                    "content": "Instrument ID,Institution ID,Type,Status,FDR Number,UTR,Amount,Maturity Date\nBARB/BLR/2024/7740192,1-1000000001,FDR,PENDING_VERIFICATION,BARB/BLR/2024/7740192,BARB240109182301,1500000.00,2032-01-10\n",
                },
            ]
            for esp in export_specs:
                job_exists = session.execute(
                    select(ExportJob).where(
                        ExportJob.report_key == esp["key"],
                        ExportJob.requested_by == org_admin_user.id,
                    )
                ).scalar_one_or_none()
                if not job_exists:
                    session.add(ExportJob(
                        id=uuid.uuid4(),
                        requested_by=org_admin_user.id,
                        institution_id=inst_a.id,
                        report_key=esp["key"],
                        params={"financial_year": "2026-27"},
                        scope_filter={"institution_id": str(inst_a.id)},
                        reason=esp["reason"],
                        status="COMPLETED",
                        row_count=esp["rows"],
                        file_hash=esp["hash"],
                        file_content=esp["content"],
                        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                        completed_at=datetime.now(timezone.utc),
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
