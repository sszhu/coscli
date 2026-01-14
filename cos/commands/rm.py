"""Remove command for COS CLI"""

import click
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import parse_cos_uri, is_cos_uri, success_message, error_message
from ..exceptions import COSError


@click.command()
@click.argument("path")
@click.option("--recursive", "-r", is_flag=True, help="Remove recursively")
@click.option("--include", multiple=True, help="Include files matching pattern")
@click.option("--exclude", multiple=True, help="Exclude files matching pattern")
@click.option("--dryrun", is_flag=True, help="Show what would be deleted")
@click.option("--force", is_flag=True, help="Force deletion without prompts")
@click.option("--no-progress", is_flag=True, help="Disable progress bar")
@click.pass_context
def rm(ctx, path, recursive, include, exclude, dryrun, force, no_progress):
    """
    Remove objects from COS.

    \b
    Examples:
      cos rm cos://bucket/file.txt        # Remove single object
      cos rm cos://bucket/path/ -r        # Remove all objects with prefix
      cos rm cos://bucket/ -r --dryrun    # Show what would be deleted
    """
    try:
        if not is_cos_uri(path):
            raise COSError(f"Invalid COS URI: {path}")
        
        # Get config and auth
        ctx_obj = ctx.obj or {}
        profile = ctx_obj.get("profile", "default")
        region = ctx_obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        
        bucket, key = parse_cos_uri(path)
        cos_client = COSClient(cos_client_raw, bucket)
        
        if not recursive:
            # Single object deletion
            if dryrun:
                click.echo(f"Would delete: cos://{bucket}/{key}")
            else:
                # If force is False, we could prompt here; currently deletion is unconditional
                cos_client.delete_object(key)
                success_message(f"Deleted cos://{bucket}/{key}")
        else:
            # Multiple objects deletion
            response = cos_client.list_objects(prefix=key, delimiter="")
            objects = response.get("Contents", [])
            
            if not objects:
                click.echo(f"No objects found matching: cos://{bucket}/{key}")
                return
            
            if dryrun:
                click.echo(f"Would delete {len(objects)} objects:")
                for obj in objects[:10]:  # Show first 10
                    click.echo(f"  - {obj.get('Key', '')}")
                if len(objects) > 10:
                    click.echo(f"  ... and {len(objects) - 10} more")
            else:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                ) as progress:
                    task = progress.add_task(f"Deleting {len(objects)} objects...", total=len(objects))
                    
                    for obj in objects:
                        obj_key = obj.get("Key", "")
                        cos_client.delete_object(obj_key)
                        progress.update(task, advance=1)
                
                success_message(f"Deleted {len(objects)} objects from cos://{bucket}/{key}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
