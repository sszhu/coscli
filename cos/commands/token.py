"""Token command for COS CLI - Generate temporary STS credentials"""

import click
import json
from datetime import datetime, timedelta

from ..auth import STSTokenManager
from ..config import ConfigManager
from ..utils import success_message, error_message, info_message, format_output


@click.command()
@click.option("--duration", "-d", default=7200, type=int, help="Token duration in seconds (default: 7200, max: 43200)")
@click.option("--profile", default="default", help="Profile name")
@click.option("--output", "-o", type=click.Choice(["json", "table", "env"]), help="Output format (json/table/env)")
@click.pass_context
def token(ctx, duration, profile, output):
    """
    Generate temporary STS credentials for testing.

    \b
    Examples:
      cos token                    # Generate token with default duration
      cos token --duration 3600    # Generate 1-hour token
      cos token --output env       # Output as environment variables
      cos token --output json      # Output as JSON
    """
    try:
        # Get config
        config_manager = ConfigManager(profile)
        
        if output is None:
            output = config_manager.get_output_format()
        
        # Get credentials
        try:
            credentials = config_manager.get_credentials()
            secret_id = credentials["secret_id"]
            secret_key = credentials["secret_key"]
            assume_role = credentials.get("assume_role")
            
            if not assume_role:
                error_message("Assume role ARN is required for generating temporary tokens")
                click.echo("\nRun 'cos configure' and set the assume_role ARN", err=True)
                ctx.exit(1)
                
        except Exception as e:
            error_message(f"Failed to get credentials: {e}")
            click.echo("\nRun 'cos configure' to set up credentials", err=True)
            ctx.exit(1)
        
        # Validate duration
        if duration < 1800:
            error_message("Duration must be at least 1800 seconds (30 minutes)")
            ctx.exit(1)
        if duration > 43200:
            error_message("Duration cannot exceed 43200 seconds (12 hours)")
            ctx.exit(1)
        
        # Get region
        region = ctx.obj.get("region") or config_manager.get_region()
        
        # Generate token
        info_message(f"Generating temporary credentials (duration: {duration}s)...")
        
        sts_manager = STSTokenManager(secret_id, secret_key, assume_role)
        sts_manager.sts_duration = duration  # Override default duration
        
        temp_creds = sts_manager.get_temp_credentials(region)
        
        # Calculate expiration time
        expiration = datetime.now() + timedelta(seconds=duration)
        
        # Format output
        if output == "env":
            # Output as environment variables
            click.echo("# Export these environment variables to use temporary credentials")
            click.echo(f"export COS_SECRET_ID='{temp_creds['tmp_secret_id']}'")
            click.echo(f"export COS_SECRET_KEY='{temp_creds['tmp_secret_key']}'")
            click.echo(f"export COS_TOKEN='{temp_creds['token']}'")
            click.echo(f"# Valid until: {expiration.strftime('%Y-%m-%d %H:%M:%S')}")
            
        elif output == "json":
            # Output as JSON
            result = {
                "Credentials": {
                    "TmpSecretId": temp_creds["tmp_secret_id"],
                    "TmpSecretKey": temp_creds["tmp_secret_key"],
                    "Token": temp_creds["token"],
                    "Expiration": expiration.isoformat(),
                },
                "ExpiresIn": duration,
                "RequestedTime": datetime.now().isoformat(),
            }
            format_output(result, "json")
            
        else:
            # Output as table
            data = [
                {"Key": "TmpSecretId", "Value": temp_creds["tmp_secret_id"][:20] + "..."},
                {"Key": "TmpSecretKey", "Value": temp_creds["tmp_secret_key"][:20] + "..."},
                {"Key": "Token", "Value": temp_creds["token"][:50] + "..."},
                {"Key": "Duration", "Value": f"{duration}s ({duration//3600}h {(duration%3600)//60}m)"},
                {"Key": "Expires At", "Value": expiration.strftime("%Y-%m-%d %H:%M:%S")},
            ]
            format_output(data, "table")
        
        success_message("Temporary credentials generated successfully")
        
        # Provide usage hint
        if output != "env":
            click.echo("\nℹ️  To use these credentials, export them as environment variables:")
            click.echo("   cos token --output env > temp_creds.sh")
            click.echo("   source temp_creds.sh")
            
    except Exception as e:
        error_message(f"Failed to generate token: {e}")
        ctx.exit(1)
