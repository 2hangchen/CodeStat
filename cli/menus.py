"""Interactive main menu and sub-menus based on questionary"""
import logging
import questionary
from typing import Optional, List, Dict, Any
from compute.metrics_service import (
    calculate_session_metrics,
    calculate_file_metrics,
    calculate_project_metrics,
    calculate_global_metrics,
)
from storage.models import get_session_summaries
from cli.views import (
    display_metrics_table,
    display_session_info,
    display_diff_lines_table,
    display_agent_comparison,
    display_global_dashboard,
)
from cli.exporter import export_metrics

logger = logging.getLogger(__name__)


def _arrow_menu(title: str, choices: List[Dict[str, Any]]) -> Optional[str]:
    """
    Simple arrow-key menu implemented with prompt_toolkit.
    Each choice is a dict: {"label": str, "value": str}.
    Returns selected value or None if cancelled / unsupported.
    """
    try:
        from prompt_toolkit import Application
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import HSplit, Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style
    except ImportError:
        return None

    current_index = {"value": 0}

    def get_menu_text():
        fragments = [("class:title", title + "\n\n")]
        for idx, item in enumerate(choices):
            is_current = idx == current_index["value"]
            prefix = "➤ " if is_current else "  "
            style = "class:selected" if is_current else "class:item"
            fragments.append((style, f"{prefix}{item['label']}\n"))
        return fragments

    text_control = FormattedTextControl(get_menu_text)
    root_container = HSplit([Window(content=text_control, dont_extend_height=True)])
    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _up(event):
        if current_index["value"] > 0:
            current_index["value"] -= 1

    @kb.add("down")
    @kb.add("j")
    def _down(event):
        if current_index["value"] < len(choices) - 1:
            current_index["value"] += 1

    @kb.add("enter")
    def _enter(event):
        value = choices[current_index["value"]]["value"]
        event.app.exit(result=value)

    @kb.add("c-c")
    @kb.add("q")
    def _cancel(event):
        event.app.exit(result=None)

    style = Style.from_dict(
        {
            "title": "bold cyan",
            "item": "",
            "selected": "reverse bold",
        }
    )

    app = Application(
        layout=Layout(root_container),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    try:
        return app.run()
    except Exception:
        return None


def show_main_menu() -> str:
    """Show main menu; prefer custom arrow-key navigation, fallback to numeric input."""
    from service_manager import get_service_manager
    from cli.views import console

    manager = get_service_manager()
    from config import get_server_config

    console.print()
    # Title line
    console.print("[bold cyan]CodeStat - AI Code Metrics[/bold cyan]")

    # MCP server status (small text)
    server_config = get_server_config()
    if manager.is_running():
        status = manager.get_status()
        console.print(
            f"[dim]MCP Server[/dim] [green]● ONLINE[/green] "
            f"[dim]at[/dim] [cyan]http://{status['host']}:{status['port']}[/cyan]"
        )
    else:
        console.print(
            f"[dim]MCP Server[/dim] [red]● OFFLINE[/red] "
            f"[dim]at[/dim] http://{server_config['host']}:{server_config['port']}"
        )

    # Repo / author info (even smaller / dimmer)
    console.print(
        "[grey50]Repo: https://github.com/2hangchen/CodeStat  Author: 2hangchen[/grey50]"
    )
    console.print("\n[dim]Use ↑/↓ to move, Enter to confirm:[/dim]\n")

    # Preferred: custom arrow-key navigation via prompt_toolkit
    menu_items: List[Dict[str, Any]] = [
        {"label": "📈 Global Dashboard (All Data)", "value": "overview"},
        {"label": "🔧 MCP Service Management", "value": "service"},
        {"label": "📄 Query Metrics by File", "value": "file"},
        {"label": "📋 Query Metrics by Session", "value": "session"},
        {"label": "📊 Query Metrics by Project", "value": "project"},
        {"label": "🆚 Compare Agents", "value": "compare"},
        {"label": "📤 Export Data", "value": "export"},
        {"label": "🧹 Data Management (Cleanup/Backup)", "value": "manage"},
        {"label": "❌ Exit", "value": "exit"},
    ]

    selected = _arrow_menu("Select operation:", menu_items)
    if selected:
        return selected

    # Fallback: numeric input menu when arrow menu is not available
    console.print("[yellow]⚠ Arrow-key menu not fully supported, fallback to numeric menu.[/yellow]")
    console.print("  [bold magenta]1[/bold magenta]  📈 Global Dashboard (All Data)")
    console.print("  [bold magenta]2[/bold magenta]  🔧 MCP Service Management")
    console.print("  [bold magenta]3[/bold magenta]  📄 Query Metrics by File")
    console.print("  [bold magenta]4[/bold magenta]  📋 Query Metrics by Session")
    console.print("  [bold magenta]5[/bold magenta]  📊 Query Metrics by Project")
    console.print("  [bold magenta]6[/bold magenta]  🆚 Compare Agents")
    console.print("  [bold magenta]7[/bold magenta]  📤 Export Data")
    console.print("  [bold magenta]8[/bold magenta]  🧹 Data Management (Cleanup/Backup)")
    console.print("  [bold magenta]0[/bold magenta]  ❌ Exit")

    mapping = {
        "1": "overview",
        "2": "service",
        "3": "file",
        "4": "session",
        "5": "project",
        "6": "compare",
        "7": "export",
        "8": "manage",
        "0": "exit",
    }

    try:
        raw = input("> ").strip()
    except EOFError:
        return "exit"
    return mapping.get(raw, "exit")


def query_by_session():
    """Query metrics by session"""
    session_id = questionary.text(
        "Enter session ID (or 'all' to view all sessions):"
    ).ask()
    
    if not session_id:
        return
    
    if session_id.lower() == "all":
        # Show all session list
        summaries = get_session_summaries()
        if not summaries:
            print("No session data available")
            return
        
        session_ids = list(set(s["session_id"] for s in summaries))
        selected = questionary.select(
            "Please select a session:",
            choices=session_ids
        ).ask()
        
        if selected:
            session_id = selected
        else:
            return
    
    print(f"\nQuerying session: {session_id}")
    print("Calculating metrics (LCS comparison in progress...)")
    
    try:
        metrics = calculate_session_metrics(session_id)
        
        # Display session info
        if metrics.get("summaries"):
            display_session_info(metrics["summaries"])
        
        # Display metrics table
        display_metrics_table(metrics, "Session Metrics (Precise LCS Calculation)")
        
        # Display diff lines details
        diff_lines = metrics.get("diff_lines", [])
        if diff_lines:
            show_details = questionary.confirm("Show diff lines details?").ask()
            if show_details:
                display_diff_lines_table(diff_lines)
        
        # Ask if export
        export_choice = questionary.confirm("Export this session's metrics?").ask()
        if export_choice:
            format_choice = questionary.select(
                "Select export format:",
                choices=["JSON", "CSV"]
            ).ask()
            
            if format_choice:
                output_path = questionary.text(
                    f"Enter export file path (default: session_{session_id}.{format_choice.lower()}):"
                ).ask()
                
                if not output_path:
                    output_path = f"session_{session_id}.{format_choice.lower()}"
                
                export_metrics(metrics, output_path, format_choice.lower())
                print(f"✅ Data exported to: {output_path}")
    
    except Exception as e:
        print(f"❌ Query failed: {e}")
        logger.error(f"Query by session failed: {e}", exc_info=True)


def query_by_file():
    """Query metrics by file"""
    file_path = questionary.text("Enter file path:").ask()
    
    if not file_path:
        return
    
    print(f"\nQuerying file: {file_path}")
    print("Calculating metrics (LCS comparison in progress...)")
    
    try:
        metrics = calculate_file_metrics(file_path)
        
        # Display metrics table
        display_metrics_table(metrics, "File Metrics")
        
        # Display diff lines details
        diff_lines = metrics.get("diff_lines", [])
        if diff_lines:
            show_details = questionary.confirm("Show diff lines details?").ask()
            if show_details:
                display_diff_lines_table(diff_lines)
        
        # Ask if export
        export_choice = questionary.confirm("Export this file's metrics?").ask()
        if export_choice:
            format_choice = questionary.select(
                "Select export format:",
                choices=["JSON", "CSV"]
            ).ask()
            
            if format_choice:
                import os
                safe_filename = os.path.basename(file_path).replace(".", "_")
                output_path = questionary.text(
                    f"Enter export file path (default: file_{safe_filename}.{format_choice.lower()}):"
                ).ask()
                
                if not output_path:
                    output_path = f"file_{safe_filename}.{format_choice.lower()}"
                
                export_metrics(metrics, output_path, format_choice.lower())
                print(f"✅ Data exported to: {output_path}")
    
    except Exception as e:
        print(f"❌ Query failed: {e}")
        logger.error(f"Query by file failed: {e}", exc_info=True)


def query_by_project():
    """Query metrics by project"""
    project_root = questionary.text("Enter project root directory path:").ask()
    
    if not project_root:
        return
    
    print(f"\nQuerying project: {project_root}")
    print("Calculating metrics (LCS comparison in progress...)")
    
    try:
        metrics = calculate_project_metrics(project_root)
        
        # Display metrics table
        display_metrics_table(metrics, "Project Metrics")
        
        # Ask if export
        export_choice = questionary.confirm("Export this project's metrics?").ask()
        if export_choice:
            format_choice = questionary.select(
                "Select export format:",
                choices=["JSON", "CSV"]
            ).ask()
            
            if format_choice:
                import os
                safe_dirname = os.path.basename(project_root).replace(".", "_")
                output_path = questionary.text(
                    f"Enter export file path (default: project_{safe_dirname}.{format_choice.lower()}):"
                ).ask()
                
                if not output_path:
                    output_path = f"project_{safe_dirname}.{format_choice.lower()}"
                
                export_metrics(metrics, output_path, format_choice.lower())
                print(f"✅ Data exported to: {output_path}")
    
    except Exception as e:
        print(f"❌ Query failed: {e}")
        logger.error(f"Query by project failed: {e}", exc_info=True)


def compare_agents():
    """Compare metrics across agents"""
    summaries = get_session_summaries()
    if not summaries:
        print("No session data available")
        return
    
    # Get all session IDs
    session_ids = list(set(s["session_id"] for s in summaries))
    
    if len(session_ids) < 2:
        print("At least 2 sessions are required for comparison")
        return
    
    # Let user select sessions to compare
    selected = questionary.checkbox(
        "Select sessions to compare (at least 2):",
        choices=session_ids
    ).ask()
    
    if not selected or len(selected) < 2:
        return
    
    print("\nCalculating metrics (LCS comparison in progress...)")
    
    try:
        metrics_list = []
        for session_id in selected:
            metrics = calculate_session_metrics(session_id)
            metrics_list.append({
                "session_id": session_id,
                "metrics": metrics
            })
        
        # Display comparison table
        display_agent_comparison(metrics_list)
    
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        logger.error(f"Compare agents failed: {e}", exc_info=True)


def show_global_dashboard():
    """Show global dashboard for all local data."""
    try:
        metrics = calculate_global_metrics()
        display_global_dashboard(metrics)
    except Exception as e:
        print(f"❌ Failed to load global dashboard: {e}")
        logger.error(f"Global dashboard failed: {e}", exc_info=True)


def manage_service():
    """MCP service management menu (uses custom arrow-key menu)."""
    from service_manager import get_service_manager
    from rich.console import Console

    console = Console()
    manager = get_service_manager()

    menu_items: List[Dict[str, Any]] = [
        {"label": "▶️  Start MCP Service", "value": "start"},
        {"label": "⏹️  Stop MCP Service", "value": "stop"},
        {"label": "🔄 Restart MCP Service", "value": "restart"},
        {"label": "📊 View Service Status", "value": "status"},
        {"label": "🔙 Back to Main Menu", "value": "back"},
    ]

    choice = _arrow_menu("Please select service management operation:", menu_items)
    if not choice:
        # Fallback to simple text input if arrow menu not available
        console.print("[yellow]⚠ Arrow-key menu not fully supported, fallback to numeric menu.[/yellow]")
        console.print("  [bold magenta]1[/bold magenta]  ▶️  Start MCP Service")
        console.print("  [bold magenta]2[/bold magenta]  ⏹️  Stop MCP Service")
        console.print("  [bold magenta]3[/bold magenta]  🔄 Restart MCP Service")
        console.print("  [bold magenta]4[/bold magenta]  📊 View Service Status")
        console.print("  [bold magenta]0[/bold magenta]  🔙 Back to Main Menu")

        mapping = {
            "1": "start",
            "2": "stop",
            "3": "restart",
            "4": "status",
            "0": "back",
        }
        try:
            raw = input("> ").strip()
        except EOFError:
            return
        choice = mapping.get(raw, "back")

    if choice == "start":
        if manager.is_running():
            console.print("[yellow]⚠️  Service is already running[/yellow]")
        else:
            console.print("[cyan]Starting MCP service...[/cyan]")
            if manager.start(background=True):
                console.print("[green]✅ MCP service started successfully[/green]")
            else:
                console.print("[red]❌ Failed to start MCP service[/red]")
    
    elif choice == "stop":
        if not manager.is_running():
            console.print("[yellow]⚠️  Service is not running[/yellow]")
        else:
            console.print("[cyan]Stopping MCP service...[/cyan]")
            if manager.stop():
                console.print("[green]✅ MCP service stopped[/green]")
            else:
                console.print("[red]❌ Failed to stop MCP service[/red]")
    
    elif choice == "restart":
        console.print("[cyan]Restarting MCP service...[/cyan]")
        if manager.restart():
            console.print("[green]✅ MCP service restarted successfully[/green]")
        else:
            console.print("[red]❌ Failed to restart MCP service[/red]")
    
    elif choice == "status":
        status = manager.get_status()
        from cli.views import display_service_status
        display_service_status(status)
    
    elif choice == "back":
        return


def manage_data():
    """Data management menu"""
    from storage.backup import backup_database, get_backup_records, restore_database
    from storage.models import delete_sessions
    from utils.time_utils import get_current_time, get_time_range_days
    from config import get_database_config
    
    choice = questionary.select(
        "Please select data management operation:",
        choices=[
            questionary.Choice("📦 Backup Data", "backup"),
            questionary.Choice("📥 Restore Data", "restore"),
            questionary.Choice("📋 View Backup Records", "list_backups"),
            questionary.Choice("🧹 Clean Expired Data", "clean"),
            questionary.Choice("🔙 Back to Main Menu", "back"),
        ]
    ).ask()
    
    if choice == "backup":
        output_path = questionary.text("Enter backup file path (leave empty for default path):").ask()
        backup_path = backup_database(output_path if output_path else None)
        if backup_path:
            print(f"✅ Backup successful: {backup_path}")
        else:
            print("❌ Backup failed")
    
    elif choice == "restore":
        backup_path = questionary.text("Enter backup file path:").ask()
        if backup_path:
            confirm = questionary.confirm("Restore will overwrite existing data. Continue?").ask()
            if confirm:
                if restore_database(backup_path):
                    print("✅ Restore successful")
                else:
                    print("❌ Restore failed")
    
    elif choice == "list_backups":
        limit = questionary.text("Number of records to display (default 10):").ask()
        limit = int(limit) if limit and limit.isdigit() else 10
        backups = get_backup_records(limit)
        if backups:
            from rich.table import Table
            from rich.console import Console
            console = Console()
            table = Table(title="Backup Records")
            table.add_column("ID", style="cyan")
            table.add_column("Backup Path", style="green")
            table.add_column("Backup Time", style="yellow")
            table.add_column("Size (KB)", style="blue", justify="right")
            for backup in backups:
                table.add_row(
                    str(backup["id"]),
                    backup["backup_path"],
                    backup["backup_time"],
                    str(backup["backup_size"])
                )
            console.print(table)
        else:
            print("No backup records available")
    
    elif choice == "clean":
        config = get_database_config()
        clean_cycle = config.get("clean_cycle", 30)
        days = questionary.text(f"Clean data older than how many days (default {clean_cycle} days):").ask()
        days = int(days) if days and days.isdigit() else clean_cycle
        
        confirm = questionary.confirm(f"Confirm deletion of all data older than {days} days?").ask()
        if confirm:
            _, before_time = get_time_range_days(days)
            deleted = delete_sessions(before_time=before_time)
            print(f"✅ Deleted {deleted} session records")
    
    elif choice == "back":
        return
