import os
import sys
import time
import click
import yaml
from picseek.config import load_config, get_db_path, DEFAULT_CONFIG_PATH


@click.group()
@click.version_option(package_name="picseek")
def main():
    """PicSeek — local image semantic search."""
    pass


@main.command()
@click.argument("directory", type=click.Path())
@click.option("--db-path", default=None, help="Override database path.")
@click.option("--config-path", default=None, help="Override config file path.")
def index(directory: str, db_path: str | None, config_path: str | None):
    """Index images in a directory."""
    directory = os.path.abspath(os.path.expanduser(directory))
    if not os.path.isdir(directory):
        click.echo(f"Error: Directory not found: {directory}", err=True)
        sys.exit(1)

    config = load_config(config_path)
    resolved_db = db_path or get_db_path(config)

    if directory not in config.get("index_paths", []):
        config.setdefault("index_paths", []).append(directory)
        from picseek.config import save_config
        save_config(config, config_path)

    click.echo(f"Scanning {directory} ...")

    from picseek.indexer import run_index
    start = time.time()
    stats = run_index(directory, resolved_db, formats=config["formats"])
    elapsed = time.time() - start

    click.echo(f"\n  New:     {stats['new']}")
    click.echo(f"  Updated: {stats['updated']}")
    click.echo(f"  Deleted: {stats['deleted']}")
    click.echo(f"  Skipped: {stats['skipped']}")
    click.echo(f"  Errors:  {stats['errors']}")
    click.echo(f"\nDone in {elapsed:.1f}s. Database: {resolved_db}")


@main.command()
@click.argument("query")
@click.option("-n", "--limit", default=None, type=int, help="Max results.")
@click.option("--no-sync", is_flag=True, help="Skip pre-search sync.")
@click.option("--db-path", default=None, help="Override database path.")
@click.option("--config-path", default=None, help="Override config file path.")
def search(query: str, limit: int | None, no_sync: bool, db_path: str | None, config_path: str | None):
    """Search images by natural language description."""
    config = load_config(config_path)
    resolved_db = db_path or get_db_path(config)
    limit = limit or config["default_limit"]

    if not os.path.exists(resolved_db):
        click.echo("No images indexed. Run 'picseek index <path>' first.")
        return

    from picseek.searcher import run_search
    start = time.time()
    results = run_search(
        query,
        resolved_db,
        limit=limit,
        sync=not no_sync,
        index_paths=config.get("index_paths", []),
        formats=config.get("formats", []),
    )
    elapsed = time.time() - start

    if not results:
        click.echo(f'No matching images found for "{query}".')
        return

    click.echo(f'\nResults for "{query}":\n')
    click.echo(f"  {'Score':<8}Path")
    for r in results:
        click.echo(f"  {r['score']:<8.4f}{r['file_path']}")
    click.echo(f"\n{len(results)} results ({elapsed:.2f}s)")


@main.command("config")
@click.option("--config-path", default=None, help="Override config file path.")
def show_config(config_path: str | None):
    """Show current configuration."""
    config = load_config(config_path)
    click.echo(yaml.dump(config, default_flow_style=False, allow_unicode=True))
