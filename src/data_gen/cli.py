"""CLI interface for generating OrchardIQ star-schema data and unstructured assets."""

import argparse
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import settings
from src.data_gen.generator import OrchardWarehouseGenerator
from src.data_gen.unstructured import generate_knowledge_base_docs, generate_support_tickets


console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OrchardIQ Synthetic Warehouse & Knowledge Base Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Volume scaling factor (1.0 = ~2M fact rows, 0.02 = fast test ~40k rows)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic pseudorandom seed",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Shortcut to run with scale 0.02 for fast testing",
    )
    parser.add_argument(
        "--warehouse-dir",
        type=str,
        default=str(settings.get_warehouse_path()),
        help="Directory to write warehouse Parquet datasets",
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default=str(settings.get_docs_path()),
        help="Directory to write knowledge base markdown docs",
    )
    parser.add_argument(
        "--unstructured-dir",
        type=str,
        default=str(settings.get_unstructured_path()),
        help="Directory to write synthetic support tickets",
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Generate only markdown documentation without warehouse facts",
    )

    args = parser.parse_args()
    scale = 0.02 if args.fast else args.scale
    warehouse_dir = Path(args.warehouse_dir)
    docs_dir = Path(args.docs_dir)
    unstructured_dir = Path(args.unstructured_dir)

    console.print(Panel.fit(
        f"[bold green]OrchardIQ Warehouse Data Generator[/bold green]\n"
        f"Scale Factor: [cyan]{scale}[/cyan] (Seed: [yellow]{args.seed}[/yellow])\n"
        f"Warehouse Path: [magenta]{warehouse_dir}[/magenta]\n"
        f"Docs Path: [magenta]{docs_dir}[/magenta]",
        title="OrchardIQ Data Engine",
    ))

    t0 = time.time()

    # 1. Generate Knowledge Base Docs
    console.print("\n[bold]1. Generating Knowledge Base Markdown Documentation...[/bold]")
    num_docs = generate_knowledge_base_docs(docs_dir)
    console.print(f"   [green][OK][/green] Generated [bold]{num_docs}[/bold] Markdown enterprise documents.")

    if args.docs_only:
        console.print(f"[bold green]Done in {time.time() - t0:.2f}s![/bold green]")
        return

    # 2. Generate Synthetic Support Tickets
    console.print("\n[bold]2. Generating Synthetic Customer Support Tickets (~5,000)...[/bold]")
    num_tickets = 5000 if scale >= 0.2 else 500
    ticket_path = generate_support_tickets(unstructured_dir, num_tickets=num_tickets, seed=args.seed)
    console.print(f"   [green][OK][/green] Generated [bold]{num_tickets}[/bold] support tickets at: [cyan]{ticket_path}[/cyan]")

    # 3. Generate Star-Schema Warehouse Tables
    console.print(f"\n[bold]3. Generating Star-Schema Warehouse Facts & Dimensions (Scale: {scale})...[/bold]")
    generator = OrchardWarehouseGenerator(warehouse_dir, seed=args.seed, scale=scale)
    table_counts = generator.generate_all()

    elapsed = time.time() - t0

    # Display Summary Table
    table = Table(title="Generated Warehouse Tables Summary", show_header=True, header_style="bold magenta")
    table.add_column("Table Name", style="cyan")
    table.add_column("Layer", style="green")
    table.add_column("Row Count", justify="right", style="yellow")
    table.add_column("Partitioning", style="white")

    total_facts = 0
    total_dims = 0

    for name, count in table_counts.items():
        is_fact = name.startswith("fact_")
        layer = "Mart / Fact" if is_fact else "Dimension"
        part = "year / month" if name in ["fact_sales", "fact_returns", "fact_support_claims", "fact_marketing_spend"] else "Single Dataset"
        table.add_row(name, layer, f"{count:,}", part)
        if is_fact:
            total_facts += count
        else:
            total_dims += count

    console.print(table)
    console.print(f"\n[bold green][OK] Warehouse generation complete in {elapsed:.2f} seconds![/bold green]")
    console.print(f"   Total Dimensions: [bold yellow]{total_dims:,}[/bold yellow] rows")
    console.print(f"   Total Facts: [bold yellow]{total_facts:,}[/bold yellow] rows")
    console.print(f"   Total Knowledge Docs: [bold yellow]{num_docs}[/bold yellow] markdown files")
    console.print(f"   Total Support Tickets: [bold yellow]{num_tickets:,}[/bold yellow] cases\n")


if __name__ == "__main__":
    main()
