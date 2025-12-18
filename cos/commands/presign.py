"""Presign command for COS CLI - Generate presigned URLs"""

import click
from datetime import datetime, timedelta

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import (
    parse_cos_uri,
    is_cos_uri,
    success_message,
    error_message,
    info_message,
)
from ..exceptions import COSError


@click.command()
@click.argument("cos_uri")
@click.option("--expires-in", "-e", default=3600, type=int, help="URL expiration in seconds (default: 3600)")
@click.option("--method", "-m", type=click.Choice(["GET", "PUT", "DELETE"]), default="GET", help="HTTP method")
@click.pass_context
def presign(ctx, cos_uri, expires_in, method):
    """
    Generate presigned URLs for COS objects.

    Presigned URLs allow temporary access to objects without credentials.

    \b
    Examples:
      cos presign cos://bucket/file.txt                    # Default 1-hour GET URL
      cos presign cos://bucket/file.txt --expires-in 7200  # 2-hour URL
      cos presign cos://bucket/file.txt --method PUT       # Upload URL
      cos presign cos://bucket/file.txt -e 300            # 5-minute URL
    """
    try:
        # Validate URI
        if not is_cos_uri(cos_uri):
            raise COSError(f"Invalid COS URI: {cos_uri}")
        
        bucket, key = parse_cos_uri(cos_uri)
        
        if not key:
            raise COSError("Object key cannot be empty")
        
        # Validate expiration
        if expires_in < 60:
            error_message("Expiration must be at least 60 seconds")
            ctx.exit(1)
        if expires_in > 604800:  # 7 days
            error_message("Expiration cannot exceed 604800 seconds (7 days)")
            ctx.exit(1)
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        
        # Generate presigned URL
        info_message(f"Generating presigned URL for {method} operation...")
        
        if method == "GET":
            url = cos_client_raw.get_presigned_url(
                Method='GET',
                Bucket=bucket,
                Key=key,
                Expired=expires_in
            )
        elif method == "PUT":
            url = cos_client_raw.get_presigned_url(
                Method='PUT',
                Bucket=bucket,
                Key=key,
                Expired=expires_in
            )
        elif method == "DELETE":
            url = cos_client_raw.get_presigned_url(
                Method='DELETE',
                Bucket=bucket,
                Key=key,
                Expired=expires_in
            )
        
        # Calculate expiration time
        expiration_time = datetime.now() + timedelta(seconds=expires_in)
        
        # Output URL
        click.echo()
        click.echo(url)
        click.echo()
        
        # Show metadata
        duration_hours = expires_in // 3600
        duration_mins = (expires_in % 3600) // 60
        duration_str = f"{duration_hours}h {duration_mins}m" if duration_hours > 0 else f"{duration_mins}m"
        
        info_message(f"Method: {method}")
        info_message(f"Duration: {expires_in}s ({duration_str})")
        info_message(f"Expires at: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show usage examples
        click.echo()
        if method == "GET":
            info_message("Usage examples:")
            click.echo(f"  # Download with curl:")
            click.echo(f"  curl -O '{url}'")
            click.echo()
            click.echo(f"  # Download with wget:")
            click.echo(f"  wget '{url}'")
        elif method == "PUT":
            info_message("Usage examples:")
            click.echo(f"  # Upload with curl:")
            click.echo(f"  curl -X PUT -T /path/to/file '{url}'")
            click.echo()
            click.echo(f"  # Upload with wget:")
            click.echo(f"  wget --method=PUT --body-file=/path/to/file '{url}'")
        elif method == "DELETE":
            info_message("Usage examples:")
            click.echo(f"  # Delete with curl:")
            click.echo(f"  curl -X DELETE '{url}'")
        
        success_message("Presigned URL generated successfully")
            
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        error_message(f"Failed to generate presigned URL: {e}")
        if ctx.obj.get("debug"):
            raise
        ctx.exit(1)
