"""List command for COS CLI"""

import click
from datetime import datetime

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import (
    parse_cos_uri,
    is_cos_uri,
    format_size,
    format_datetime,
    format_output,
    error_message,
)
from ..exceptions import COSError


@click.command()
@click.argument("path", required=False, default="")
@click.option("--recursive", "-r", is_flag=True, help="List recursively")
@click.option("--human-readable", "-h", is_flag=True, help="Human-readable sizes")
@click.pass_context
def ls(ctx, path, recursive, human_readable):
    """
    List buckets or objects.

    \b
    Examples:
      cos ls                        # List all buckets
      cos ls cos://bucket/          # List objects in bucket
      cos ls cos://bucket/prefix/   # List with prefix
      cos ls cos://bucket/ -r       # Recursive listing
    """
    try:
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        output_format = ctx.obj.get("output")
        
        config_manager = ConfigManager(profile)
        
        if output_format is None:
            output_format = config_manager.get_output_format()
        
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        
        # List buckets if no path provided
        if not path:
            cos_client = COSClient(cos_client_raw)
            buckets = cos_client.list_buckets()
            
            # Format output
            if output_format == "json":
                format_output(buckets, "json")
            elif output_format == "text":
                format_output([b["Name"] for b in buckets], "text")
            else:
                data = []
                for bucket in buckets:
                    data.append({
                        "Name": bucket["Name"],
                        "Region": bucket["Location"],
                        "Created": bucket["CreationDate"][:19] if bucket["CreationDate"] else "",
                    })
                format_output(data, "table")
            return
        
        # List objects in bucket
        if not is_cos_uri(path):
            raise COSError(f"Invalid COS URI: {path}")
        
        bucket, prefix = parse_cos_uri(path)
        cos_client = COSClient(cos_client_raw, bucket)
        
        # Get objects
        delimiter = "" if recursive else "/"
        response = cos_client.list_objects(prefix=prefix, delimiter=delimiter)
        
        # Extract objects and directories
        objects = []
        
        # Add common prefixes (directories) if not recursive
        if not recursive:
            for prefix_info in response.get("CommonPrefixes", []):
                prefix_name = prefix_info.get("Prefix", "")
                objects.append({
                    "Key": prefix_name,
                    "Size": 0,
                    "LastModified": "",
                    "Type": "DIR",
                })
        
        # Add objects
        for obj in response.get("Contents", []):
            key = obj.get("Key", "")
            size = int(obj.get("Size", 0))
            last_modified = obj.get("LastModified", "")
            
            # Parse datetime
            if last_modified:
                try:
                    dt = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%fZ")
                    last_modified = format_datetime(dt)
                except:
                    pass
            
            objects.append({
                "Key": key,
                "Size": size,
                "LastModified": last_modified,
                "Type": "FILE",
            })
        
        # Format output
        if output_format == "json":
            format_output(objects, "json")
        elif output_format == "text":
            format_output([obj["Key"] for obj in objects], "text")
        else:
            # Table format
            data = []
            for obj in objects:
                size_display = format_size(obj["Size"]) if human_readable else str(obj["Size"])
                if obj["Type"] == "DIR":
                    size_display = "DIR"
                
                data.append({
                    "Key": obj["Key"],
                    "Size": size_display,
                    "Last Modified": obj["LastModified"],
                })
            
            if data:
                format_output(data, "table")
            else:
                click.echo(f"No objects found in cos://{bucket}/{prefix}")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)
