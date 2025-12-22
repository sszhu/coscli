"""Token command for COS CLI - Generate temporary STS credentials"""

import click
import json
from datetime import datetime, timedelta
from typing import Optional, List

from ..auth import STSTokenManager
from ..config import ConfigManager
from ..utils import (
    success_message, error_message, info_message, format_output,
    parse_cos_uri, validate_bucket_name
)


def build_policy(
    bucket: str,
    region: str,
    appid: str,
    prefix: Optional[str] = None,
    actions: Optional[List[str]] = None,
    read_only: bool = False
) -> dict:
    """
    Build a CAM policy for STS credentials.
    
    Args:
        bucket: Bucket name
        region: Region
        appid: Account APPID
        prefix: Object prefix to restrict access (e.g., 'folder/subfolder')
        actions: List of allowed actions (if None, uses defaults)
        read_only: If True, only allow read operations
        
    Returns:
        Policy dict suitable for STS AssumeRole
    """
    # Default actions based on read_only flag
    if actions is None:
        if read_only:
            actions = [
                "name/cos:GetObject",
                "name/cos:HeadObject",
                "name/cos:OptionsObject",
                "name/cos:ListParts",
            ]
        else:
            actions = [
                # Read operations
                "name/cos:GetObject",
                "name/cos:HeadObject",
                "name/cos:OptionsObject",
                # Write operations
                "name/cos:PutObject",
                "name/cos:PostObject",
                "name/cos:DeleteObject",
                # Multipart operations
                "name/cos:InitiateMultipartUpload",
                "name/cos:ListMultipartUploads",
                "name/cos:ListParts",
                "name/cos:UploadPart",
                "name/cos:CompleteMultipartUpload",
                "name/cos:AbortMultipartUpload",
            ]
    else:
        # Ensure actions have proper prefix
        actions = [f"name/cos:{a}" if not a.startswith("name/") else a for a in actions]
    
    # Build resource string
    if prefix:
        # Ensure prefix doesn't start with / and ends with /*
        prefix = prefix.lstrip('/')
        if not prefix.endswith('/'):
            prefix += '/'
        resource = f"qcs::cos:{region}:uid/{appid}:{bucket}/{prefix}*"
    else:
        # Full bucket access
        resource = f"qcs::cos:{region}:uid/{appid}:{bucket}/*"
    
    # Build policy
    policy = {
        "version": "2.0",
        "statement": [
            {
                "effect": "allow",
                "action": actions,
                "resource": [resource]
            }
        ]
    }
    
    # Add bucket-level operations (needed for listing)
    # Note: GetBucket permission is required on the bucket to list objects
    # The actual object access is still restricted by the prefix resource above
    bucket_actions = ["name/cos:HeadBucket", "name/cos:GetBucket"]
    bucket_resource = f"qcs::cos:{region}:uid/{appid}:{bucket}/*"
    
    policy["statement"].append({
        "effect": "allow",
        "action": bucket_actions,
        "resource": [bucket_resource]
    })
    
    # Note: We don't add prefix condition here because:
    # 1. The CLI/SDK automatically filters results by prefix in the list request
    # 2. Tencent COS condition syntax for prefix may not work consistently
    # 3. Object access is already restricted by the resource path above
    
    return policy


def extract_appid_from_bucket(bucket: str) -> Optional[str]:
    """
    Extract APPID from bucket name.
    Tencent COS bucket names typically end with -APPID.
    
    Args:
        bucket: Bucket name (e.g., 'mybucket-1234567890')
        
    Returns:
        APPID or None
    """
    parts = bucket.split('-')
    if len(parts) > 1 and parts[-1].isdigit() and len(parts[-1]) == 10:
        return parts[-1]
    return None


@click.command()
@click.option("--duration", "-d", default=7200, type=int, 
              help="Token duration in seconds (default: 7200, max: 43200)")
@click.option("--profile", default="default", help="Profile name")
@click.option("--output", "-o", type=click.Choice(["json", "table", "env"]), 
              help="Output format (json/table/env)")
@click.option("--bucket", "-b", help="Bucket name for prefix-restricted access")
@click.option("--prefix", "-p", help="Object prefix to restrict access (e.g., 'folder/subfolder')")
@click.option("--region", "-r", help="Region (default: from config or ap-shanghai)")
@click.option("--appid", help="Account APPID (auto-detected from bucket name if not provided)")
@click.option("--action", "actions", multiple=True, 
              help="Allowed actions (can specify multiple times)")
