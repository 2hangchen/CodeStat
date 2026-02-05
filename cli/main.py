"""CLI entry point, parses command line arguments"""
import argparse
import sys
import logging
from pathlib import Path

# Add project root to Python path to ensure modules can be imported
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config import get_cli_config
from logging_config import setup_logging
from storage.db import get_db
from cli.menus import (
    show_main_menu,
    query_by_session,
    query_by_file,
    query_by_project,
    compare_agents,
    manage_data,
    manage_service,
    show_global_dashboard,
)
from cli.views import console
from cli.exporter import export_metrics
from compute.metrics_service import calculate_session_metrics, calculate_file_metrics, calculate_project_metrics
import questionary

logger = setup_logging(log_level="INFO", module_name="cli")


def print_banner():
    """Minimal banner (kept for future extension, currently no-op)."""
    # Intentionally kept very light; main layout is handled in the menu.
    console.print()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Local MCP AI Code Statistics Tool CLI")
    parser.add_argument(
        "--session",
        type=str,
        help="Query by session ID (quick command)"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Query by file path (quick command)"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Query by project root directory (quick command)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export format (json/csv), must be used with --session/--file/--project"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Export file path, must be used with --export"
    )
    parser.add_argument(
        "--start-service",
        action="store_true",
        help="Start MCP service (background)"
    )
    parser.add_argument(
        "--stop-service",
        action="store_true",
        help="Stop MCP service"
    )
    parser.add_argument(
        "--service-status",
        action="store_true",
        help="Check MCP service status"
    )
    
    args = parser.parse_args()
    
    # Initialize database
    try:
        db = get_db()
        db.initialize()
    except Exception as e:
        console.print(f"[red]❌ Database initialization failed: {e}[/red]")
        sys.exit(1)
    
    # Handle service management commands
    if args.start_service:
        from service_manager import get_service_manager
        manager = get_service_manager()
        if manager.start(background=True):
            console.print("[green]✅ MCP service started successfully[/green]")
        else:
            console.print("[red]❌ Failed to start MCP service[/red]")
        return
    
    if args.stop_service:
        from service_manager import get_service_manager
        manager = get_service_manager()
        if manager.stop():
            console.print("[green]✅ MCP service stopped[/green]")
        else:
            console.print("[yellow]⚠️  MCP service is not running or failed to stop[/yellow]")
        return
    
    if args.service_status:
        from service_manager import get_service_manager
        from cli.views import display_service_status
        manager = get_service_manager()
        status = manager.get_status()
        display_service_status(status)
        return
    
    # Quick command mode
    if args.session:
        try:
            metrics = calculate_session_metrics(args.session)
            from cli.views import display_metrics_table, display_session_info
            if metrics.get("summaries"):
                display_session_info(metrics["summaries"])
            display_metrics_table(metrics)
            
            if args.export and args.output:
                export_metrics(metrics, args.output, args.export)
                console.print(f"[green]✅ Data exported to: {args.output}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Query failed: {e}[/red]")
            sys.exit(1)
        return
    
    if args.file:
        try:
            metrics = calculate_file_metrics(args.file)
            from cli.views import display_metrics_table
            display_metrics_table(metrics)
            
            if args.export and args.output:
                export_metrics(metrics, args.output, args.export)
                console.print(f"[green]✅ Data exported to: {args.output}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Query failed: {e}[/red]")
            sys.exit(1)
        return
    
    if args.project:
        try:
            metrics = calculate_project_metrics(args.project)
            from cli.views import display_metrics_table
            display_metrics_table(metrics)
            
            if args.export and args.output:
                export_metrics(metrics, args.output, args.export)
                console.print(f"[green]✅ Data exported to: {args.output}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Query failed: {e}[/red]")
            sys.exit(1)
        return
    
    # Interactive menu mode
    print_banner()
    
    while True:
        try:
            choice = show_main_menu()
            
            if choice == "exit":
                console.print("\n[green]👋 Exiting tool, data is safely stored locally~[/green]")
                break
            elif choice == "overview":
                show_global_dashboard()
            elif choice == "file":
                query_by_file()
            elif choice == "session":
                query_by_session()
            elif choice == "project":
                query_by_project()
            elif choice == "compare":
                compare_agents()
            elif choice == "export":
                # Export functionality is integrated in query functions
                console.print("[yellow]Please select export option when querying[/yellow]")
            elif choice == "service":
                manage_service()
            elif choice == "manage":
                manage_data()
            
            # Ask if continue
            if choice != "exit":
                continue_choice = questionary.confirm("Continue querying?").ask()
                if not continue_choice:
                    console.print("\n[green]👋 Exiting tool, data is safely stored locally~[/green]")
                    break
                print()  # Empty line separator
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error occurred: {e}[/red]")
            logger.error(f"CLI error: {e}", exc_info=True)
            continue_choice = questionary.confirm("Continue?").ask()
            if not continue_choice:
                break


if __name__ == "__main__":
    main()
