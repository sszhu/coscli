"""Configure command for COS CLI"""

import click
from rich.prompt import Prompt

from ..config import ConfigManager
from ..utils import success_message, info_message, output_table


@click.group(name="configure", invoke_without_command=True)
@click.option("--profile", default="default", help="Profile name")
@click.pass_context
def configure(ctx, profile):
    """Configure COS CLI settings"""
    # If no subcommand is provided, run interactive setup
    if ctx.invoked_subcommand is None:
        ctx.invoke(interactive, profile=profile)


@configure.command(name="interactive")
@click.option("--profile", default="default", help="Profile name")
@click.pass_context
def interactive(ctx, profile):
    """Interactive configuration setup"""
    config_manager = ConfigManager(profile)
    
    info_message(f"Configuring profile: {profile}")
    
    # Get current values
    current_secret_id = config_manager.get_credential_value("secret_id") or ""
    current_region = config_manager.get_region()
    current_output = config_manager.get_output_format()
    
    # Prompt for values
    secret_id = Prompt.ask(
        "Secret ID",
        default=current_secret_id[:10] + "..." if current_secret_id else None
    )
    if secret_id and not secret_id.endswith("..."):
        config_manager.set_credential_value("secret_id", secret_id)
    
    secret_key = Prompt.ask("Secret Key", password=True)
    if secret_key:
        config_manager.set_credential_value("secret_key", secret_key)
    
    assume_role = Prompt.ask(
        "Assume Role ARN",
        default=config_manager.get_credential_value("assume_role") or ""
    )
    if assume_role:
        config_manager.set_credential_value("assume_role", assume_role)
    
    region = Prompt.ask("Default region", default=current_region)
    config_manager.set_config_value("region", region)
    
    bucket = Prompt.ask(
        "Default bucket",
        default=config_manager.get_bucket() or ""
    )
    if bucket:
        config_manager.set_config_value("bucket", bucket)
    
    prefix = Prompt.ask(
        "Default prefix",
        default=config_manager.get_prefix() or ""
    )
    if prefix:
        config_manager.set_config_value("prefix", prefix)
    
    output_format = Prompt.ask(
        "Default output format",
        choices=["json", "table", "text"],
        default=current_output
    )
    config_manager.set_config_value("output", output_format)
    
    success_message(f"Configuration saved for profile: {profile}")


@configure.command()
@click.argument("key")
@click.argument("value")
@click.option("--profile", default="default", help="Profile name")
def set(key, value, profile):
    """Set a configuration value"""
    config_manager = ConfigManager(profile)
    
    # Determine if it's a credential or config
    if key in ["secret_id", "secret_key", "assume_role"]:
        config_manager.set_credential_value(key, value)
    else:
        config_manager.set_config_value(key, value)
    
    success_message(f"Set {key} = {value}")


@configure.command()
@click.argument("key")
@click.option("--profile", default="default", help="Profile name")
def get(key, profile):
    """Get a configuration value"""
    config_manager = ConfigManager(profile)
    
    # Try config first, then credentials
    value = config_manager.get_config_value(key)
    if value is None:
        value = config_manager.get_credential_value(key)
    
    if value:
        # Mask sensitive values
        if key in ["secret_id", "secret_key"]:
            value = "****"
        click.echo(value)
    else:
        click.echo(f"Key '{key}' not found", err=True)


@configure.command()
@click.option("--profile", default="default", help="Profile name")
def list(profile):
    """List all configuration values"""
    config_manager = ConfigManager(profile)
    config = config_manager.list_all_config()
    
    if not config:
        click.echo("No configuration found")
        return
    
    data = [{"Key": k, "Value": v} for k, v in config.items()]
    output_table(data)


@configure.command(name="import-token")
@click.option("--tmp-secret-id", required=True, help="Temporary Secret ID")
@click.option("--tmp-secret-key", required=True, help="Temporary Secret Key")
@click.option("--token", required=True, help="Security Token")
@click.option("--profile", default="temp", help="Profile name (default: temp)")
def import_token(tmp_secret_id, tmp_secret_key, token, profile):
    """
    Import temporary STS credentials for quick testing.
    
    Examples:
        cos configure import-token --tmp-secret-id xxx --tmp-secret-key yyy --token zzz
        
        # Or use output from 'cos token':
        eval $(cos token --output env)
        cos configure import-token --tmp-secret-id $COS_SECRET_ID --tmp-secret-key $COS_SECRET_KEY --token $COS_TOKEN
    """
    config_manager = ConfigManager(profile)
    
    # Store as regular credentials (will be treated as temporary based on token presence)
    config_manager.set_credential_value("secret_id", tmp_secret_id)
    config_manager.set_credential_value("secret_key", tmp_secret_key)
    config_manager.set_credential_value("token", token)
    
    success_message(f"Temporary credentials imported to profile: {profile}")
    info_message("Note: These credentials will expire. Use --profile temp when using commands.")
    info_message("Example: cos ls --profile temp")
