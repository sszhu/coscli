"""Lifecycle management commands for COS CLI"""

import json
import click
from rich.console import Console

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import (
    parse_cos_uri,
    success_message,
    error_message,
)
from ..exceptions import COSError

console = Console()


@click.group()
def lifecycle():
    """Manage bucket lifecycle configuration."""
    pass


@lifecycle.command("get")
@click.argument("cos_uri")
@click.pass_context
def get_lifecycle(ctx, cos_uri):
    """
    Get bucket lifecycle configuration.

    \b
    Examples:
      cos lifecycle get cos://bucket
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Get lifecycle configuration
        response = cos_client.get_bucket_lifecycle()
        
        # Format and display
        output_format = ctx.obj.get("output", "json")
        if output_format == "json":
            console.print_json(json.dumps(response, indent=2))
        else:
            # Display in readable format
            rules = response.get("Rule", [])
            if not rules:
                console.print("[yellow]No lifecycle rules configured[/yellow]")
            else:
                console.print(f"[bold]Lifecycle Rules for {bucket}:[/bold]\n")
                for i, rule in enumerate(rules, 1):
                    console.print(f"[cyan]Rule {i}:[/cyan]")
                    console.print(f"  ID: {rule.get('ID', 'N/A')}")
                    console.print(f"  Status: {rule.get('Status', 'N/A')}")
                    console.print(f"  Filter: {rule.get('Filter', {})}")
                    
                    # Display transitions
                    transitions = rule.get('Transition', [])
                    if not isinstance(transitions, list):
                        transitions = [transitions]
                    for trans in transitions:
                        console.print(f"  Transition: {trans}")
                    
                    # Display expiration
                    expiration = rule.get('Expiration', {})
                    if expiration:
                        console.print(f"  Expiration: {expiration}")
                    console.print()
        
        success_message("Retrieved lifecycle configuration")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@lifecycle.command("put")
@click.argument("cos_uri")
@click.option("--config", "-c", "config_file", required=True, type=click.Path(exists=True),
              help="JSON file with lifecycle configuration")
@click.pass_context
def put_lifecycle(ctx, cos_uri, config_file):
    """
    Set bucket lifecycle configuration.

    \b
    Examples:
      cos lifecycle put cos://bucket --config lifecycle.json
    
    \b
    Example lifecycle.json:
      {
        "Rule": [
          {
            "ID": "Delete old files",
            "Status": "Enabled",
            "Filter": {"Prefix": "logs/"},
            "Expiration": {"Days": 30}
          }
        ]
      }
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Load configuration from file
        with open(config_file, 'r') as f:
            lifecycle_config = json.load(f)
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Set lifecycle configuration
        cos_client.put_bucket_lifecycle(lifecycle_config)
        
        success_message(f"Set lifecycle configuration for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@lifecycle.command("delete")
@click.argument("cos_uri")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_lifecycle(ctx, cos_uri, yes):
    """
    Delete bucket lifecycle configuration.

    \b
    Examples:
      cos lifecycle delete cos://bucket
      cos lifecycle delete cos://bucket --yes
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Confirmation
        if not yes:
            if not click.confirm(f"Delete lifecycle configuration for {bucket}?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Delete lifecycle configuration
        cos_client.delete_bucket_lifecycle()
        
        success_message(f"Deleted lifecycle configuration for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
