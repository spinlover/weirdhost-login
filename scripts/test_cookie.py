#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地 Cookie 有效性测试（无需浏览器 / 无需过 Cloudflare）

用法（Windows MINGW / CMD / PowerShell）：
    set WEIRDHOST_COOKIE_1=备注-----remember_web_xxx=值
    python scripts/test_cookie.py

直接用你的 Cookie 请求 Weirdhost API，判断 Cookie 是否有效：
  - 返回 200 且含 "data"          → Cookie 有效 ✅
  - 返回 HTML (<!DOCTYPE) / 401 / redirect → Cookie 无效或已过期 ❌
"""

import os
import sys
import asyncio
import aiohttp
from urllib.parse import unquote

DOMAIN = "hub.weirdhost.xyz"
API = f"https://{DOMAIN}/api/client?page=1"


def parse(raw):
    raw = raw.strip()
    if "-----" in raw:                      # 去掉可选备注前缀
        raw = raw.split("-----", 1)[1].strip()
    name, _, value = raw.partition("=")
    # 浏览器拷贝的 Cookie 值本身是 base64+URL 编码，发请求前需要还原成原始字节
    try:
        value = unquote(value)
    except Exception:
        pass
    return name.strip(), value.strip()


async def main():
    # 支持多种方式提供 Cookie：
    #   1) 命令行参数：python scripts/test_cookie.py "备注-----remember_web_xxx=值"
    #   2) 环境变量  ：WEIRDHOST_COOKIE_1=... python scripts/test_cookie.py
    #   3) 文件      ：python scripts/test_cookie.py --file cookie.txt（第1行放 Cookie）
    raw = ""
    if len(sys.argv) > 2 and sys.argv[1] == "--file":
        try:
            with open(sys.argv[2], "r", encoding="utf-8") as f:
                raw = f.read().strip()
        except OSError as e:
            print(f"读取文件失败: {e}")
            return
    else:
        raw = (sys.argv[1].strip() if len(sys.argv) > 1 else "") or os.environ.get("WEIRDHOST_COOKIE_1", "").strip()
    if not raw:
        print("未检测到 Cookie。")
        print("使用方式：")
        print('  python scripts/test_cookie.py "我的账号-----remember_web_xxx=值"')
        print('  或 python scripts/test_cookie.py --file cookie.txt')
        return

    name, value = parse(raw)
    if not name or not value:
        print("Cookie 格式错误：应为  remember_web_xxx=值")
        return

    print(f"Cookie 名 : {name}")
    print(f"Cookie 值 : (长度 {len(value)})  {value[:40]}...")
    print(f"请求      : {API}\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://{DOMAIN}/",
        "Cookie": f"{name}={value}",
    }

    async with aiohttp.ClientSession() as s:
        async with s.get(API, headers=headers, allow_redirects=False) as r:
            text = await r.text()
            ctype = r.headers.get("Content-Type", "?")
            print(f"HTTP 状态   : {r.status}")
            print(f"Content-Type: {ctype}")
            print(f"响应前300字 :\n{text[:300]}\n")
            loc = r.headers.get("Location")
            if loc:
                print(f"重定向到   : {loc}\n")

            if r.status == 200 and '"data"' in text:
                print("=" * 50)
                print("✅ Cookie 有效，服务器已返回服务器列表")
                print("=" * 50)
            else:
                print("=" * 50)
                print("❌ Cookie 无效 / 已过期（或账号无服务器）")
                print("   请重新登录网站，复制最新 remember_web_ Cookie 再试")
                print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
