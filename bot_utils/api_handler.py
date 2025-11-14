import httpx
import asyncio

class TeraboxAPI:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        self.headers = {'User-Agent': self.user_agent}
        self.client = httpx.AsyncClient(timeout=60, follow_redirects=True, headers=self.headers)
        self.api_callers = [self._call_api_1, self._call_api_2]

    async def _call_api_1(self, url):
        print("Attempting with API 1 (Vercel)...")
        api_url = f"https://terabox-downloader-api.vercel.app/api/get-download-link?url={url}"
        resp = await self.client.get(api_url)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success") or not data.get("response"): raise ValueError("API 1 failed or returned no files.")
        
        files = []
        for item in data["response"]:
            files.append({
                "name": item.get('file_name', 'N/A'),
                "size": self._parse_size(item.get("size", "0 B")),
                "dlink": item.get('download_link'),
                "thumb": item.get('thumbnail_link')
            })
        return files

    async def _call_api_2(self, url):
        print("Attempting with API 2 (Railway)...")
        api_url = f"https://teraap-production.up.railway.app/folder?url={url}"
        resp = await self.client.get(api_url)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("files"): raise ValueError("API 2 returned no files.")

        files = []
        for item in data["files"]:
            files.append({
                "name": item.get('file_name', 'N/A'),
                "size": item.get('size_bytes', 0),
                "dlink": item.get('download_link'),
                "thumb": item.get('thumbnail')
            })
        return files

    async def get_download_links(self, url):
        for api_func in self.api_callers:
            try:
                files = await api_func(url)
                if files:
                    print(f"Success with {api_func.__name__}")
                    return files
            except Exception as e:
                print(f"API call with {api_func.__name__} failed: {e}")
                await asyncio.sleep(1)
        
        raise ValueError("All available APIs failed to process this link.")

    def _parse_size(self, size_str: str) -> int:
        size_str = size_str.strip().upper()
        if not size_str: return 0
        units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        try:
            value_str, unit = size_str.split()
            return int(float(value_str) * units[unit])
        except (ValueError, KeyError): return 0

    async def get_thumbnail_content(self, url: str):
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.content
        except Exception:
            return None
