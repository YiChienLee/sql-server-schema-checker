import argparse
from core.sp_checker import main as sp_main
from core.view_checker import main as view_main
from core.schema_checker import main as schema_main
from core.view_sync import main as view_sync_main  # Added: view sync functionality

# Main entry point: dispatch to the appropriate comparison/sync module based on mode

def main():
    parser = argparse.ArgumentParser(description="Unified SQL Server Comparison Tool")

    # Required mode argument: supports sp/view/schema/sync-view
    parser.add_argument("--mode", required=True, choices=["sp", "view", "schema", "sync-view"], help="Comparison mode")

    # Optional: output file and format
    parser.add_argument("--output", required=False, help="Output filename (optional)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")

    # Optional: show detailed content differences (used for comparison modes)
    parser.add_argument("--show-content", action="store_true", help="Show content differences if applicable")

    # Optional: allow creation of new views that don't exist in target DBs
    parser.add_argument("--allow-create-new", action="store_true", help="Allow creating views that do not exist in the target DB")

    args = parser.parse_args()

    # Dispatch based on selected mode
    if args.mode == "sp":
        sp_main(args)  # Compare Stored Procedures
    elif args.mode == "view":
        view_main(args)  # Compare Views
    elif args.mode == "schema":
        schema_main(args)  # Compare Table Schemas
    elif args.mode == "sync-view":
        view_sync_main(args)  # Sync view definitions to other DBs using sp_helptext

if __name__ == "__main__":
    main()