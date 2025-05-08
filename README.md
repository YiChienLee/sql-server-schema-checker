# SQL Server Schema Checker

Compare SQL Server stored procedures, views, and table schemas across multiple databases.
Highlights differences in columns, indexes, triggers, PKs, FKs, and more.
Outputs results in JSON or CSV. Ideal for version control and cross-environment validation.

---

## Usage

### 1. Prepare Input Files

You will need the following input files:

* `Account.csv`: List of databases to compare. The first row is the standard, followed by targets.
* `SpList.csv`: List of stored procedures to compare.
* `ViewList.csv`: List of views to compare.
* `TableList.csv`: List of tables to compare.
* `SpList.xlsx`, `ViewList.xlsx`, `TableList.xlsx`: Lists of SPs, Views, and Tables to compare.

> Note: The first row of `Account.csv` is the **standard database**; all others are comparison targets.

### 2. Setup Environment

1. Install Python 3.x
2. Install required packages:

```bash
pip install -r requirements.txt
```

### 3. Edit Excel Configuration Files

* `Account.xlsx`: Input DB connection info (server, database, username, password)
* `TableList.xlsx`: List of tables to compare
* `ViewList.xlsx`: List of views to compare
* `SpList.xlsx`: List of stored procedures to compare

### 4. Switch to Project Directory

```bash
D:
cd D:\Yvette\DB_Diff
```

### 5. Run CLI Comparison

```bash
# Compare Stored Procedures
definitions
python main.py --mode sp --output sp_diff.json --format json --show-content

# Compare Views (definition and row count)
python main.py --mode view --output view_diff.json --format json --show-content

# Compare Table Schemas
python main.py --mode schema --output schema_diff.json --format json --show-content

# Sync View Definitions (from standard DB to all targets)
python main.py --mode sync-view --output sync_log.json --format json

# Sync View Definitions with new view creation enabled
python main.py --mode sync-view --output sync_log.json --format json --allow-create-new
```

---

## Features

* Compare stored procedure definitions (case-insensitive, whitespace/format tolerant)
* Compare view definitions and row count (includes test-server mapping logic)
* Compare table schema including:

  * Column properties (name, type, length, nullability, default value)
  * Primary Keys (PK)
  * Foreign Keys (FK)
  * Indexes (excluding PK & unique constraints)
  * Triggers (including optional diff view)
  * UNIQUE constraints
* Async execution powered by `asyncio` for fast, concurrent analysis
* Outputs to JSON, CSV, or prints to console
* Modular Python codebase: easy to maintain, extend, and test
* Sync view definitions from standard DB to all targets (preserves formatting with `sp_helptext`)
* Optionally create new views in targets using `--allow-create-new`
* Show error messages in red with `colorama` for better readability across platforms

---

## Project Structure

```
db_checker/
├── core/
│   ├── sp_checker.py
│   ├── view_checker.py
│   ├── schema_checker.py
│   ├── schema_utils.py
│   └── view_sync.py

├── utils/
│   ├── db_reader.py
│   ├── result_writer.py
│   └── sql_cleaner.py
├── main.py
├── requirements.txt
├── README.md
├── Account.csv
├── SpList.xlsx
├── ViewList.xlsx
└── TableList.xlsx
```

---

## Git Suggestions

To avoid committing local Excel or result JSON files to Git, you can run:

```bash
git update-index --skip-worktree Account.xlsx
git update-index --skip-worktree TableList.xlsx
git update-index --skip-worktree ViewList.xlsx
git update-index --skip-worktree SpList.xlsx
```

To resume tracking later:

```bash
git update-index --no-skip-worktree <filename>
```

---

## GitHub Topics

```
sql-server  schema-diff  database-tools  data-engineering
python  sql-comparison  devops  automation
```

---

## Author

Made with ❤️ by Yvette.Lee

---

## License

MIT License
