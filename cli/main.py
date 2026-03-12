"""CLI interface for the Agent Orchestrator — Rich-based interactive terminal."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich import box

from config.settings import settings
from agents.orchestrator import OrchestratorAgent


console = Console()

BANNER = r"""
    _                    _    ___           _               _             _
   / \   __ _  ___ _ __ | |_ / _ \ _ __ ___| |__   ___  ___| |_ _ __ __ _| |_ ___  _ __
  / _ \ / _` |/ _ \ '_ \| __| | | | '__/ __| '_ \ / _ \/ __| __| '__/ _` | __/ _ \| '__|
 / ___ \ (_| |  __/ | | | |_| |_| | | | (__| | | |  __/\__ \ |_| | | (_| | || (_) | |
/_/   \_\__, |\___|_| |_|\__|\___/|_|  \___|_| |_|\___||___/\__|_|  \__,_|\__\___/|_|
        |___/
"""

HELP_TEXT = """
**Available Commands:**
- Type any request in natural language to route it to specialist agents
- `/agents` — List all available specialist agents
- `/preview <request>` — Preview which agents would handle your request
- `/help` — Show this help message
- `/clear` — Clear the screen
- `/quit` or `/exit` — Exit the application
"""


def display_banner() -> None:
    """Show the startup banner."""
    console.print(Text(BANNER, style="bold cyan"))
    console.print(
        Panel(
            "[bold]Multi-Agent Orchestrator[/bold] — Master-Slave Architecture\n"
            "Powered by GitHub Copilot via GitHub Models API\n"
            "Type [bold green]/help[/bold green] for commands or enter a request.",
            title="🤖 Agent Orchestrator v1.0",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )
    console.print()


def display_agents(orchestrator: OrchestratorAgent) -> None:
    """Display a table of all available agents."""
    table = Table(title="🤖 Available Specialist Agents", box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="bold", width=3)
    table.add_column("Agent", style="bold green", width=18)
    table.add_column("Description", style="white")

    for i, agent in enumerate(orchestrator.list_agents(), 1):
        table.add_row(str(i), agent["name"], agent["description"])

    console.print(table)
    console.print()


def display_routing_preview(routing: dict) -> None:
    """Show which agents the orchestrator would select."""
    console.print(Panel(
        routing.get("analysis", "N/A"),
        title="🧭 Routing Analysis",
        border_style="yellow",
    ))
    assignments = routing.get("assignments", [])
    if assignments:
        table = Table(box=box.SIMPLE, border_style="yellow")
        table.add_column("Priority", style="bold", width=8)
        table.add_column("Agent", style="bold green", width=18)
        table.add_column("Task", style="white")
        for a in assignments:
            table.add_row(str(a.get("priority", "?")), a.get("agent_id", "?"), a.get("task", "?"))
        console.print(table)
    console.print()


def display_results(state: dict) -> None:
    """Display the orchestrator's results with Rich formatting."""
    routing = state.get("routing_decision", {})
    results = state.get("agent_results", [])

    # Show orchestrator analysis
    console.print(Panel(
        routing.get("analysis", "N/A"),
        title="🧭 Orchestrator Analysis",
        border_style="cyan",
    ))

    # Show each agent's output
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        border = "green" if result["status"] == "success" else "red"

        # Task description panel
        console.print(Panel(
            Markdown(result["task_description"]),
            title=f"📋 {result['agent_name']} — Task Description",
            border_style="yellow",
            box=box.ROUNDED,
        ))

        # Result panel
        console.print(Panel(
            Markdown(result["result"]),
            title=f"{status_icon} {result['agent_name']} Agent — Result",
            border_style=border,
            box=box.DOUBLE,
        ))
        console.print()


def run_interactive() -> None:
    """Main interactive REPL loop."""
    display_banner()

    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        console.print(Panel(
            f"[bold red]Configuration Error[/bold red]\n\n{str(e)}\n\n"
            "1. Copy `.env.example` to `.env`\n"
            "2. Set your `GITHUB_TOKEN` in the `.env` file\n"
            "3. Get a token at: https://github.com/settings/tokens",
            title="⚠️  Setup Required",
            border_style="red",
        ))
        sys.exit(1)

    # Initialize orchestrator
    with console.status("[bold cyan]Initializing agents...", spinner="dots"):
        orchestrator = OrchestratorAgent()

    console.print("[green]✓ All 9 specialist agents initialized and ready.[/green]\n")

    # REPL
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]>[/bold cyan]").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ("/quit", "/exit"):
                console.print("[yellow]Goodbye! 👋[/yellow]")
                break

            if user_input.lower() == "/help":
                console.print(Markdown(HELP_TEXT))
                continue

            if user_input.lower() == "/agents":
                display_agents(orchestrator)
                continue

            if user_input.lower() == "/clear":
                console.clear()
                display_banner()
                continue

            if user_input.lower().startswith("/preview "):
                request = user_input[9:].strip()
                if request:
                    with console.status("[bold yellow]Analyzing request...", spinner="dots"):
                        routing = orchestrator.get_routing_preview(request)
                    display_routing_preview(routing)
                else:
                    console.print("[red]Usage: /preview <your request>[/red]")
                continue

            # Process request through orchestrator
            console.print()
            with console.status(
                "[bold cyan]🤖 Orchestrator is processing your request...",
                spinner="dots",
            ):
                state = orchestrator.invoke(user_input)

            display_results(state)

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit to exit.[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
            if settings.verbose:
                console.print_exception()


def main() -> None:
    """Entry point for the CLI."""
    run_interactive()


if __name__ == "__main__":
    main()
