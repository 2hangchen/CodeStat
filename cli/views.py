"""Table, bar chart, and color rendering based on rich"""
import logging
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.bar import Bar
from rich import box

logger = logging.getLogger(__name__)

console = Console()


def format_percentage(value: float) -> str:
    """Format percentage with color markers"""
    if value >= 80:
        return f"[green]{value:.2f}%[/green]"
    elif value >= 50:
        return f"[yellow]{value:.2f}%[/yellow]"
    else:
        return f"[red]{value:.2f}%[/red]"


def display_service_status(status: Dict[str, Any]):
    """Display MCP service status"""
    table = Table(title="MCP Service Status", box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Item", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    table.add_row("Running Status", "✅ Running" if status["running"] else "❌ Not Running")
    if status["running"]:
        table.add_row("Process ID", str(status["pid"]))
    table.add_row("Listen Address", f"{status['host']}:{status['port']}")
    table.add_row("PID File", status["pid_file"])
    
    console.print(table)
    
    if status["running"]:
        # Test if service is accessible
        try:
            import requests
            response = requests.get(
                f"http://{status['host']}:{status['port']}/health",
                timeout=2
            )
            if response.status_code == 200:
                console.print("[green]✅ Service health check passed[/green]")
                health_data = response.json()
                console.print(f"[dim]Version: {health_data.get('version', 'unknown')}[/dim]")
            else:
                console.print(f"[yellow]⚠️  Service response abnormal: {response.status_code}[/yellow]")
        except ImportError:
            console.print("[yellow]⚠️  Cannot perform health check (requests library missing)[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Cannot connect to service: {e}[/red]")


def display_metrics_table(metrics: Dict[str, Any], title: str = "Metrics Statistics"):
    """
    Display metrics overview table
    
    Args:
        metrics: Metrics data
        title: Table title
    """
    table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Metric Name", style="cyan", no_wrap=True)
    table.add_column("Value", style="green", justify="right")
    
    table.add_row("AI Generated Lines", f"{metrics.get('ai_total_lines', 0)} lines")
    table.add_row("Adopted Lines", f"{metrics.get('adopted_lines', 0)} lines")
    table.add_row("Code Adoption Rate", format_percentage(metrics.get('adoption_rate', 0.0)))
    table.add_row("Code Generation Rate", format_percentage(metrics.get('generation_rate', 0.0)))
    
    if "file_count" in metrics:
        table.add_row("Files Involved", f"{metrics.get('file_count', 0)} files")
    
    if "session_count" in metrics:
        table.add_row("Sessions", f"{metrics.get('session_count', 0)} sessions")
    
    console.print(table)


def display_global_dashboard(metrics: Dict[str, Any]):
    """Display a concise global dashboard for all local data."""
    from rich.layout import Layout

    layout = Layout()
    layout.split_column(
        Layout(name="summary", size=8),
        Layout(name="details"),
    )

    # Top summary panel
    summary_table = Table(
        title="Global Summary",
        box=box.ROUNDED,
        show_header=False,
        header_style="bold magenta",
    )
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green", justify="right")

    summary_table.add_row("AI Generated Lines", f"{metrics.get('ai_total_lines', 0)}")
    summary_table.add_row("Adopted Lines", f"{metrics.get('adopted_lines', 0)}")
    summary_table.add_row(
        "Adoption Rate", format_percentage(metrics.get("adoption_rate", 0.0))
    )
    summary_table.add_row(
        "Generation Rate", format_percentage(metrics.get("generation_rate", 0.0))
    )
    summary_table.add_row(
        "Files Involved", str(metrics.get("file_count", 0))
    )
    summary_table.add_row(
        "Sessions", str(metrics.get("session_count", 0))
    )

    layout["summary"].update(summary_table)

    # Bottom: simple bar chart for quick visual
    bar_data = {
        "AI Lines": float(metrics.get("ai_total_lines", 0)),
        "Adopted": float(metrics.get("adopted_lines", 0)),
    }
    # Avoid all zeros
    bar_data = {k: v for k, v in bar_data.items() if v > 0}

    if bar_data:
        from rich.table import Table as RichTable

        max_value = max(bar_data.values())
        bar_table = RichTable(
            title="Adoption Overview",
            box=box.SIMPLE,
            show_header=False,
        )
        bar_table.add_column("Item", style="cyan")
        bar_table.add_column("Chart", style="blue")
        bar_table.add_column("Value", style="green", justify="right")

        for label, value in bar_data.items():
            length = int((value / max_value) * 40) if max_value > 0 else 0
            bar = "█" * length
            bar_table.add_row(label, bar, f"{int(value)}")

        layout["details"].update(bar_table)
    else:
        layout["details"].update(
            Panel("[yellow]No global data yet. Generate some AI code to see stats here.[/yellow]")
        )

    console.print(layout)


def display_session_info(summaries: List[Dict[str, Any]]):
    """Display session details"""
    if not summaries:
        return
    
    summary = summaries[0]  # Take first session info
    session_info = summary.get("session_info", "")
    create_time = summary.get("create_time", "")
    
    info_text = Text()
    if session_info:
        info_text.append("🤖 Agent Info: ", style="bold")
        info_text.append(f"{session_info}\n", style="cyan")
    if create_time:
        info_text.append("📅 Operation Time: ", style="bold")
        info_text.append(f"{create_time}\n", style="cyan")
    
    if info_text:
        panel = Panel(info_text, title="Session Details", border_style="blue")
        console.print(panel)


def display_diff_lines_table(diff_lines: List[Dict[str, Any]], limit: int = 20):
    """
    Display diff lines details table
    
    Args:
        diff_lines: Diff lines list
        limit: Display line limit
    """
    if not diff_lines:
        console.print("[yellow]No diff lines data[/yellow]")
        return
    
    table = Table(title=f"Diff Lines Details (showing first {min(limit, len(diff_lines))} lines)", box=box.ROUNDED)
    table.add_column("Diff Type", style="cyan", width=10)
    table.add_column("Line Number", style="green", justify="right", width=8)
    table.add_column("Code Content", style="white", overflow="fold")
    
    for diff_line in diff_lines[:limit]:
        diff_type = diff_line.get("diff_type", "")
        line_number = diff_line.get("line_number", "")
        line_content = diff_line.get("line_content", "")
        
        # Type color markers
        if diff_type == "add":
            type_style = "[green]add[/green]"
        elif diff_type == "modify":
            type_style = "[yellow]modify[/yellow]"
        else:
            type_style = diff_type
        
        table.add_row(type_style, str(line_number), line_content)
    
    console.print(table)
    
    if len(diff_lines) > limit:
        console.print(f"[dim]... {len(diff_lines) - limit} more lines not shown[/dim]")


def display_simple_bar_chart(data: Dict[str, float], title: str = "Metrics Comparison"):
    """
    Display simple bar chart
    
    Args:
        data: Data dictionary, keys are labels, values are numbers
        title: Chart title
    """
    if not data:
        console.print("[yellow]No data to display[/yellow]")
        return
    
    # Calculate max value for normalization
    max_value = max(data.values()) if data.values() else 1
    
    table = Table(title=title, box=box.SIMPLE)
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green", justify="right")
    table.add_column("Chart", style="blue")
    
    for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
        # Calculate bar length (assuming max width of 50)
        bar_length = int((value / max_value) * 50) if max_value > 0 else 0
        bar = "█" * bar_length
        table.add_row(label, f"{value:.2f}", bar)
    
    console.print(table)


def display_agent_comparison(metrics_list: List[Dict[str, Any]]):
    """
    Display cross-agent metrics comparison
    
    Args:
        metrics_list: Metrics list, each element contains session_id and metrics data
    """
    if not metrics_list:
        console.print("[yellow]No comparison data[/yellow]")
        return
    
    table = Table(title="Cross-Agent Metrics Comparison", box=box.ROUNDED)
    table.add_column("Session ID", style="cyan")
    table.add_column("AI Generated Lines", style="green", justify="right")
    table.add_column("Adopted Lines", style="green", justify="right")
    table.add_column("Adoption Rate", style="green", justify="right")
    table.add_column("Generation Rate", style="green", justify="right")
    
    for item in metrics_list:
        session_id = item.get("session_id", "unknown")
        metrics = item.get("metrics", {})
        
        table.add_row(
            session_id[:30] + "..." if len(session_id) > 30 else session_id,
            str(metrics.get("ai_total_lines", 0)),
            str(metrics.get("adopted_lines", 0)),
            format_percentage(metrics.get("adoption_rate", 0.0)),
            format_percentage(metrics.get("generation_rate", 0.0))
        )
    
    console.print(table)
