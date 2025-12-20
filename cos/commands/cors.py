"""CORS configuration commands for COS CLI"""

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
def cors():
    """Manage bucket CORS configuration."""
    pass


@cors.command("get")
@click.argument("cos_uri")
@click.pass_context
def get_cors(ctx, cos_uri):
    """
    Get bucket CORS configuration.

    \b
    Examples:
      cos cors get cos://bucket
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
        
        # Get CORS configuration
        response = cos_client.get_bucket_cors()
        
        # Format and display
        output_format = ctx.obj.get("output", "json")
        if output_format == "json":
            console.print_json(json.dumps(response, indent=2))
        else:
            # Display in readable format
            rules = response.get("CORSRule", [])
            if not rules:
                console.print("[yellow]No CORS rules configured[/yellow]")
            else:
                console.print(f"[bold]CORS Rules for {bucket}:[/bold]\n")
                for i, rule in enumerate(rules, 1):
                    console.print(f"[cyan]Rule {i}:[/cyan]")
                    console.print(f"  ID: {rule.get('ID', 'N/A')}")
                    console.print(f"  Allowed Origins: {rule.get('AllowedOrigin', [])}")
                    console.print(f"  Allowed Methods: {rule.get('AllowedMethod', [])}")
                    console.print(f"  Allowed Headers: {rule.get('AllowedHeader', [])}")
                    console.print(f"  Expose Headers: {rule.get('ExposeHeader', [])}")
                    console.print(f"  Max Age: {rule.get('MaxAgeSeconds', 'N/A')}")
                    console.print()
        
        success_message("Retrieved CORS configuration")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@cors.command("put")
@click.argument("cos_uri")
@click.option("--config", "-c", "config_file", required=True, type=click.Path(exists=True),
              help="JSON file with CORS configuration")
@click.pass_context
def put_cors(ctx, cos_uri, config_file):
    """
    Set bucket CORS configuration.

    \b
    Examples:
      cos cors put cos://bucket --config cors.json
    
    \b
    Example cors.json:
      {
        "CORSRule": [
          {
            "ID": "Allow all",
            "AllowedOrigin": ["*"],
            "AllowedMethod": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedHeader": ["*"],
            "ExposeHeader": ["ETag", "Content-Length"],
            "MaxAgeSeconds": 3600
          }
        ]
      }
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Load configuration from file
        with open(config_file, 'r') as f:
            cors_config = json.load(f)
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Set CORS configuration
        cos_client.put_bucket_cors(cors_config)
        
        success_message(f"Set CORS configuration for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@cors.command("delete")
@click.argument("cos_uri")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_cors(ctx, cos_uri, yes):
    """
    Delete bucket CORS configuration.

    \b
    Examples:
      cos cors delete cos://bucket
      cos cors delete cos://bucket --yes
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Confirmation
        if not yes:
            if not click.confirm(f"Delete CORS configuration for {bucket}?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Delete CORS configuration
        cos_client.delete_bucket_cors()
        
        success_message(f"Deleted CORS configuration for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
