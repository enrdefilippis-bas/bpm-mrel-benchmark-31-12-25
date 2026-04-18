#!/usr/bin/env python3
"""Final verification: metrics check, app import, and ready-to-commit status."""
import sys
import os
from pathlib import Path

# Add project to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=" * 70)
print("FINAL VERIFICATION FOR MREL BENCHMARK EXTENSION")
print("=" * 70)

# Step 1: Check imports
print("\n1. Checking app imports...")
try:
    from app.app import app
    print("   ✓ App imports OK")
except Exception as e:
    print(f"   ✗ App import failed: {e}")
    sys.exit(1)

# Step 2: Check parquet files
print("\n2. Checking data files...")
facts_file = ROOT / "data" / "processed" / "facts.parquet"
banks_file = ROOT / "data" / "processed" / "banks.parquet"

if not facts_file.exists():
    print(f"   ✗ {facts_file} not found")
    sys.exit(1)
if not banks_file.exists():
    print(f"   ✗ {banks_file} not found")
    sys.exit(1)

import pandas as pd
try:
    facts = pd.read_parquet(facts_file)
    banks = pd.read_parquet(banks_file)
    print(f"   ✓ facts.parquet: {len(facts):,} rows")
    print(f"   ✓ banks.parquet: {len(banks)} banks")
except Exception as e:
    print(f"   ✗ Failed to read parquets: {e}")
    sys.exit(1)

# Step 3: Verify peer sets resolved
print("\n3. Checking peer set resolution...")
from core.peers import ITALIAN_OSII_RESOLUTION, EU_OSII_SIMILAR_SIZE, resolve_peer_set

italian_leis = resolve_peer_set(ITALIAN_OSII_RESOLUTION, banks)
print(f"   ✓ Italian O-SIIs resolved: {len(italian_leis)} banks")

eu_similar_leis = resolve_peer_set(EU_OSII_SIMILAR_SIZE, banks, facts)
print(f"   ✓ EU similar size (150-300B TEM) resolved: {len(eu_similar_leis)} banks")

# Step 4: Verify key metrics
print("\n4. Checking metric values (Q4-2025)...")
from core.metrics import cet1_ratio, t1_capital_ratio, total_capital_ratio, leverage_ratio, total_assets

try:
    cet1 = cet1_ratio(facts)
    t1 = t1_capital_ratio(facts)
    tcap = total_capital_ratio(facts)
    lev = leverage_ratio(facts)
    assets = total_assets(facts)

    print(f"   ✓ CET1 ratio: {len(cet1)} rows")
    print(f"   ✓ Tier 1 ratio: {len(t1)} rows")
    print(f"   ✓ Total capital ratio: {len(tcap)} rows")
    print(f"   ✓ Leverage ratio: {len(lev)} rows")
    print(f"   ✓ Total assets: {len(assets)} rows")
except Exception as e:
    print(f"   ✗ Metric extraction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Spot-check key banks
print("\n5. Spot-checking key banks (Q4-2025)...")
banks_to_check = {
    'BPM': '815600E4E6DCD2D25E30',
    'UniCredit': '549300TRUWO2CD2G5692',
    'Intesa': '2W8N8UU78PMDQKZENC08'
}

from core.schema import Template
q4_2025 = pd.Timestamp("2025-12-31")

print(f"\n   Bank data for reference_date = {q4_2025.date()}")
print(f"   {'Bank':<15} {'CET1%':<8} {'T1%':<8} {'TCap%':<8} {'Lev%':<8}")
print("   " + "-" * 48)

for name, lei in banks_to_check.items():
    cet1_val = cet1[(cet1['entity_lei'] == lei) & (cet1['reference_date'] == q4_2025)]['cet1_ratio'].values
    t1_val = t1[(t1['entity_lei'] == lei) & (t1['reference_date'] == q4_2025)]['t1_capital_ratio'].values
    tcap_val = tcap[(tcap['entity_lei'] == lei) & (tcap['reference_date'] == q4_2025)]['total_capital_ratio'].values
    lev_val = lev[(lev['entity_lei'] == lei) & (lev['reference_date'] == q4_2025)]['leverage_ratio'].values

    cet1_str = f"{cet1_val[0]*100:.2f}" if len(cet1_val) > 0 else "n/a"
    t1_str = f"{t1_val[0]*100:.2f}" if len(t1_val) > 0 else "n/a"
    tcap_str = f"{tcap_val[0]*100:.2f}" if len(tcap_val) > 0 else "n/a"
    lev_str = f"{lev_val[0]*100:.2f}" if len(lev_val) > 0 else "n/a"

    print(f"   {name:<15} {cet1_str:<8} {t1_str:<8} {tcap_str:<8} {lev_str:<8}")

print("\n" + "=" * 70)
print("ALL CHECKS PASSED - READY TO COMMIT")
print("=" * 70)
