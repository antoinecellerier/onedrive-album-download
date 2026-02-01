"""Command-line interface for OneDrive Album Downloader."""

import asyncio
import sys
import traceback
from pathlib import Path
import click
from tqdm import tqdm

from onedrive_downloader import __version__
from onedrive_downloader.auth import OneDriveAuthenticator
from onedrive_downloader.api import OneDriveAPIClient
from onedrive_downloader.parser import parse_and_encode_url
from onedrive_downloader.downloader import ImageDownloader
from onedrive_downloader.config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_CONCURRENT_DOWNLOADS,
    DEFAULT_MAX_RETRIES
)


@click.command()
@click.version_option(version=__version__, prog_name="onedrive-downloader")
@click.argument('album_url')
@click.option(
    '--output', '-o',
    default=DEFAULT_OUTPUT_DIR,
    help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})'
)
@click.option(
    '--concurrent', '-c',
    type=int,
    default=DEFAULT_CONCURRENT_DOWNLOADS,
    help=f'Concurrent downloads (default: {DEFAULT_CONCURRENT_DOWNLOADS}, try 15-20 for faster speeds)'
)
@click.option(
    '--retries', '-r',
    type=int,
    default=DEFAULT_MAX_RETRIES,
    help=f'Max retries per image (default: {DEFAULT_MAX_RETRIES})'
)
@click.option(
    '--config',
    default='config.json',
    help='OAuth config file (default: config.json)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Verbose output'
)
@click.option(
    '--no-recursive',
    is_flag=True,
    help='Don\'t recursively download from subfolders'
)
@click.option(
    '--dry-run', '-n',
    is_flag=True,
    help='Show what would be downloaded without downloading'
)
def main(album_url, output, concurrent, retries, config, verbose, no_recursive, dry_run):
    """
    Download all images from a OneDrive album.

    ALBUM_URL should be a OneDrive sharing link (from the Share button), e.g.:
    https://1drv.ms/a/c/YOUR_ALBUM_ID

    Examples:

        Download album to default directory:
        $ python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID"

        Download to custom directory with 10 concurrent downloads:
        $ python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID" -o ./photos -c 10

        Verbose output:
        $ python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID" -v

        Dry run (preview only):
        $ python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID" --dry-run
    """
    try:
        # Step 1: Authenticate
        click.echo("🔐 Authenticating with Microsoft...")

        try:
            auth = OneDriveAuthenticator(config)
            access_token = auth.get_access_token()
        except FileNotFoundError as e:
            click.echo(f"\n❌ Error: {str(e)}", err=True)
            click.echo("\nSetup instructions:")
            click.echo("1. Copy config.json.example to config.json")
            click.echo("2. Fill in your Azure AD application credentials")
            click.echo("3. See README.md for detailed setup instructions")
            sys.exit(1)
        except Exception as e:
            click.echo(f"\n❌ Authentication failed: {str(e)}", err=True)
            if verbose:
                traceback.print_exc()
            sys.exit(1)

        click.echo("✓ Authentication successful\n")

        # Step 2: Initialize API client
        client = OneDriveAPIClient(access_token)

        # Step 3: Parse and encode sharing URL
        if verbose:
            click.echo(f"Album URL: {album_url}")

        try:
            encoded_url = parse_and_encode_url(album_url)
            if verbose:
                click.echo(f"Encoded URL: {encoded_url}\n")
        except ValueError as e:
            click.echo(f"\n❌ Error: {str(e)}", err=True)
            sys.exit(1)

        # Step 4: Get shared item metadata
        click.echo("📂 Accessing album...")

        try:
            album_info = client.get_album_info(encoded_url)
            album_name = album_info['name']
            drive_id = album_info['drive_id']
            item_id = album_info['item_id']
        except Exception as e:
            click.echo(f"\n❌ Failed to access album: {str(e)}", err=True)
            if verbose:
                traceback.print_exc()
            sys.exit(1)

        click.echo(f"✓ Found album: {album_name}\n")

        # Step 5: Get all image URLs
        click.echo("🔍 Finding images...")

        try:
            image_items = client.get_shared_album_images(
                encoded_url,
                recursive=not no_recursive
            )
        except Exception as e:
            click.echo(f"\n❌ Failed to enumerate images: {str(e)}", err=True)
            if verbose:
                traceback.print_exc()
            sys.exit(1)

        if not image_items:
            click.echo("✓ No images found in album.")
            sys.exit(0)

        click.echo(f"✓ Found {len(image_items)} image(s)\n")

        # Calculate total size
        from onedrive_downloader.utils import format_size
        total_size = sum(item.size for item in image_items)

        if verbose or dry_run:
            click.echo(f"Total size: {format_size(total_size)}\n")

        # Dry run: show what would be downloaded and exit
        if dry_run:
            output_path = Path(output) / album_name
            click.echo(f"📁 Would download to: {output_path}\n")
            click.echo("Files:")
            for item in image_items:
                click.echo(f"  • {item.filename} ({format_size(item.size)})")
            click.echo(f"\n✓ Dry run complete. {len(image_items)} file(s), {format_size(total_size)} total.")
            sys.exit(0)

        # Step 6: Download images
        output_path = Path(output) / album_name
        click.echo(f"⬇️  Downloading to: {output_path}")

        # Create progress bar
        progress_bar = tqdm(
            total=len(image_items),
            unit='image',
            desc='Downloading',
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
        )

        # Progress callback to update progress bar
        def on_progress(result):
            progress_bar.update(1)
            if verbose and not result.success:
                tqdm.write(f"  ✗ Failed: {result.filename} - {result.error}")

        # Run async download
        try:
            downloader = ImageDownloader(output_path, concurrent, retries)
            results = asyncio.run(downloader.download_all(image_items, on_progress))
        except Exception as e:
            progress_bar.close()
            click.echo(f"\n❌ Download failed: {str(e)}", err=True)
            if verbose:
                traceback.print_exc()
            sys.exit(1)
        finally:
            progress_bar.close()

        # Step 7: Display summary
        stats = downloader.get_stats(results)

        click.echo("\n" + "="*60)
        click.echo("✓ Download complete!")
        click.echo("="*60)
        click.echo(f"Total images:            {stats['total']}")

        if stats['downloaded'] > 0:
            click.echo(f"Newly downloaded:        {stats['downloaded']}")

        if stats['skipped'] > 0:
            click.echo(f"Skipped (already exist): {stats['skipped']}")

        if stats['failed'] > 0:
            click.echo(f"Failed:                  {stats['failed']}")

        click.echo(f"Total size:              {stats['total_size_formatted']}")
        click.echo(f"Location:                {output_path}")
        click.echo("="*60)

        # Show failed downloads if any
        if stats['failed'] > 0 and not verbose:
            click.echo("\nSome downloads failed. Use -v for detailed error messages.")

        # Exit with error code if any downloads failed
        if stats['failed'] > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Download interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {str(e)}", err=True)
        if verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
