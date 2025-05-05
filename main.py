"""
main.py

Unified CLI entry point for running different types of SQL Server structure comparisons:
- sp: Stored Procedures
- view: Views
- schema: Table Schemas
"""

import argparse
from core.sp_checker import main as sp_main
from core.view_checker import main as view_main
from core.schema_checker import main as schema_main

def main():
    parser = argparse.ArgumentParser(description="Unified SQL Server Comparison Tool")
    parser.add_argument("--mode", required=True, choices=["sp", "view", "schema"], help="Comparison mode")
    parser.add_argument("--output", required=False, help="Output filename (optional)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--show-content", action="store_true", help="Show content differences if applicable")
    args = parser.parse_args()

    # Pass parsed arguments to the corresponding comparison module
    if args.mode == "sp":
        sp_main(args)
    elif args.mode == "view":
        view_main(args)
    elif args.mode == "schema":
        schema_main(args)

if __name__ == "__main__":
    main()
