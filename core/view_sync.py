import pyodbc
import asyncio
from collections import defaultdict
from datetime import datetime
import sys
from colorama import init, Fore, Style

init(autoreset=True)

from utils.db_reader import read_db_info, read_list_from_excel
from utils.result_writer import save_results

# Retrieve full view definition from base DB using sp_helptext (preserves formatting)
def get_view_definition_raw(conn, view_name):
    cursor = conn.cursor()
    cursor.execute(f"EXEC sp_helptext '{view_name}'")
    lines = [row[0] for row in cursor.fetchall()]
    return ''.join(lines)

# Check if a view exists in the target DB
def view_exists(conn, view_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT OBJECT_ID('{view_name}', 'V')")
    return cursor.fetchone()[0] is not None

# Apply view definition with conditional logic based on existence and user flag
def apply_view_definition(conn, view_name, definition, allow_create_new):
    cursor = conn.cursor()
    if view_exists(conn, view_name):
        drop_sql = f"DROP VIEW {view_name};"
        cursor.execute(drop_sql)
        cursor.execute(definition)
        conn.commit()
    else:
        if allow_create_new:
            print(f"[INFO] View '{view_name}' does not exist. Creating new.")
            cursor.execute(definition)
            conn.commit()
        else:
            raise Exception(f"View '{view_name}' does not exist in target DB and --allow-create-new is not set.")

# Build SQL Server connection string
def build_conn_str(info):
    return f"DRIVER={{SQL Server}};SERVER={info['server']};DATABASE={info['database']};UID={info['username']};PWD={info['password']}"

# Sync a single view to all target databases
async def sync_view_to_targets(base_db, target_dbs, view_name, allow_create_new):
    result = defaultdict(dict)

    # Fetch view definition from base DB
    base_conn = pyodbc.connect(build_conn_str(base_db))
    try:
        definition = get_view_definition_raw(base_conn, view_name)
    except Exception as e:
        for target in target_dbs:
            msg = f"Failed to get definition from base: {e}"
            print(f"{Fore.RED}[ERROR] {target['database']} - {view_name}: {msg}")
            result[target['database']][f"[{view_name}]"] = [msg]
        return result
    base_conn.close()

    # Apply definition to each target DB
    for target in target_dbs:
        try:
            with pyodbc.connect(build_conn_str(target)) as conn:
                apply_view_definition(conn, view_name, definition, allow_create_new)
            result[target['database']][f"[{view_name}]"] = ["Sync successful"]
        except Exception as e:
            msg = f"Sync failed: {e}"
            print(f"{Fore.RED}[ERROR] {target['database']} - {view_name}: {msg}")
            result[target['database']][f"[{view_name}]"] = [msg]

    return result

# Async entry point for syncing all views
async def main_async(args):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f"Start Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

    # Load DB connection info and view list
    base_db, target_dbs = read_db_info("Account.xlsx")
    views = read_list_from_excel("ViewList.xlsx", column_name="View Name")

    # Launch parallel sync tasks for each view
    tasks = [sync_view_to_targets(base_db, target_dbs, view, args.allow_create_new) for view in views]
    all_results_nested = await asyncio.gather(*tasks)

    # Aggregate results
    final_result = defaultdict(lambda: defaultdict(dict))
    for view_result in all_results_nested:
        for db, content in view_result.items():
            final_result[base_db['server']][db].update(content)

    # Output results
    if args.output:
        save_results(final_result, args.format, args.output)
    else:
        save_results(final_result, "console", None)

    print(f"End Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

# CLI entry point
def main(args=None):
    import argparse
    parser = argparse.ArgumentParser(description="Sync SQL Server View definitions to multiple databases")
    parser.add_argument("--output", required=False, help="Output filename (optional)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--allow-create-new", action="store_true", help="Allow creating views that do not exist in the target DB")
    if args is None:
        args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
