"""百度百科浏览器读取与 KKBOX 官方歌曲资料读取。"""

from __future__ import annotations

from typing import Dict, Optional
from urllib.parse import parse_qs, unquote, urlencode, urlparse

import asyncio
import json
import os

from bs4 import BeautifulSoup
from playwright.async_api import Route, async_playwright


class BaikeReader:
    def __init__(self, proxy: str, timeout: int) -> None:
        self._timeout = timeout
        self._slots = asyncio.Semaphore(2)
        self._proxy: Optional[Dict[str, str]] = None
        if proxy:
            parsed = urlparse(proxy)
            self._proxy = {"server": f"{parsed.scheme}://{parsed.netloc.rsplit('@', 1)[-1]}"}
            if parsed.username is not None:
                self._proxy["username"] = unquote(parsed.username)
            if parsed.password is not None:
                self._proxy["password"] = unquote(parsed.password)

    @staticmethod
    async def _route(route: Route) -> None:
        host = urlparse(route.request.url).hostname or ""
        first_party = any(
            host == domain or host.endswith("." + domain)
            for domain in ("baidu.com", "bdimg.com", "bdstatic.com")
        )
        if not first_party or route.request.resource_type in {"image", "media", "font"}:
            await route.abort()
        else:
            await route.continue_()

    async def fetch_html(self, url: str) -> str:
        env = {
            key: value
            for key, value in os.environ.items()
            if key in {
                "PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR", "TEMP", "TMP",
                "SYSTEMROOT", "WINDIR", "USERPROFILE", "LOCALAPPDATA", "APPDATA",
                "DISPLAY", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS",
            }
        }
        async with asyncio.timeout(self._timeout), self._slots:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    executable_path=playwright.chromium.executable_path,
                    headless=True,
                    chromium_sandbox=True,
                    proxy=self._proxy,
                    env=env,
                    timeout=self._timeout * 1000,
                )
                try:
                    context = await browser.new_context(
                        accept_downloads=False, service_workers="block", locale="zh-CN"
                    )
                    await context.route("**/*", self._route)
                    page = await context.new_page()
                    await page.goto(url, wait_until="domcontentloaded", timeout=self._timeout * 1000)
                    await page.locator("h1").wait_for(state="visible", timeout=self._timeout * 1000)
                    return await page.content()
                finally:
                    await browser.close()


def kkbox_widget_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if parsed.hostname not in {"www.kkbox.com", "kkbox.com"} or len(parts) != 4 or parts[2] != "song":
        return None
    territory, language, _, song_id = parts
    return "https://widget.kkbox.com/v1/?" + urlencode({
        "id": song_id, "type": "song", "terr": territory.upper(),
        "lang": language.upper(), "autoplay": "false",
    })


def parse_kkbox_widget(html: str, source_url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    state = soup.select_one("[data-state]")
    if state is None:
        raise ValueError("KKBOX 官方嵌入页未返回结构化歌曲信息")
    data = json.loads(state["data-state"])["feed"]["data"]
    expected_id = parse_qs(urlparse(source_url).query)["id"][0]
    if data.get("song_crypt_id") != expected_id:
        raise ValueError("KKBOX 返回的歌曲 ID 与请求不一致")
    song = data.get("song_name")
    artist = data.get("artist_name")
    if not song or not artist:
        raise ValueError("KKBOX 官方嵌入页未返回歌曲和艺人信息")
    lines = [f"歌曲：{song}", f"艺人：{artist}"]
    if data.get("album_name"):
        lines.append(f"专辑：{data['album_name']}")
    if data.get("duration_ms") is not None:
        lines.append(f"时长：{data['duration_ms']} 毫秒")
    lines.extend([
        f"歌曲 ID：{expected_id}",
        f"资料来源：KKBOX 官方歌曲嵌入页 {source_url}",
        "此来源不包含原地区网页的完整歌词与专辑说明。",
    ])
    return "\n".join(lines)
