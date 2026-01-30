"""Async image downloader with retry logic."""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Tuple
from onedrive_downloader.config import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_SECONDS, USER_AGENT
from onedrive_downloader.utils import sanitize_filename, format_size


class DownloadResult:
    """Result of a download operation."""

    def __init__(self, filename, success, error=None, size=0, skipped=False):
        self.filename = filename
        self.success = success
        self.error = error
        self.size = size
        self.skipped = skipped  # True if file already existed

    def __repr__(self):
        if self.skipped:
            return f"⊙ {self.filename} (skipped)"
        status = "✓" if self.success else "✗"
        return f"{status} {self.filename}"


class ImageDownloader:
    """Async downloader for images with retry logic and progress tracking."""

    def __init__(self, output_dir, concurrent=5, max_retries=DEFAULT_MAX_RETRIES):
        """
        Initialize the downloader.

        Args:
            output_dir: Directory to save downloaded images
            concurrent: Maximum number of concurrent downloads
            max_retries: Maximum retry attempts per image
        """
        self.output_dir = Path(output_dir)
        self.concurrent = concurrent
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_SECONDS)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def download_image(
        self,
        session,
        url,
        filename,
        semaphore,
        progress_callback=None
    ):
        """
        Download a single image with retry logic.

        Args:
            session: aiohttp ClientSession
            url: Download URL
            filename: Filename to save as
            semaphore: asyncio.Semaphore for rate limiting
            progress_callback: Optional callback(result) to call on completion

        Returns:
            DownloadResult
        """
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        output_path = self.output_dir / safe_filename

        # Check if file already exists
        if output_path.exists():
            file_size = output_path.stat().st_size
            result = DownloadResult(
                filename=safe_filename,
                success=True,
                size=file_size,
                skipped=True
            )
            if progress_callback:
                progress_callback(result)
            return result

        # Download with retry logic
        async with semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(url, timeout=self.timeout) as response:
                        response.raise_for_status()

                        # Stream download to file
                        total_size = 0
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                                total_size += len(chunk)

                        result = DownloadResult(
                            filename=safe_filename,
                            success=True,
                            size=total_size
                        )

                        if progress_callback:
                            progress_callback(result)

                        return result

                except asyncio.TimeoutError:
                    error_msg = f"Timeout (attempt {attempt + 1}/{self.max_retries})"
                    if attempt < self.max_retries - 1:
                        # Exponential backoff
                        await asyncio.sleep(2 ** attempt)
                    else:
                        result = DownloadResult(
                            filename=safe_filename,
                            success=False,
                            error=error_msg
                        )
                        if progress_callback:
                            progress_callback(result)
                        return result

                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    if attempt < self.max_retries - 1:
                        # Exponential backoff
                        await asyncio.sleep(2 ** attempt)
                    else:
                        # Clean up partial download
                        if output_path.exists():
                            output_path.unlink()

                        result = DownloadResult(
                            filename=safe_filename,
                            success=False,
                            error=error_msg
                        )
                        if progress_callback:
                            progress_callback(result)
                        return result

        # Should never reach here
        result = DownloadResult(
            filename=safe_filename,
            success=False,
            error="Unknown error"
        )
        if progress_callback:
            progress_callback(result)
        return result

    async def download_all(self, image_items, progress_callback=None):
        """
        Download all images concurrently.

        Args:
            image_items: List of (filename, url, size, mime_type) tuples
            progress_callback: Optional callback(result) to call on each completion

        Returns:
            List of DownloadResult objects
        """
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.concurrent)

        # Create session with custom headers
        connector = aiohttp.TCPConnector(limit=self.concurrent)
        async with aiohttp.ClientSession(
            connector=connector,
            headers={'User-Agent': USER_AGENT}
        ) as session:

            # Create download tasks
            tasks = []
            for filename, url, size, mime_type in image_items:
                task = self.download_image(
                    session,
                    url,
                    filename,
                    semaphore,
                    progress_callback
                )
                tasks.append(task)

            # Run all downloads concurrently
            results = await asyncio.gather(*tasks)

        return results

    def get_stats(self, results):
        """
        Get download statistics from results.

        Args:
            results: List of DownloadResult objects

        Returns:
            Dict with statistics: {
                'total': int,
                'successful': int,
                'failed': int,
                'skipped': int,
                'downloaded': int,
                'total_size': int,
                'total_size_formatted': str
            }
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        skipped = sum(1 for r in results if r.skipped)
        downloaded = successful - skipped
        failed = total - successful
        total_size = sum(r.size for r in results if r.success)

        return {
            'total': total,
            'successful': successful,
            'downloaded': downloaded,
            'skipped': skipped,
            'failed': failed,
            'total_size': total_size,
            'total_size_formatted': format_size(total_size)
        }


async def download_images(
    image_items,
    output_dir,
    concurrent=5,
    max_retries=DEFAULT_MAX_RETRIES,
    progress_callback=None
):
    """
    Convenience function to download images.

    Args:
        image_items: List of (filename, url, size, mime_type) tuples
        output_dir: Directory to save images
        concurrent: Maximum concurrent downloads
        max_retries: Maximum retry attempts per image
        progress_callback: Optional callback(result) on each completion

    Returns:
        List of DownloadResult objects

    Example:
        >>> results = await download_images(
        ...     image_items,
        ...     "./downloads/album",
        ...     concurrent=10
        ... )
        >>> successful = sum(1 for r in results if r.success)
        >>> print(f"Downloaded {successful}/{len(results)} images")
    """
    downloader = ImageDownloader(output_dir, concurrent, max_retries)
    results = await downloader.download_all(image_items, progress_callback)
    return results
