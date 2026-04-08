import os
import sys
import time
import subprocess
import tempfile
import webbrowser
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
@click.option("--open", "open_results", is_flag=True, help="Open top results in system viewer.")
@click.option("--html", is_flag=True, help="Generate HTML preview and open in browser.")
@click.option("--db-path", default=None, help="Override database path.")
@click.option("--config-path", default=None, help="Override config file path.")
def search(query: str, limit: int | None, no_sync: bool, open_results: bool, html: bool, db_path: str | None, config_path: str | None):
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

    if open_results:
        paths = [r["file_path"] for r in results]
        subprocess.Popen(["open"] + paths, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if html:
        _open_html_preview(query, results, elapsed)


def _open_html_preview(query: str, results: list[dict], elapsed: float):
    from html import escape
    import base64

    items = []
    for r in results:
        path = r["file_path"]
        score = r["score"]
        name = os.path.basename(path)
        try:
            ext = os.path.splitext(path)[1].lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp", "bmp": "bmp"}.get(ext, "jpeg")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            src = f"data:image/{mime};base64,{b64}"
        except Exception:
            src = ""
        items.append(f"""
      <div class="card">
        <img src="{src}" alt="{escape(name)}" onclick="window.open('file://{escape(path)}')">
        <div class="info">
          <span class="score">{score:.4f}</span>
          <span class="name" title="{escape(path)}">{escape(name)}</span>
        </div>
      </div>""")

    html_content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>PicSeek: {escape(query)}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; }}
  h1 {{ text-align: center; font-size: 1.4em; color: #a0a0ff; }}
  .meta {{ text-align: center; color: #888; font-size: 0.9em; margin-bottom: 20px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; max-width: 1400px; margin: 0 auto; }}
  .card {{ background: #16213e; border-radius: 10px; overflow: hidden; transition: transform 0.2s; }}
  .card:hover {{ transform: scale(1.03); }}
  .card img {{ width: 100%; height: 220px; object-fit: cover; cursor: pointer; }}
  .info {{ padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; }}
  .score {{ background: #0f3460; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; color: #e94560; }}
  .name {{ font-size: 0.8em; color: #aaa; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 60%; }}
</style></head><body>
<h1>PicSeek: "{escape(query)}"</h1>
<p class="meta">{len(results)} results in {elapsed:.2f}s</p>
<div class="grid">{"".join(items)}</div>
</body></html>"""

    tmp = tempfile.NamedTemporaryFile(suffix=".html", prefix="picseek_", delete=False, mode="w", encoding="utf-8")
    tmp.write(html_content)
    tmp.close()
    webbrowser.open(f"file://{tmp.name}")
    click.echo(f"Preview: {tmp.name}")


@main.command("config")
@click.option("--config-path", default=None, help="Override config file path.")
def show_config(config_path: str | None):
    """Show current configuration."""
    config = load_config(config_path)
    click.echo(yaml.dump(config, default_flow_style=False, allow_unicode=True))
