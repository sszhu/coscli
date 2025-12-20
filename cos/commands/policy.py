"""Bucket policy commands for COS CLI"""

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
def policy():
    """Manage bucket policies."""
    pass


@policy.command("get")
@click.argument("cos_uri")
@click.pass_context
def get_policy(ctx, cos_uri):
    """
    Get bucket policy.

    \b
    Examples:
      cos policy get cos://bucket
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
        
        # Get bucket policy
        response = cos_client.get_bucket_policy()
        
        # Extract and format policy
        policy_str = response.get("Policy", "{}")
        policy = json.loads(policy_str) if isinstance(policy_str, str) else policy_str
        
        # Display
        output_format = ctx.obj.get("output", "json")
        if output_format == "json":
            console.print_json(json.dumps(policy, indent=2))
        else:
            console.print(f"[bold]Policy for {bucket}:[/bold]\n")
            console.print_json(json.dumps(policy, indent=2))
        
        success_message("Retrieved bucket policy")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@policy.command("put")
@click.argument("cos_uri")
@click.option("--policy", "-p", "policy_file", required=True, type=click.Path(exists=True),
              help="JSON file with bucket policy")
@click.pass_context
def put_policy(ctx, cos_uri, policy_file):
    """
    Set bucket policy.

    \b
    Examples:
      cos policy put cos://bucket --policy policy.json
    
    \b
    Example policy.json:
      {
        "version": "2.0",
        "Statement": [
          {
            "Effect": "Allow",
            "Principal": {"qcs": ["qcs::cam::uin/100000000001:uin/100000000001"]},
            "Action": ["name/cos:GetObject"],
            "Resource": ["qcs::cos:ap-shanghai:uid/1250000000:bucket/*"]
          }
        ]
      }
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Load policy from file
        with open(policy_file, 'r') as f:
            policy_dict = json.load(f)
        
        # Convert to JSON string if needed
        policy_str = json.dumps(policy_dict) if isinstance(policy_dict, dict) else policy_dict
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Set bucket policy
        cos_client.put_bucket_policy(policy_str)
        
        success_message(f"Set policy for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


@policy.command("delete")
@click.argument("cos_uri")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_policy(ctx, cos_uri, yes):
    """
    Delete bucket policy.

    \b
    Examples:
      cos policy delete cos://bucket
      cos policy delete cos://bucket --yes
    """
    try:
        bucket, _ = parse_cos_uri(cos_uri)
        
        # Confirmation
        if not yes:
            if not click.confirm(f"Delete policy for {bucket}?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Delete bucket policy
        cos_client.delete_bucket_policy()
        
        success_message(f"Deleted policy for {bucket}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
