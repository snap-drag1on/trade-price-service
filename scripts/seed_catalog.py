"""
Seed script for product catalogs (CN, UZ, V45, laptops).
Applies migrations + inserts product research data.

Usage:
  python scripts/seed_catalog.py --table cn              # Dry run CN catalog (V43)
  python scripts/seed_catalog.py --table cn --apply       # Actually send to Supabase
  python scripts/seed_catalog.py --table uz               # Dry run UZ catalog (V44)
  python scripts/seed_catalog.py --table uz --apply       # Actually send to Supabase
  python scripts/seed_catalog.py --table v45              # Dry run V45 migration
  python scripts/seed_catalog.py --table v45 --apply      # Actually run V45 migration
  python scripts/seed_catalog.py --table lp               # Dry run laptop seed (V45 data)
  python scripts/seed_catalog.py --table lp --apply       # Insert laptop catalog
  python scripts/seed_catalog.py --table all --apply      # Apply cn + uz + v45 + lp in order
  python scripts/seed_catalog.py --apply --sql-only       # Migration SQL only, skip seed
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.supabase_client import get_service_client
from app.config import settings

SEED_FILES = {
    "cn": Path(__file__).parent.parent / "supabase" / "seed_cn_catalog.sql",
    "uz": Path(__file__).parent.parent / "supabase" / "seed_uz_catalog.sql",
    "v45": Path(__file__).parent.parent / "supabase" / "migrations" / "20260612_v45_product_catalog.sql",
    "lp": Path(__file__).parent.parent / "supabase" / "seed_laptops.sql",
    "v46": Path(__file__).parent.parent / "supabase" / "migrations" / "20260613_v46_agent_router.sql",
    "v47": Path(__file__).parent.parent / "supabase" / "migrations" / "20260614_v47_countries.sql",
    "v48": Path(__file__).parent.parent / "supabase" / "migrations" / "20260615_v48_trade_rules.sql",
    "v49": Path(__file__).parent.parent / "supabase" / "migrations" / "20260616_v49_freight_corridors.sql",
    "v50": Path(__file__).parent.parent / "supabase" / "migrations" / "20260617_v50_hs_code_reference.sql",
    "v51": Path(__file__).parent.parent / "supabase" / "migrations" / "20260618_v51_all_countries.sql",
    "v52": Path(__file__).parent.parent / "supabase" / "migrations" / "20260619_v52_all_hs_codes.sql",
    "v53": Path(__file__).parent.parent / "supabase" / "migrations" / "20260620_v53_all_freight_corridors.sql",
    "v54": Path(__file__).parent.parent / "supabase" / "migrations" / "20260621_v54_all_certifications.sql",
    "v55": Path(__file__).parent.parent / "supabase" / "migrations" / "20260622_v55_cbu_api.sql",
}

MIGRATION_COMMENTS = {
    "cn": "V43",
    "uz": "V44",
    "v45": "V45",
    "lp": "V45 (Laptops)",
    "v46": "V46",
    "v47": "V47",
    "v48": "V48",
    "v49": "V49",
    "v50": "V50",
    "v51": "V51",
    "v52": "V52",
    "v53": "V53",
    "v54": "V54",
    "v55": "V55",
}

SEED_DATA_COMMENTS = {
    "cn": "-- 2. Seed data:",
    "uz": "-- 2. Seed data:",
}


def exec_sql_via_api(sql: str) -> bool:
    """Run raw SQL via Supabase REST API (pg-meta /api/sql endpoint)."""
    if not settings.supabase_service_key:
        print("ERROR: SUPABASE_SERVICE_KEY not set.")
        return False

    # Extract project ref from supabase_url
    # e.g. https://letrqfcyrraatfwmuxln.supabase.co
    import re
    m = re.search(r'https?://([^.]+)\.supabase\.co', settings.supabase_url)
    if not m:
        print(f"ERROR: Cannot parse project ref from {settings.supabase_url}")
        return False
    project_ref = m.group(1)
    url = f"https://{project_ref}.supabase.co/api/sql"

    try:
        r = httpx.post(url, json={"query": sql}, headers={
            "Authorization": f"Bearer {settings.supabase_service_key}",
            "Content-Type": "application/json",
        }, timeout=60)
        if r.is_success or r.status_code == 200:
            print(f"API response: {r.text[:300]}")
            return True
        else:
            print(f"API error {r.status_code}: {r.text[:500]}")
            return False
    except Exception as e:
        print(f"HTTP error: {e}")
        return False


def apply_sql(sql: str, label: str, args: argparse.Namespace) -> bool:
    print(f"\n{'='*50}")
    print(f"Table: {label}")
    print(f"SQL size: {len(sql)} chars")
    print("-" * 40)
    print(sql[:2000] + ("..." if len(sql) > 2000 else ""))
    print("-" * 40)

    if not args.apply:
        print("\nDry run — use --apply to execute")
        return True

    # Method 1: try supabase-py (if it has .sql())
    supabase = get_service_client()
    if supabase is not None and hasattr(supabase, "sql"):
        try:
            supabase.sql(sql).execute()
            print(f"SUCCESS: {label} seed SQL applied to Supabase.")
            return True
        except Exception as e:
            print(f"supabase-py error: {e}")

    # Method 2: try REST API directly
    print("Trying direct REST API…")
    if exec_sql_via_api(sql):
        print(f"SUCCESS: {label} applied via REST API.")
        return True

    # Method 3: save to file for manual execution
    out_dir = Path(__file__).parent.parent / "supabase" / "_pending"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{label.replace(' ', '_').replace('(', '').replace(')', '')}.sql"
    out_path.write_text(sql)
    print(f"ERROR: Failed to apply {label}.")
    print(f"SQL saved to {out_path} — run manually in Supabase dashboard or via psql.")
    return False


def main():
    parser = argparse.ArgumentParser(description="Seed product catalogs")
    parser.add_argument("--table", choices=["cn", "uz", "v45", "lp", "v46", "v47", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "all"], default="cn", help="Which catalog/table to seed")
    parser.add_argument("--apply", action="store_true", help="Execute SQL on Supabase")
    parser.add_argument("--sql-only", action="store_true", help="Migration SQL only, skip seed data")
    args = parser.parse_args()

    tables = ["cn", "uz", "v45", "lp", "v46", "v47", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55"] if args.table == "all" else [args.table]

    for table in tables:
        path = SEED_FILES[table]
        if not path.exists():
            print(f"ERROR: Seed SQL not found at {path}")
            continue

        sql = path.read_text()

        if args.sql_only and table in SEED_DATA_COMMENTS:
            comment = SEED_DATA_COMMENTS[table]
            parts = sql.split(comment)
            sql = parts[0]

        ok = apply_sql(sql, f"{table} ({MIGRATION_COMMENTS[table]})", args)
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
