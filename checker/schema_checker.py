"""
schema_checker.py

Compares table structures across multiple SQL Server databases (columns, PK, FK, indexes, triggers, UNIQUE).
Supports multiple target databases and outputs results to JSON, CSV, or console.
"""

import argparse
import asyncio
from collections import defaultdict
from datetime import datetime

from utils.db_reader import read_db_info, read_list_from_excel
from utils.result_writer import save_results
from checker.schema_utils import (
    fetch_schema_info, 
    compare_full_schema
)
from utils.config import DEFAULT_ACCOUNT_PATH, DEFAULT_TABLE_LIST

# Compare the schema of a target database
async def compare_target_schema(base_schema_data, target_db, tables_to_compare, base_db_name, show_trigger_content=False):
    try:
        target_schema_data = await fetch_schema_info(target_db, tables_to_compare)
        differences = defaultdict(dict)

        for table in tables_to_compare:
            diff = compare_full_schema(
                base_schema=base_schema_data,
                target_schema=target_schema_data,
                base_db=base_db_name,
                target_db=target_db["database"],
                table_name=table,
                show_trigger_content=show_trigger_content
            )
            if diff:
                differences[target_db["database"]][table] = diff

        return target_db["server"], differences
    except Exception as e:
        return target_db["server"], {target_db["database"]: {"[ERROR]": str(e)}}

# Async main workflow
async def main_async(args):
    print(f"Start Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

    base_db, target_dbs = read_db_info(DEFAULT_ACCOUNT_PATH)
    tables_to_compare = read_list_from_excel(DEFAULT_TABLE_LIST, column_name="Table Name")

    base_schema_data = await fetch_schema_info(base_db, tables_to_compare)

    tasks = [
        compare_target_schema(base_schema_data, target_db, tables_to_compare, base_db["database"], args.show_content)
        for target_db in target_dbs
    ]
    results = await asyncio.gather(*tasks)

    all_differences = defaultdict(lambda: defaultdict(dict))
    for server, db_diffs in results:
        all_differences[server].update(db_diffs)

    if args.output:
        save_results(all_differences, args.format, args.output)
    else:
        save_results(all_differences, "console", None)

    print(f"End Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

# CLI entry point
def main(args=None):
    parser = argparse.ArgumentParser(description="Compare SQL Server schema (columns, PK, FK, index, trigger)")
    parser.add_argument("--output", required=False, help="Output filename (optional)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--show-content", action="store_true", help="Show detailed trigger content diff")
    if args is None:
        args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
