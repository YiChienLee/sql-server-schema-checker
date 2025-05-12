# SQL Server Schema Checker

Compare SQL Server stored procedures, views, and table schemas across multiple databases.
Highlights differences in columns, indexes, triggers, PKs, FKs, and more.
Outputs results in JSON or CSV. Ideal for version control and cross-environment validation.

---

## Usage

### 1. Prepare Input Files

Place the following files in the `data/` folder:

- `data/Account.xlsx`: List of database connections. The first row is the standard, followed by targets.
- `data/SpList.xlsx`: List of stored procedures to compare/sync.
- `data/ViewList.xlsx`: List of views to compare/sync.
- `data/TableList.xlsx`: List of tables to compare.

> The first row of `Account.xlsx` is the **standard database**; all others are comparison targets.

---

### 2. Setup Environment

🛠 If you encounter `No module named 'pip'` error, install pip manually:
```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

```bash
# Upgrade pip (if already installed)
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Edit Excel Configuration Files

- `data/Account.xlsx`: Columns should include `server`, `database`, `username`, `password`
- `data/TableList.xlsx`: List of full table names to compare
- `data/ViewList.xlsx`: List of view names to compare or sync
- `data/SpList.xlsx`: List of stored procedure names to compare or sync

---

### 4. Switch to Project Directory

```bash
cd path/to/your/project
```

---

### 5. Run CLI Comparison or Sync

```bash
# Compare Stored Procedure definitions
python main.py --mode sp --output sp_diff.json --format json --show-content

# Compare Views (definition and row count)
python main.py --mode view --output view_diff.json --format json --show-content

# Compare Table Schemas
python main.py --mode schema --output schema_diff.json --format json --show-content

# Sync Stored Procedures (auto-detects from SpList.xlsx)
python main.py --mode sync_sp --allow-create-new

# Sync Views (auto-detects from ViewList.xlsx)
python main.py --mode sync_view --allow-create-new
```

---

## Features

- Compare stored procedure definitions (case-insensitive, whitespace/format tolerant)
- Compare view definitions and row count (includes test-server mapping logic)
- Compare table schema including:
  - Column properties (name, type, length, nullability, default value)
  - Primary Keys (PK)
  - Foreign Keys (FK)
  - Indexes (excluding PK & unique constraints)
  - Triggers (including optional diff view)
  - UNIQUE constraints
- Async execution powered by `asyncio` for fast, concurrent analysis
- Outputs to JSON, CSV, or prints to console
- Modular Python codebase: easy to maintain, extend, and test
- Sync view and SP definitions from standard DB to all targets (preserves formatting with `sp_helptext`)
- Optionally create new objects in targets using `--allow-create-new`
- Show error messages in red with `colorama` for better readability across platforms

---

## Project Structure

```
your-project/
├── checker/
│   ├── sp_checker.py
│   ├── view_checker.py
│   ├── schema_checker.py
│   └── schema_utils.py
│
├── sync/
│   └── object_sync.py
│
├── utils/
│   ├── db_reader.py
│   ├── result_writer.py
│   └── sql_cleaner.py
│
├── data/
│   ├── Account.xlsx
│   ├── SpList.xlsx
│   ├── ViewList.xlsx
│   └── TableList.xlsx
│
├── main.py
├── requirements.txt
└── README.md
```

---

## Git Suggestions

To avoid committing local Excel or result JSON files to Git, you can run:

```bash
git update-index --skip-worktree data/Account.xlsx
git update-index --skip-worktree data/TableList.xlsx
git update-index --skip-worktree data/ViewList.xlsx
git update-index --skip-worktree data/SpList.xlsx
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

Made with by Yvette.Lee

---

## License

MIT License
