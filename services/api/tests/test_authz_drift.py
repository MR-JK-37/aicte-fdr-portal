"""CI drift test: verifies that ROLE_PERMISSIONS_MATRIX in app/authz.py
matches docs/AUTH_ROLES_MATRIX.md §3 verbatim.

Fails in CI if anyone edits the matrix doc without updating the code or vice versa (R2.7).
"""

from pathlib import Path

from app.authz import ROLE_PERMISSIONS_MATRIX, PermissionVerb
from app.models.enums import AppRole

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DOC_PATH = REPO_ROOT / "docs" / "AUTH_ROLES_MATRIX.md"

ROLE_COLUMN_MAP = {
    1: AppRole.ORG_ADMIN,
    2: AppRole.INSTITUTION_SUBMITTER,
    3: AppRole.INSTITUTION_VIEWER,
    4: AppRole.INTAKE_OFFICER,
    5: AppRole.SCRUTINY_OFFICER,
    6: AppRole.FINANCE_VERIFIER,
    7: AppRole.REGIONAL_SUPERVISOR,
    8: AppRole.COMPETENT_AUTHORITY,
    9: AppRole.AUDIT_REVIEWER,
    10: AppRole.IDENTITY_ADMIN,
    11: AppRole.PLATFORM_OPERATOR,
    12: AppRole.BANK_VERIFIER,
}


def test_auth_roles_matrix_doc_drift():
    assert DOC_PATH.exists(), f"Missing matrix doc at {DOC_PATH}"

    text = DOC_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    table_lines: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## 3. Permission verbs per role"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip().startswith("|") and not line.strip().startswith("|---"):
            table_lines.append(line.strip())

    assert len(table_lines) >= 15, f"Expected table lines in section 3, got {len(table_lines)}"

    # Parse header to verify columns
    header = [c.strip() for c in table_lines[0].split("|")[1:-1]]
    assert header[0] == "Verb"

    # Row mapping
    for row_str in table_lines[1:]:
        cells = [c.strip() for c in row_str.split("|")[1:-1]]
        if len(cells) < 13:
            continue
        raw_verb = cells[0]
        # Multi-verbs separated by slash, e.g. "create_draft / edit_draft / submit"
        verbs_in_row = [v.strip() for v in raw_verb.split("/")]

        for col_idx, cell_value in enumerate(cells[1:], start=1):
            if col_idx not in ROLE_COLUMN_MAP:
                continue
            role = ROLE_COLUMN_MAP[col_idx]
            is_allowed = cell_value != "—" and cell_value != "-"

            for v in verbs_in_row:
                # Normalise verb if needed
                v_norm = v.split("(")[0].strip()
                if v_norm == "reconcile_statement" or v_norm == "resolve_exception" or v_norm in PermissionVerb._value2member_map_ or v_norm == "configure_integrations" or v_norm == "administer_platform":
                    verb_enum = PermissionVerb(v_norm)
                else:
                    continue

                expected_in_matrix = is_allowed
                actual_in_matrix = verb_enum.value in ROLE_PERMISSIONS_MATRIX.get(role, {})
                assert actual_in_matrix == expected_in_matrix, (
                    f"Drift detected for role {role.value}, verb {verb_enum.value}: "
                    f"Doc says '{cell_value}' (allowed={expected_in_matrix}), but "
                    f"ROLE_PERMISSIONS_MATRIX has {actual_in_matrix}."
                )
