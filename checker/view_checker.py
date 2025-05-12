"""
view_checker.py

Compares SQL Server View definitions and row counts.
Supports multiple target databases and outputs results as JSON, CSV, or to console.
"""

import pyodbc
import argparse
import asyncio
import difflib
from collections import defaultdict
from datetime import datetime

from utils.db_reader import read_db_info, read_list_from_excel
from utils.sql_cleaner import clean_definition_lines
from utils.result_writer import save_results
from utils.config import DEFAULT_ACCOUNT_PATH, DEFAULT_VIEW_LIST

# Retrieve View definitions from the database
def get_view_definitions(conn_str):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.name, m.definition
        FROM sys.sql_modules m
        JOIN sys.objects o ON m.object_id = o.object_id
        WHERE o.type = 'V'
    """)
    definitions = {row[0]: row[1].strip() if row[1] else None for row in cursor.fetchall()}
    conn.close()
    return definitions

def get_view_definitions_async(conn_str):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, get_view_definitions, conn_str)

# Retrieve View row count

def get_view_row_count(conn_str, view_name):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM [{view_name}]")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        return f"Error: {str(e)}"

def get_view_row_count_async(conn_str, view_name):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, get_view_row_count, conn_str, view_name)

# Compare view definitions between base and target
def compare_view_definitions(base_def, target_def, show_content=False):
    if base_def is None and target_def is None:
        return ["Missing in both databases"]
    elif base_def is None:
        return ["Missing in standard"]
    elif target_def is None:
        return ["Missing in target database"]
    else:
        base_lines = clean_definition_lines(base_def)
        target_lines = clean_definition_lines(target_def)
        if base_lines != target_lines:
            if show_content:
                diff = difflib.ndiff(base_lines, target_lines)
                diff_lines = [line for line in diff if line.startswith("- ") or line.startswith("+ ")]
                return ["Definition is different!", *diff_lines]
            else:
                return ["Definition is different!"]
    return []

# Compare definitions across all target databases
async def compare_view_definitions_across_targets(base_db, target_dbs, views_to_compare, show_content):
    base_conn_str = f"DRIVER={{SQL Server}};SERVER={base_db['server']};DATABASE={base_db['database']};UID={base_db['username']};PWD={base_db['password']}"
    base_defs = await get_view_definitions_async(base_conn_str)

    all_differences = defaultdict(lambda: defaultdict(dict))
    for target_db in target_dbs:
        target_conn_str = f"DRIVER={{SQL Server}};SERVER={target_db['server']};DATABASE={target_db['database']};UID={target_db['username']};PWD={target_db['password']}"
        target_defs = await get_view_definitions_async(target_conn_str)

        for view in views_to_compare:
            diffs = compare_view_definitions(base_defs.get(view), target_defs.get(view), show_content)
            if diffs:
                all_differences[target_db["server"]][target_db["database"]][f"[{view}]"] = diffs
    return all_differences

# Compare row counts between target and test environments
async def compare_view_row_counts(target_dbs, views_to_compare, to_test_server):
    differences = defaultdict(lambda: defaultdict(dict))

    for target_db in target_dbs:
        test_db = target_db.copy()
        test_db["server"] = to_test_server(target_db["server"])

        target_conn_str = f"DRIVER={{SQL Server}};SERVER={target_db['server']};DATABASE={target_db['database']};UID={target_db['username']};PWD={target_db['password']}"
        test_conn_str = f"DRIVER={{SQL Server}};SERVER={test_db['server']};DATABASE={test_db['database']};UID={test_db['username']};PWD={test_db['password']}"

        row_tasks = []
        for view in views_to_compare:
            row_tasks.append(get_view_row_count_async(target_conn_str, view))
            row_tasks.append(get_view_row_count_async(test_conn_str, view))

        row_results = await asyncio.gather(*row_tasks)

        for i, view in enumerate(views_to_compare):
            target_count = row_results[i * 2]
            test_count = row_results[i * 2 + 1]
            diffs = []
            if isinstance(target_count, int) and isinstance(test_count, int):
                if target_count != test_count:
                    diffs.append(f"Row count mismatch: Target={target_count}, Test={test_count}")
            else:
                diffs.append(f"Query error: Target={target_count}, Test={test_count}")
            if diffs:
                differences[target_db["server"]][target_db["database"]][f"[{view}]"] = diffs

    return differences

# Generate test server name (e.g., DB123 → DBTST123)
def to_test_server(server_name):
    import re
    return re.sub(r"(\D+)(\d+)", r"\1TST\2", server_name)

# Async main workflow
async def main_async(args):
    print(f"Start Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

    base_db, target_dbs = read_db_info(DEFAULT_ACCOUNT_PATH)
    views_to_compare = read_list_from_excel(DEFAULT_VIEW_LIST, column_name="View Name")

    def_task = compare_view_definitions_across_targets(base_db, target_dbs, views_to_compare, args.show_content)
    count_task = compare_view_row_counts(target_dbs, views_to_compare, to_test_server)
    all_definitions, all_counts = await asyncio.gather(def_task, count_task)

    all_differences = defaultdict(lambda: defaultdict(dict))
    for server, dbs in all_definitions.items():
        for db, content in dbs.items():
            all_differences[server][db].update(content)

    for server, dbs in all_counts.items():
        for db, content in dbs.items():
            for view_key, diff_list in content.items():
                if view_key in all_differences[server][db]:
                    all_differences[server][db][view_key].extend(diff_list)
                else:
                    all_differences[server][db][view_key] = diff_list

    if args.output:
        save_results(all_differences, args.format, args.output)
    else:
        save_results(all_differences, "console", None)

    print(f"End Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

# CLI entry point
def main(args=None):
    parser = argparse.ArgumentParser(description="Compare SQL Server View definitions and row counts")
    parser.add_argument("--output", required=False, help="Output filename (optional)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--show-content", action="store_true", help="Show detailed diff content")
    if args is None:
        args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
