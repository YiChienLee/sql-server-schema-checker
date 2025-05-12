"""
schema_utils.py

封裝與 SQL Server schema 結構相關的查詢與比對工具。
包含欄位、PK、FK、Index、Trigger、Unique constraint 等比對。
"""

import pyodbc
import asyncio
import re
import difflib
from collections import defaultdict
from utils.sql_cleaner import clean_definition_lines


# ---------- 資料查詢區 ----------

def build_conn_str(db: dict) -> str:
    return f"DRIVER={{SQL Server}};SERVER={db['server']};DATABASE={db['database']};UID={db['username']};PWD={db['password']}"

def query_db(conn_str, query):
    with pyodbc.connect(conn_str, timeout=10) as conn:
        return conn.cursor().execute(query).fetchall()

def get_schemas(conn_str):
    result = defaultdict(list)
    rows = query_db(conn_str, """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE,
               COALESCE(CHARACTER_MAXIMUM_LENGTH, 0), IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
    """)
    for row in rows:
        result[row[0]].append(row[1:])
    return result

def get_primary_keys(conn_str, tables):
    result = defaultdict(set)
    if not tables:
        return result
    table_str = ", ".join(f"'{t}'" for t in tables)
    rows = query_db(conn_str, f"""
        SELECT TABLE_NAME, COLUMN_NAME 
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_NAME IN ({table_str})
    """)
    for row in rows:
        result[row[0]].add(row[1])
    return result

def get_foreign_keys(conn_str, tables):
    result = defaultdict(set)
    if not tables:
        return result
    table_str = ", ".join(f"'{t}'" for t in tables)
    rows = query_db(conn_str, f"""
        SELECT tc.TABLE_NAME, kcu.COLUMN_NAME, ccu.TABLE_NAME, ccu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu ON tc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
        WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
        AND tc.TABLE_NAME IN ({table_str})
    """)
    for row in rows:
        result[row[0]].add((row[1], row[2], row[3]))
    return result

def get_indexes(conn_str, tables):
    result = defaultdict(set)
    if not tables:
        return result
    table_str = ", ".join(f"'{t}'" for t in tables)
    rows = query_db(conn_str, f"""
        SELECT t.name, ind.name, col.name
        FROM sys.indexes ind
        JOIN sys.index_columns ic ON ind.object_id = ic.object_id AND ind.index_id = ic.index_id
        JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
        JOIN sys.tables t ON ind.object_id = t.object_id
        WHERE t.name IN ({table_str})
        AND ind.is_primary_key = 0 AND ind.is_unique_constraint = 0
    """)
    for row in rows:
        result[row[0]].add((row[1], row[2]))
    return result

def get_triggers(conn_str, tables):
    result = defaultdict(dict)
    if not tables:
        return result
    table_str = ", ".join(f"'{t}'" for t in tables)
    rows = query_db(conn_str, f"""
        SELECT trg.name, tbl.name, m.definition,
               CASE WHEN trg.is_instead_of_trigger = 1 THEN 'INSTEAD OF' ELSE 'AFTER' END,
               STUFF((SELECT '/' + TE.type_desc
                      FROM sys.trigger_events TE
                      WHERE TE.object_id = trg.object_id
                      FOR XML PATH('')), 1, 1, '')
        FROM sys.triggers trg
        JOIN sys.tables tbl ON trg.parent_id = tbl.object_id
        JOIN sys.sql_modules m ON trg.object_id = m.object_id
        WHERE tbl.name IN ({table_str})
    """)
    for name, table, definition, trig_type, event in rows:
        result[table][name] = {
            "definition": definition or "",
            "type": trig_type,
            "event": event
        }
    return result

def get_unique_constraints(conn_str, tables):
    result = defaultdict(set)
    if not tables:
        return result
    table_str = ", ".join(f"'{t}'" for t in tables)
    rows = query_db(conn_str, f"""
        SELECT tc.TABLE_NAME, kcu.COLUMN_NAME, tc.CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        WHERE tc.CONSTRAINT_TYPE = 'UNIQUE'
        AND tc.TABLE_NAME IN ({table_str})
    """)
    for row in rows:
        result[row[0]].add((row[2], row[1]))
    return result


# ---------- 非同步 fetch 全部結構 ----------

