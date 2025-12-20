"""Versioning commands for COS CLI"""

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
def versioning():
    """Manage bucket versioning."""
    pass


@versioning.command("get")
@click.argument("cos_uri")
@click.pass_context
def get_versioning(ctx, cos_uri):
    """
    Get bucket versioning status.

    \b
    Examples:
      cos versioning get cos://bucket
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
        
        # Get versioning status
        response = cos_client.get_bucket_versioning()
        
        # Display status
        status = response.get("Status", "Disabled")
        if status == "Enabled":
            console.print(f"[green]Versioning is ENABLED for {bucket}[/green]")
        elif status == "Suspended":
            console.print(f"[yellow]Versioning is SUSPENDED for {bucket}[/yellow]")
        else:
            console.print(f"[dim]Versioning is DISABLED for {bucket}[/dim]")
        
        success_message("Retrieved versioning status")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@versioning.command("enable")
@click.argument("cos_uri")
@click.pass_context
def enable_versioning(ctx, cos_uri):
    """
    Enable bucket versioning.

    \b
    Examples:
      cos versioning enable cos://bucket
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
        
        # Enable versioning
        cos_client.put_bucket_versioning("Enabled")
        
        success_message(f"Enabled versioning for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@versioning.command("suspend")
@click.argument("cos_uri")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def suspend_versioning(ctx, cos_uri, yes):
    """
    Suspend bucket versioning.

    \b
    Examples:
      cos versioning suspend cos://bucket
      cos versioning suspend cos://bucket --yes
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Confirmation
        if not yes:
            if not click.confirm(f"Suspend versioning for {bucket}? (existing versions will be kept)"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Suspend versioning
        cos_client.put_bucket_versioning("Suspended")
        
        success_message(f"Suspended versioning for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