@click.option("--read-only", is_flag=True, help="Generate read-only credentials")
@click.pass_context
def token(ctx, duration, profile, output, bucket, prefix, region, appid, actions, read_only):
    """
    Generate temporary STS credentials for COS access.

    \b
    Examples:
      # Basic token generation
      cos token
      
      # Generate with custom duration
      cos token --duration 3600
      
      # Output as environment variables for sourcing
      cos token --output env > creds.sh && source creds.sh
      
      # Generate prefix-restricted token
      cos token --bucket mybucket-1234567890 --prefix "data/uploads"
      
      # Generate read-only token for specific prefix
      cos token --bucket mybucket-1234567890 --prefix "reports" --read-only
      
      # Specify region and custom actions
      cos token --bucket mybucket-1234567890 --region ap-shanghai \\
                --action GetObject --action PutObject
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
        if duration < 900:
            error_message("Duration must be at least 900 seconds (15 minutes)")
            ctx.exit(1)
        if duration > 43200:
            error_message("Duration cannot exceed 43200 seconds (12 hours)")
            ctx.exit(1)
        
        # Get region
        if region is None:
            region = ctx.obj.get("region") or config_manager.get_region()
        
        # Build policy if bucket is specified
        policy = None
        if bucket:
            # Parse bucket from URI if provided
            if bucket.startswith("cos://"):
                bucket, key = parse_cos_uri(bucket)
                if key and not prefix:
                    prefix = key
            
            # Validate bucket name
            if not validate_bucket_name(bucket):
                error_message(f"Invalid bucket name: {bucket}")
                ctx.exit(1)
            
            # Extract APPID
            if not appid:
                appid = extract_appid_from_bucket(bucket)
                if not appid:
                    error_message(
                        "Could not extract APPID from bucket name. "
                        "Please provide --appid explicitly."
                    )
                    click.echo(
                        "\nBucket names should end with -APPID (e.g., mybucket-1234567890)",
                        err=True
                    )
                    ctx.exit(1)
            
            # Convert actions tuple to list if provided
            action_list = list(actions) if actions else None
            
            # Build policy
            policy = build_policy(
                bucket=bucket,
                region=region,
                appid=appid,
                prefix=prefix,
                actions=action_list,
                read_only=read_only
            )
            
            # For env output, send info messages to stderr
            if output == "env":
                click.echo(
                    f"ℹ Generating prefix-restricted credentials for {bucket}",
                    err=True
                )
                if prefix:
                    click.echo(f"  Prefix: {prefix}", err=True)
                click.echo(f"  Duration: {duration}s", err=True)
                if read_only:
                    click.echo("  Mode: Read-only", err=True)
            else:
                info_message(f"Generating prefix-restricted credentials for {bucket}")
                if prefix:
                    click.echo(f"  Prefix: {prefix}")
                if read_only:
                    click.echo("  Mode: Read-only")
        else:
            # For env output, send info messages to stderr
            if output == "env":
                click.echo(
                    f"ℹ Generating temporary credentials (duration: {duration}s)...",
                    err=True
                )
            else:
                info_message(f"Generating temporary credentials (duration: {duration}s)...")
        
        # Generate token
        sts_manager = STSTokenManager(secret_id, secret_key, assume_role)
        sts_manager.sts_duration = duration  # Override default duration
        
        temp_creds = sts_manager.get_temp_credentials(
            region=region,
            policy=policy
        )
        
        # Calculate expiration time
        expiration = datetime.now() + timedelta(seconds=duration)
        
        # Format output
        if output == "env":
            # Output as environment variables (stdout only, no decorations)
            click.echo("# Export these environment variables to use temporary credentials")
            click.echo(f"export COS_SECRET_ID='{temp_creds['tmp_secret_id']}'")
            click.echo(f"export COS_SECRET_KEY='{temp_creds['tmp_secret_key']}'")
            click.echo(f"export COS_TOKEN='{temp_creds['token']}'")
            if bucket:
                click.echo(f"# Restricted to: cos://{bucket}/{prefix or ''}")
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
            if bucket:
                result["Restrictions"] = {
                    "Bucket": bucket,
                    "Prefix": prefix,
                    "ReadOnly": read_only,
                }
                result["Policy"] = policy
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
            if bucket:
                data.insert(0, {"Key": "Bucket", "Value": bucket})
                if prefix:
                    data.insert(1, {"Key": "Prefix", "Value": prefix})
                if read_only:
                    data.insert(2, {"Key": "Mode", "Value": "Read-only"})
            format_output(data, "table")
        
        # Success message to stderr for env output, normal for others
        if output == "env":
            click.echo("✓ Temporary credentials generated successfully", err=True)
        else:
            success_message("Temporary credentials generated successfully")
        
        # Provide usage hint
        if output != "env":
            click.echo("\nℹ️  To use these credentials, export them as environment variables:")
            if bucket:
                cmd_parts = [f"   cos token --bucket {bucket}"]
                if prefix:
                    cmd_parts.append(f" --prefix {prefix}")
                cmd_parts.append(" --output env > temp_creds.sh")
                click.echo("".join(cmd_parts))
            else:
                click.echo("   cos token --output env > temp_creds.sh")
            click.echo("   source temp_creds.sh")
            
    except Exception as e:
        error_message(f"Failed to generate token: {e}")
        import traceback
        if ctx.obj.get("debug"):
            click.echo(traceback.format_exc(), err=True)
        ctx.exit(1)
