"""Main CLI entry point for COS CLI"""

import click

from .config import ConfigManager
from .commands import configure, ls, cp, rm, mb, rb, token, mv, presign, sync, lifecycle, policy, cors, versioning
from . import __version__


@click.group()
@click.version_option(version=__version__)
@click.option("--profile", default="default", help="Use a specific profile")
@click.option("--region", default=None, help="Override default region")
@click.option("--output", type=click.Choice(["json", "table", "text"]), help="Output format")
@click.option("--endpoint-url", default=None, help="Override endpoint URL")
@click.option("--no-verify-ssl", is_flag=True, help="Disable SSL verification")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output")
@click.pass_context
def cli(ctx, profile, region, output, endpoint_url, no_verify_ssl, debug, quiet):
    """
    Tencent Cloud Object Storage (COS) Command Line Interface

    A powerful CLI tool for managing Tencent COS, similar to AWS CLI.

    \b
    Examples:
      cos configure                           # Setup credentials
      cos ls                                  # List buckets
      cos ls cos://bucket/                    # List objects
      cos cp file.txt cos://bucket/file.txt   # Upload file
      cos cp cos://bucket/file.txt ./local    # Download file
      cos rm cos://bucket/file.txt            # Delete object
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store options in context
    ctx.obj["profile"] = profile
    ctx.obj["region"] = region
    ctx.obj["output"] = output
    ctx.obj["endpoint_url"] = endpoint_url
    ctx.obj["no_verify_ssl"] = no_verify_ssl
    ctx.obj["debug"] = debug
    ctx.obj["quiet"] = quiet


# Register commands
cli.add_command(configure.configure)
cli.add_command(ls.ls)
cli.add_command(cp.cp)
cli.add_command(mv.mv)
cli.add_command(rm.rm)
cli.add_command(sync.sync)
cli.add_command(mb.mb)
cli.add_command(rb.rb)
cli.add_command(presign.presign)
cli.add_command(token.token)
cli.add_command(lifecycle.lifecycle)
cli.add_command(policy.policy)
cli.add_command(cors.cors)
cli.add_command(versioning.versioning)


def main():
    """Main entry point"""
    cli(obj={})


if __name__ == "__main__":
    main()
