import os
import httpx
import aiofiles
import asyncio
import time
from typing import Any, Dict

class Downloader:
    def __init__(self):
        self.client = httpx.AsyncClient(follow_redirects=True, timeout=120)
        self.chunk_size = 10 * 1024 * 1024  # Download in 10MB chunks

    async def _download_chunk_with_retry(self, url: str, headers: Dict[str, str], start: int, end: int):
        """Downloads a single chunk of a file with aggressive retries."""
        chunk_headers = headers.copy()
        chunk_headers['Range'] = f"bytes={start}-{end}"
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                async with self.client.stream("GET", url, headers=chunk_headers, timeout=60) as response:
                    response.raise_for_status()
                    content = await response.aread()
                    return content
            except (httpx.RequestError, httpx.ReadError, httpx.RemoteProtocolError) as e:
                print(f"Chunk from {start} to {end} failed on attempt {attempt + 1}/{max_retries}: {type(e).__name__}")
                if attempt + 1 == max_retries:
                    raise  # Re-raise the exception on the final attempt
                await asyncio.sleep(2 * (attempt + 1)) # Wait longer after each failure
        return None

    async def download_file(
        self,
        url: str,
        filename: str,
        user_agent: str,
        referer: str,
        cookies: str,
        progress: Any | None = None,
        p_kwargs: Dict[str, Any] | None = None,
    ):
        """The main download function using the resumable chunk downloader."""
        filename = os.path.normpath(f"./downloads/{filename}")
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        p_kwargs = p_kwargs or {}
        
        headers = {'User-Agent': user_agent, 'Referer': referer, 'Cookie': cookies}

        try:
            head_resp = await self.client.head(url, headers=headers)
            head_resp.raise_for_status()
            total_size = int(head_resp.headers.get("content-length", 0))
            
            if total_size == 0:
                raise RuntimeError("Could not determine file size.")

            async with aiofiles.open(filename, "wb") as f:
                downloaded_size = 0
                for start in range(0, total_size, self.chunk_size):
                    end = min(start + self.chunk_size - 1, total_size - 1)
                    
                    chunk_content = await self._download_chunk_with_retry(url, headers, start, end)
                    
                    if chunk_content:
                        await f.write(chunk_content)
                        downloaded_size += len(chunk_content)
                        if progress:
                            await progress(downloaded_size, total_size, **p_kwargs)
                    else:
                        raise RuntimeError(f"Failed to download chunk {start}-{end} after all retries.")

            if progress:
                await progress(total_size, total_size, **p_kwargs)
            
            return filename

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise type(e)("Download link was rejected by the server (403 Forbidden). The link may be expired or invalid.")
            else:
                raise
        except Exception as e:
            print(f"An error occurred during download setup: {e}")
            raise

    async def close(self):
        await self.client.aclose()