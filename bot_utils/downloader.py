import os
import httpx
import aiofiles
import asyncio
import time
from typing import Any, Dict

class Downloader:
    def __init__(self):
        self.client = httpx.AsyncClient(follow_redirects=True, timeout=120)
        self._stream_chunk_bytes = 524288

    async def _download_stream(self, url, filename, total_size, headers, progress, p_kwargs):
        interval = 1.5
        last_update = time.time()
        async with self.client.stream("GET", url, headers=headers, timeout=120) as r:
            r.raise_for_status()
            async with aiofiles.open(filename, "wb") as f:
                d_size = 0
                async for chunk in r.aiter_bytes(self._stream_chunk_bytes):
                    await f.write(chunk)
                    d_size += len(chunk)
                    if progress and time.time() - last_update >= interval:
                        await progress(d_size, total_size, **p_kwargs)
                        last_update = time.time()
        if progress: await progress(total_size, total_size, **p_kwargs)

    async def download_file(self, url, filename, user_agent, referer, cookies, progress=None, p_kwargs=None):
        filename = os.path.normpath(f"./downloads/{filename}")
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        p_kwargs = p_kwargs or {}
        
        headers = {'User-Agent': user_agent, 'Referer': referer, 'Cookie': cookies}
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                head_resp = await self.client.head(url, headers=headers)
                head_resp.raise_for_status()
                total_size = int(head_resp.headers.get("content-length", 0))
                
                if total_size == 0: raise RuntimeError("Could not determine file size.")

                await self._download_stream(url, filename, total_size, headers, progress, p_kwargs)
                return filename
            
            except (httpx.RequestError, httpx.ReadError, httpx.RemoteProtocolError) as e:
                print(f"Download attempt {attempt + 1} failed: {type(e).__name__}")
                if attempt + 1 == max_retries: raise
                await asyncio.sleep(3 * (attempt + 1))
