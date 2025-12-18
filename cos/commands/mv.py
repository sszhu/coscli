"""Move command for COS CLI"""

import click
from pathlib import Path

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
@click.argument("source")
@click.argument("destination")
@click.option("--recursive", "-r", is_flag=True, help="Move recursively")
@click.option("--force", "-f", is_flag=True, help="Force overwrite")
@click.pass_context
def mv(ctx, source, destination, recursive, force):
    """
    Move or rename objects.

    \b
    Examples:
      cos mv cos://bucket/old.txt cos://bucket/new.txt       # Rename
      cos mv cos://bucket/dir/ cos://bucket/newdir/ -r       # Move directory
      cos mv cos://bucket1/file cos://bucket2/file           # Move between buckets
    """
    try:
        # Validate URIs
        if not is_cos_uri(source):
            raise COSError(f"Source must be a COS URI: {source}")
        if not is_cos_uri(destination):
            raise COSError(f"Destination must be a COS URI: {destination}")
        
        # Parse URIs
        src_bucket, src_key = parse_cos_uri(source)
        dst_bucket, dst_key = parse_cos_uri(destination)
        
        if not src_key:
            raise COSError("Source key cannot be empty")
        if not dst_key:
            raise COSError("Destination key cannot be empty")
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        
        # Handle recursive move
        if recursive:
            # List all objects with prefix
            src_client = COSClient(cos_client_raw, src_bucket)
            objects = src_client.list_objects(prefix=src_key, delimiter="")
            
            if not objects:
                info_message(f"No objects found with prefix: {src_key}")
                return
            
            moved_count = 0
            for obj in objects:
                src_obj_key = obj["Key"]
                
                # Calculate destination key
                relative_key = src_obj_key[len(src_key):].lstrip("/")
                dst_obj_key = dst_key.rstrip("/") + "/" + relative_key if relative_key else dst_key
                
                # Copy to destination
                if src_bucket == dst_bucket:
                    client = COSClient(cos_client_raw, src_bucket)
                else:
                    dst_client = COSClient(cos_client_raw, dst_bucket)
                    client = dst_client
                
                # Copy
                copy_source = {'Bucket': src_bucket, 'Key': src_obj_key, 'Region': region or config_manager.get_region()}
                
                if src_bucket == dst_bucket:
                    cos_client_raw.copy_object(
                        Bucket=dst_bucket,
                        Key=dst_obj_key,
                        CopySource=copy_source
                    )
                else:
                    cos_client_raw.copy_object(
                        Bucket=dst_bucket,
                        Key=dst_obj_key,
                        CopySource=copy_source
                    )
                
                # Delete source
                src_client.delete_object(src_obj_key)
                
                info_message(f"Moved: {src_obj_key} -> cos://{dst_bucket}/{dst_obj_key}")
                moved_count += 1
            
            success_message(f"Successfully moved {moved_count} objects")
        
        else:
            # Single object move
            src_client = COSClient(cos_client_raw, src_bucket)
            
            # Check if source exists
            try:
                src_client.head_object(src_key)
            except:
                raise COSError(f"Source object not found: cos://{src_bucket}/{src_key}")
            
            # Check if destination exists
            if not force:
                try:
                    dst_client = COSClient(cos_client_raw, dst_bucket)
                    dst_client.head_object(dst_key)
                    if not click.confirm(f"Destination already exists. Overwrite?"):
                        error_message("Move cancelled")
                        ctx.exit(1)
                except:
                    pass  # Destination doesn't exist, safe to proceed
            
            # Copy to destination
            copy_source = {
                'Bucket': src_bucket,
                'Key': src_key,
                'Region': region or config_manager.get_region()
            }
            
            cos_client_raw.copy_object(
                Bucket=dst_bucket,
                Key=dst_key,
                CopySource=copy_source
            )
            
            # Delete source
            src_client.delete_object(src_key)
            
            success_message(f"Moved: cos://{src_bucket}/{src_key} -> cos://{dst_bucket}/{dst_key}")
            
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        error_message(f"Failed to move object: {e}")
        if ctx.obj.get("debug"):
            raise
        ctx.exit(1)
