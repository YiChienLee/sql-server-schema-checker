import argparse
from checker.sp_checker import main as sp_main
from checker.view_checker import main as view_main
from checker.schema_checker import main as schema_main
from sync import object_sync

# Entry point of the CLI tool for comparison and sync operations
def main():
    parser = argparse.ArgumentParser(
        description="A unified tool for comparing and synchronizing SQL Server objects like views, stored procedures, and schemas.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Operation mode: compare or sync
    parser.add_argument(
        "--mode",
        required=True,
        choices=["sp", "view", "schema", "sync_sp", "sync_view"],
        help="Choose the task to perform:\n"
             "  - sp: Compare stored procedures\n"
             "  - view: Compare views\n"
             "  - schema: Compare table schemas\n"
             "  - sync_sp: Sync only stored procedures (auto-configured)\n"
             "  - sync_view: Sync only views (auto-configured)"
    )

    # Output options
    parser.add_argument("--output", help="Optional output filename")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Format of the output report")

    # Comparison-specific option
    parser.add_argument("--show-content", action="store_true", help="Show detailed content differences if applicable")

    # Sync option
    parser.add_argument("--allow-create-new", action="store_true", help="Create objects in target DBs if missing")

    args = parser.parse_args()

    # Sync mode routing
    if args.mode == "sync_sp":
        object_sync.run_mode("sp", args)
        return
    elif args.mode == "sync_view":
        object_sync.run_mode("view", args)
        return

    # Route execution based on selected mode
    if args.mode == "sp":
        sp_main(args)
    elif args.mode == "view":
        view_main(args)
    elif args.mode == "schema":
        schema_main(args)


if __name__ == "__main__":
    main()
