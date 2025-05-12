import pyodbc
import asyncio
from collections import defaultdict
from datetime import datetime
import sys
from colorama import init, Fore

# Step 1: Initialize color output for better visibility in terminal
init(autoreset=True)

from utils.db_reader import read_db_info, read_list_from_excel
from utils.result_writer import save_results
from utils.config import DEFAULT_ACCOUNT_PATH, DEFAULT_VIEW_LIST, DEFAULT_SP_LIST

# Step 5: Build connection string for pyodbc from a dictionary
def build_conn_str(info):
    return f"DRIVER={{SQL Server}};SERVER={info['server']};DATABASE={info['database']};UID={info['username']};PWD={info['password']}"

# Step 6: Retrieve object definition (View or SP) using sp_helptext to preserve formatting
def get_object_definition_raw(conn, object_name, object_type):
    cursor = conn.cursor()
    cursor.execute(f"EXEC sp_helptext '{object_name}'")
    rows = cursor.fetchall()
    return ''.join(row[0] for row in rows) if rows else None

# Step 8: Determine whether the object exists in the target DB
def object_exists(conn, object_name, object_type):
    cursor = conn.cursor()
    type_code = {'view': 'V', 'sp': 'P'}[object_type]
    cursor.execute("SELECT OBJECT_ID(?, ?)", (object_name, type_code))
    return cursor.fetchone()[0] is not None

# Step 7: Create or replace an object in the target DB
def apply_object_definition(conn, object_name, definition, object_type, allow_create_new):
    cursor = conn.cursor()
    drop_type = {"sp": "PROCEDURE", "view": "VIEW"}[object_type]

    if object_exists(conn, object_name, object_type):
        print(f"[INFO] Replacing existing {object_type}: {object_name}")
        cursor.execute(f"DROP {drop_type} {object_name};")
        cursor.execute(definition)
        conn.commit()
    elif allow_create_new:
        print(f"[INFO] Creating new {object_type}: {object_name}")
        cursor.execute(definition)
        conn.commit()
    else:
        raise Exception(f"{object_type.title()} '{object_name}' does not exist and --allow-create-new not set.")

# Step 4: Synchronize a single object from base DB to all target DBs
async def sync_object_to_targets(base_db, target_dbs, object_name, object_type, allow_create_new):
    result = defaultdict(dict)
    try:
        with pyodbc.connect(build_conn_str(base_db)) as base_conn:
            definition = get_object_definition_raw(base_conn, object_name, object_type)
            if not definition:
                raise ValueError("Definition is empty or not found.")
    except Exception as e:
        msg = f"Failed to get definition from base: {e}"
        for target in target_dbs:
            print(f"{Fore.RED}[ERROR] {target['database']} - {object_name}: {msg}")
            result[target['database']][f"[{object_name}]"] = [msg]
        return result

    for target in target_dbs:
        try:
            with pyodbc.connect(build_conn_str(target)) as conn:
                apply_object_definition(conn, object_name, definition, object_type, allow_create_new)
            result[target['database']][f"[{object_name}]"] = ["Sync successful"]
        except Exception as e:
            msg = f"Sync failed: {e}"
            print(f"{Fore.RED}[ERROR] {target['database']} - {object_name}: {msg}")
            result[target['database']][f"[{object_name}]"] = [msg]

    return result

# Step 3: Main logic to sync all specified object types in parallel
async def main_async(args):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f"Start Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

    # Step 3.1: Read DB connection info
    base_db, target_dbs = read_db_info(args.account)
    final_result = defaultdict(lambda: defaultdict(dict))

    # Step 3.2: Loop through selected object types
    for object_type in args.target:
        object_list = read_list_from_excel(args.input, column_name=f"{object_type.title()} Name")
        tasks = [sync_object_to_targets(base_db, target_dbs, obj, object_type, args.allow_create_new) for obj in object_list]
        sync_results = await asyncio.gather(*tasks)

        for result in sync_results:
            for db, content in result.items():
                final_result[base_db['server']][db].update(content)

    # Step 3.3: Save or print result
    if args.output:
        save_results(final_result, args.format, args.output)
    else:
        save_results(final_result, "console", None)

    print(f"End Time: {datetime.now():%Y-%m-%d %H:%M:%S}")

# Step 2: Callable entry point (for main.py integration)
def run(args):
    asyncio.run(main_async(args))

# Step 2.1: Handle simplified sync mode
def run_mode(mode: str, args):
    args.account = DEFAULT_ACCOUNT_PATH
    args.input = DEFAULT_SP_LIST if mode == "sp" else DEFAULT_VIEW_LIST
    args.target = [mode]
    run(args)
