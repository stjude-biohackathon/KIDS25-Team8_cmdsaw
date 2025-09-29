#!/usr/bin/env python3
"""
FlowGen CLI - Generate WDL tasks from command-line help text
"""
import click
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .runner import run_help, discover_subcoms
from .parser import build_prompt, call_model, validate_json
from .translator import json_to_wdl, json_to_nextflow

console = Console()


@click.group()
def cli():
    """FlowGen CLI - Generate WDL / NEXTFLOW tasks from command-line help text"""
    pass


@cli.command()
@click.argument('executable')
@click.option('--discover-subcommands', is_flag=True, 
              help='Discover and process subcommands')
@click.option('--format', 'output_format', default='wdl', 
              type=click.Choice(['wdl', 'nextflow']),
              help='Output format (currently only WDL supported)')
@click.option('--help-text', default=None,
              help='Path to help text file (for testing)')
@click.option('--outdir', default='./output', 
              help='Output directory')
@click.option('--skip-validation', is_flag=True,
              help='Skip JSON validation')
def generate(executable, discover_subcommands, output_format, help_text, outdir, skip_validation):
    """Generate WDL tasks from executable help text"""
    
    if output_format not in ['wdl', 'nextflow']:
        raise click.ClickException("Only WDL and Nextflow formats are currently supported")

    # Create output directory
    output_path = Path(outdir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if help_text:
        # Load help text from file
        help_file = Path(help_text)
        if not help_file.is_file():
            raise click.ClickException(f"Help text file not found: {help_text}")
        with open(help_file, 'r') as f:
            help_text_content = f.read()
        version = None  # Version unknown when using static help text
    else:
        # Get main help
        console.print(f"[blue]Running[/blue] [bold]{executable} --help[/bold]...")
        help_text_content, version = run_help(executable)
        console.print(f"[green]Detected version:[/green] {version or '[dim]unknown[/dim]'}")

        # write help_text to a file
        help_file = output_path / f"{executable}_help.txt"
        with open(help_file, 'w') as f:
            f.write(help_text_content)
        console.print(f"[dim]Saved help text to[/dim] {help_file}")
    
    commands_to_process = []
    
    if discover_subcommands:
        console.print("[blue]Discovering subcommands...[/blue]")
        subcommands = discover_subcoms(help_text)
        
        if subcommands:
            # Create a nice table for subcommands
            table = Table(title="Found Subcommands", show_header=True, header_style="bold magenta")
            table.add_column("Command", style="cyan")
            for subcmd in subcommands:
                table.add_row(subcmd)
            console.print(table)
        else:
            console.print("[yellow]No subcommands found[/yellow]")
        
        for subcmd in subcommands:
            try:
                subcmd_help, _ = run_help(executable, [subcmd])
                commands_to_process.append({
                    'name': subcmd,
                    'help_text': subcmd_help,
                    'is_subcommand': True
                })
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not get help for [bold]{subcmd}[/bold]: {e}")
    else:
        commands_to_process.append({
            'name': executable,
            'help_text': help_text_content,
            'is_subcommand': False
        })

    # Process each command
    for cmd_info in commands_to_process:
        console.print(f"\n[blue]Processing[/blue] [bold cyan]{cmd_info['name']}[/bold cyan]...")
        
        # Build prompt and call model
        prompt = build_prompt(cmd_info['help_text'], executable, version)
        
        try:
            with console.status(f"[green]Calling LLM for {cmd_info['name']}. Check  [bold]{output_path}/llama_response.json[/bold] for streaming json build.", spinner="dots"):
                json_response = call_model(prompt)
            
            if not skip_validation:
                with console.status("[bold green]Validating JSON response...", spinner="dots"):
                    validate_json(json_response)
            
            # Generate WDL
            if output_format == 'wdl':
            
                # Create output directory structure
                tool_dir = output_path / f"{executable}_WDL"
                tool_dir.mkdir(parents=True, exist_ok=True)

                json_file = tool_dir / f"{cmd_info['name']}.json"
                with open(json_file, 'w') as f:
                    f.write(json_response)
                
                wdl_success = json_to_wdl(json_response, tool_dir)
                if wdl_success:
                    console.print(f"[green]Success![/green] WDL tasks generated in [bold]{tool_dir}[/bold]")
                else:
                    console.print(f"[red]Failed[/red] to generate WDL tasks for [bold]{cmd_info['name']}[/bold]")
                
                
            elif output_format == 'nextflow':

                # Create output directory structure
                tool_dir = output_path / f"{executable}_NEXTFLOW"
                tool_dir.mkdir(parents=True, exist_ok=True)

                json_file = tool_dir / f"{cmd_info['name']}.json"
                with open(json_file, 'w') as f:
                    f.write(json_response)
                    
                nextflow_success = json_to_nextflow(json_response, tool_dir)
                if nextflow_success:
                    console.print(f"[green]Success![/green] Nextflow workflow generated in [bold]{output_path}[/bold]")
                else:
                    console.print(f"[red]Failed[/red] to generate Nextflow workflow for [bold]{cmd_info['name']}[/bold]")
            
        except Exception as e:
            console.print(f"[red]Error[/red] processing [bold]{cmd_info['name']}[/bold]: {e}")

    # Final summary
    console.print(f"\n[green]Processing complete![/green]")


if __name__ == '__main__':
    cli()