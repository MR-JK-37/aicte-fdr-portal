#!/usr/bin/env python3
"""verify_mobile_icons.py — Enforce icon hygiene in apps/mobile.

DESIGN_SPEC.md §8 & §13.3:
"Material Symbols only on Android, SF Symbols only on iOS, and both resolve from
the single closed Icon.tsx enum so an icon-import lint rule fails on any other icon source."
"""

import sys
import re
from pathlib import Path

FORBIDDEN_PATTERNS = [
    r"@expo/vector-icons",
    r"react-native-vector-icons",
    r"lucide-react-native",
    r"react-native-feather",
    r"font-awesome",
]

MOBILE_ROOT = Path(__file__).resolve().parent.parent / "apps" / "mobile"
ALLOWED_FILE = MOBILE_ROOT / "src" / "design-system" / "Icon.tsx"

def check_icons() -> int:
    errors = 0
    checked_files = 0

    print("=================================================================")
    print("AICTE FDR Mobile — Icon Import Hygiene Verifier (DESIGN_SPEC §8)")
    print("=================================================================")

    for path in MOBILE_ROOT.rglob("*.tsx"):
        if "node_modules" in str(path) or ".expo" in str(path):
            continue

        checked_files += 1
        content = path.read_text(encoding="utf-8")

        for pattern in FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"[FAIL] Forbidden icon library '{pattern}' found in: {path.relative_to(MOBILE_ROOT)}")
                errors += 1

        # Check that direct raw icon imports only occur in Icon.tsx
        if path.resolve() != ALLOWED_FILE.resolve():
            if "material-symbols-react-native" in content or "@material-symbols-react-native" in content:
                print(f"[FAIL] Direct material-symbols import outside Icon.tsx: {path.relative_to(MOBILE_ROOT)}")
                errors += 1
            if "expo-symbols" in content:
                print(f"[FAIL] Direct expo-symbols import outside Icon.tsx: {path.relative_to(MOBILE_ROOT)}")
                errors += 1

    print(f"[*] Total mobile source files scanned: {checked_files}")
    if errors == 0:
        print("[SUCCESS] All mobile icons strictly routed through Icon.tsx using Material Symbols / SF Symbols.")
        print("=================================================================")
        return 0
    else:
        print(f"[FAILED] {errors} icon lint errors detected.")
        print("=================================================================")
        return 1

if __name__ == "__main__":
    sys.exit(check_icons())
