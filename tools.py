import re
import httpx
import json
from typing import Optional, List
from urllib.parse import quote

SHORTENER_TEMPLATES = {
    "shrinkme.io": {"api_url": "https://shrinkme.io/api", "request_format": "{api_url}?api={api_key}&url={url}", "response_key": "shortenedUrl"},
    "shrinke.io": {"api_url": "https://shrinke.io/api", "request_format": "{api_url}?api={api_key}&url={url}", "response_key": "shortenedUrl"},
    "linksfly.me": {"api_url": "https://linksfly.me/api", "request_format": "{api_url}?api={api_key}&url={url}", "response_key": "shortenedUrl"},
    "droplink.co": {"api_url": "https://droplink.co/api", "request_format": "{api_url}?api={api_key}&url={url}", "response_key": "shortenedUrl"},
    "v2links.com": {"api_url": "https://v2links.com/api", "request_format": "{api_url}?api={api_key}&url={url}", "response_key": "shortenedUrl"}
}

def get_supported_domains() -> List[str]:
    return list(SHORTENER_TEMPLATES.keys())

async def shorten_url(domain: str, api_key: str, long_url: str) -> Optional[str]:
    if domain not in SHORTENER_TEMPLATES: return None
    template = SHORTENER_TEMPLATES[domain]
    try:
        full_api_url = template["request_format"].format(api_url=template["api_url"], api_key=api_key, url=quote(long_url))
        async with httpx.AsyncClient() as client:
            resp = await client.get(full_api_url)
            resp.raise_for_status()
            data = resp.json()
            if response_key := template.get("response_key"):
                if data.get("status") == "success": return data.get(response_key)
    except Exception:
        return None
    return None
