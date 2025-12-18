"""Make bucket command for COS CLI"""

import click

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import parse_cos_uri, is_cos_uri, success_message, error_message
from ..exceptions import COSError


@click.command()
@click.argument("bucket")
@click.option("--region", help="Region for the bucket")
@click.pass_context
def mb(ctx, bucket, region):
    """
    Create a new bucket.

    \b
    Examples:
      cos mb cos://my-new-bucket
      cos mb cos://my-new-bucket --region ap-beijing
    """
    try:
        if not is_cos_uri(bucket):
            raise COSError(f"Invalid COS URI: {bucket}. Use format: cos://bucket-name")
        
        bucket_name, key = parse_cos_uri(bucket)
        if key:
            raise COSError("Bucket URI should not contain a path")
        
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        if region is None:
            region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        if region is None:
            region = config_manager.get_region()
        
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        cos_client = COSClient(cos_client_raw)
        
        # Create bucket
        cos_client.create_bucket(bucket_name)
        success_message(f"Created bucket: cos://{bucket_name} in region {region}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