async def fetch_schema_info(db: dict, tables: list[str]):
    conn_str = build_conn_str(db)
    loop = asyncio.get_running_loop()
    return await asyncio.gather(
        loop.run_in_executor(None, get_schemas, conn_str),
        loop.run_in_executor(None, get_primary_keys, conn_str, tables),
        loop.run_in_executor(None, get_foreign_keys, conn_str, tables),
        loop.run_in_executor(None, get_indexes, conn_str, tables),
        loop.run_in_executor(None, get_triggers, conn_str, tables),
        loop.run_in_executor(None, get_unique_constraints, conn_str, tables)
    )


# ---------- 比對邏輯 ----------

def normalize_default(value):
    if value is None:
        return "NULL"
    value = str(value).strip().upper()
    while re.match(r"^\(\(.*\)\)$", value):
        value = value[1:-1]
    return value

def compare_triggers(base_trigs, target_trigs, show_content):
    result = {}
    all_names = set(base_trigs.keys()).union(target_trigs.keys())
    for name in all_names:
        b = base_trigs.get(name)
        t = target_trigs.get(name)
        if b is None:
            result[name] = "Missing in standard"
        elif t is None:
            result[name] = "Missing in target"
        else:
            if b["type"] != t["type"] or b["event"] != t["event"]:
                result[name] = "Trigger metadata differs"
            else:
                base_lines = clean_definition_lines(b["definition"])
                target_lines = clean_definition_lines(t["definition"])
                if base_lines != target_lines:
                    if show_content:
                        diff = difflib.ndiff(base_lines, target_lines)
                        diff_lines = [line for line in diff if line.startswith("- ") or line.startswith("+ ")]
                        result[name] = ["Definition differs"] + diff_lines
                    else:
                        result[name] = "Definition differs"
    return result

def compare_full_schema(base_schema, target_schema, base_db, target_db, table_name, show_trigger_content=False):
    b_schemas, b_pks, b_fks, b_indexes, b_trigs, b_uniques = base_schema
    t_schemas, t_pks, t_fks, t_indexes, t_trigs, t_uniques = target_schema

    diff = {}

    # 欄位結構
    b_cols = {c[0]: c for c in b_schemas.get(table_name, [])}
    t_cols = {c[0]: c for c in t_schemas.get(table_name, [])}
    all_cols = set(b_cols.keys()).union(t_cols.keys())

    for col in all_cols:
        if col not in b_cols:
            diff[col] = "Missing in standard"
        elif col not in t_cols:
            diff[col] = "Missing in target"
        else:
            b_type, b_len, b_null, b_def = b_cols[col][1:]
            t_type, t_len, t_null, t_def = t_cols[col][1:]
            messages = []
            if b_type.lower() != t_type.lower():
                messages.append(f"Type: {b_type} vs {t_type}")
            if b_len != t_len:
                messages.append(f"Length: {b_len} vs {t_len}")
            if b_null != t_null:
                messages.append(f"Nullable: {b_null} vs {t_null}")
            if normalize_default(b_def) != normalize_default(t_def):
                messages.append(f"Default: {b_def} vs {t_def}")
            if messages:
                diff[col] = "; ".join(messages)

    # PK
    if b_pks.get(table_name, set()) != t_pks.get(table_name, set()):
        diff["Primary Key"] = f"{sorted(b_pks.get(table_name, set()))} vs {sorted(t_pks.get(table_name, set()))}"

    # FK
    if b_fks.get(table_name, set()) != t_fks.get(table_name, set()):
        diff["Foreign Key"] = f"{sorted(b_fks.get(table_name, set()))} vs {sorted(t_fks.get(table_name, set()))}"

    # Index
    if b_indexes.get(table_name, set()) != t_indexes.get(table_name, set()):
        diff["Index"] = f"{sorted(b_indexes.get(table_name, set()))} vs {sorted(t_indexes.get(table_name, set()))}"

    # Trigger
    trig_diff = compare_triggers(b_trigs.get(table_name, {}), t_trigs.get(table_name, {}), show_trigger_content)
    if trig_diff:
        diff["Trigger"] = trig_diff

    # Unique Constraint
    if b_uniques.get(table_name, set()) != t_uniques.get(table_name, set()):
        diff["Unique"] = f"{sorted(b_uniques.get(table_name, set()))} vs {sorted(t_uniques.get(table_name, set()))}"

    return diff if diff else None
