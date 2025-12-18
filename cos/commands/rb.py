"""Remove bucket command for COS CLI"""

import click

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import parse_cos_uri, is_cos_uri, success_message, error_message
from ..exceptions import COSError


@click.command()
@click.argument("bucket")
@click.option("--force", "-f", is_flag=True, help="Delete all objects in bucket first")
@click.pass_context
def rb(ctx, bucket, force):
    """
    Remove a bucket.

    \b
    Examples:
      cos rb cos://my-bucket          # Remove empty bucket
      cos rb cos://my-bucket --force  # Remove bucket and all contents
    """
    try:
        if not is_cos_uri(bucket):
            raise COSError(f"Invalid COS URI: {bucket}. Use format: cos://bucket-name")
        
        bucket_name, key = parse_cos_uri(bucket)
        if key:
            raise COSError("Bucket URI should not contain a path")
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw, bucket_name)
        
        if force:
            # Delete all objects first
            response = cos_client.list_objects(prefix="", delimiter="")
            objects = response.get("Contents", [])
            
            if objects:
                click.echo(f"Deleting {len(objects)} objects...")
                for obj in objects:
                    obj_key = obj.get("Key", "")
                    cos_client.delete_object(obj_key)
        
        # Delete bucket
        cos_client.delete_bucket(bucket_name)
        success_message(f"Deleted bucket: cos://{bucket_name}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
