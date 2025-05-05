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

### 2. Run CLI Comparison

```bash
# Compare Stored Procedures
definitions
python main.py --mode sp --output sp_diff.json --format json --show-content

# Compare Views (definition and row count)
python main.py --mode view --output view_diff.csv --format csv

# Compare Table Schemas
python main.py --mode schema --output schema_diff.json --format json --show-content
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

---

## Project Structure

```
db_checker/
├── core/
│   ├── sp_checker.py
│   ├── view_checker.py
│   ├── schema_checker.py
│   └── schema_utils.py
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
