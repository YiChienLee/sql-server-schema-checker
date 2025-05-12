"""
sp_checker.py

Compares stored procedure definitions across SQL Server databases.
Supports multiple target databases, shows content diffs, and outputs to JSON/CSV.
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
from utils.config import DEFAULT_ACCOUNT_PATH, DEFAULT_SP_LIST

# Retrieve all stored procedure definitions from a database
def get_sp_definitions(conn_str):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.name, m.definition
        FROM sys.sql_modules m
        JOIN sys.objects o ON m.object_id = o.object_id
        WHERE o.type = 'P'
    """)
    definitions = {row[0]: row[1].strip() if row[1] else None for row in cursor.fetchall()}
    conn.close()
    return definitions

# Wrap in asynchronous execution
def get_sp_definitions_async(conn_str):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, get_sp_definitions, conn_str)

# Compare stored procedure definitions (optionally show content differences)
def compare_definitions(base_def, target_def, base_db, target_db, sp_name, show_content):
    differences = defaultdict(dict)

    if base_def is None and target_def is None:
        differences[target_db][f"[{sp_name}]"] = ["Missing in both databases"]
    elif base_def is None:
        differences[target_db][f"[{sp_name}]"] = ["Missing in standard"]
    elif target_def is None:
        differences[target_db][f"[{sp_name}]"] = ["Missing in target database"]
    else:
        base_lines = clean_definition_lines(base_def)
        target_lines = clean_definition_lines(target_def)

        if base_lines != target_lines:
            if show_content:
                diff = difflib.ndiff(base_lines, target_lines)
                diff_lines = [line for line in diff if line.startswith("- ") or line.startswith("+ ")]
                differences[target_db][f"[{sp_name}]"] = ["Definition is different!", *diff_lines]
            else:
                differences[target_db][f"[{sp_name}]"] = ["Definition is different!"]

    return differences if differences else None

# Compare stored procedures for one target database
async def compare_sp_definitions(base_db, target_db, sp_list, show_content):
    base_conn_str = f"DRIVER={{SQL Server}};SERVER={base_db['server']};DATABASE={base_db['database']};UID={base_db['username']};PWD={base_db['password']}"
    target_conn_str = f"DRIVER={{SQL Server}};SERVER={target_db['server']};DATABASE={target_db['database']};UID={target_db['username']};PWD={target_db['password']}"

    base_defs, target_defs = await asyncio.gather(
        get_sp_definitions_async(base_conn_str),
        get_sp_definitions_async(target_conn_str)
    )

    base_keys = {k.lower(): k for k in base_defs}
    target_keys = {k.lower(): k for k in target_defs}

    result = defaultdict(dict)
    for sp in sp_list:
        key_lower = sp.lower()
        base_key = base_keys.get(key_lower)
        target_key = target_keys.get(key_lower)
        base_def = base_defs.get(base_key)
        target_def = target_defs.get(target_key)

        messages = []
        if base_key != sp or target_key != sp:
            messages.append(f"Warning: Case mismatch for SP '{sp}' → Base='{base_key}', Target='{target_key}'")

        diff = compare_definitions(base_def, target_def, base_db["database"], target_db["database"], sp, show_content)

        if diff:
            for db, d in diff.items():
                for name, msg in d.items():
                    result[db][name] = messages + msg
        elif messages:
            result[target_db["database"]][f"[{sp}]"] = messages

    return target_db["server"], result

# Async entry point
async def main_async(args):
    print(f"Start Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

    base_db, target_dbs = read_db_info(DEFAULT_ACCOUNT_PATH)
    sp_list = read_list_from_excel(DEFAULT_SP_LIST, column_name="SP Name")

    tasks = [
        compare_sp_definitions(base_db, target_db, sp_list, args.show_content)
        for target_db in target_dbs
    ]
    all_results = await asyncio.gather(*tasks)

    final_diff = defaultdict(lambda: defaultdict(dict))
    for server, db_diff in all_results:
        for dbname, data in db_diff.items():
            final_diff[server][dbname].update(data)

    if args.output:
        save_results(final_diff, args.format, args.output)
    else:
        save_results(final_diff, "console", None)

    print(f"End Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

# CLI entry point
def main(args=None):
    parser = argparse.ArgumentParser(description="Compare SQL Server Stored Procedure definitions")
    parser.add_argument("--output", required=False, help="Output filename (optional)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--show-content", action="store_true", help="Show detailed diff content")
    if args is None:
        args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
