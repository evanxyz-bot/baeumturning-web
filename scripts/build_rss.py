# -*- coding: utf-8 -*-
"""sitemap.xml 을 읽어 website/rss.xml (RSS 2.0) 을 만든다.

네이버 서치어드바이저는 사이트맵과 별개로 RSS 제출을 받는다.
사이트맵의 loc·lastmod 를 그대로 쓰고, 각 loc 에 대응하는 로컬 html 에서
<title> 과 meta description 을 뽑아 item 을 채운다.

  python website/scripts/build_rss.py

새 페이지를 올리거나 sitemap.xml 을 고친 뒤 1회 돌린다.
"""
from __future__ import annotations

import html
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
OUT = ROOT / "rss.xml"
SITE = "https://outfocus.co.kr/"
KST = timezone(timedelta(hours=9))
MAX_ITEMS = 100

CHANNEL_TITLE = "아웃포커스 · 배움터닝"

WDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
DESC_RE = re.compile(
    r"<meta[^>]+name=[\"']description[\"'][^>]*>", re.I)
# content 안에 작은따옴표('배움터닝')가 들어가므로 여는 따옴표를 역참조로 닫는다
CONTENT_RE = re.compile(r"content=([\"'])(.*?)\1", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def rfc822(date_str: str) -> str:
    """'2026-09-18' → 'Thu, 18 Sep 2026 00:00:00 +0900'."""
    d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=KST)
    return "%s, %02d %s %04d %02d:%02d:%02d +0900" % (
        WDAY[d.weekday()], d.day, MON[d.month - 1], d.year,
        d.hour, d.minute, d.second)


def local_path(loc: str) -> Path | None:
    """loc → 로컬 html 파일 경로."""
    path = unquote(urlsplit(loc).path).lstrip("/")
    if path == "" or path.endswith("/"):
        path += "index.html"
    p = ROOT / path
    return p if p.is_file() else None


def clean(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    return " ".join(text.split())


def extract(p: Path) -> tuple[str, str]:
    src = p.read_text(encoding="utf-8", errors="replace")
    m = TITLE_RE.search(src)
    title = clean(m.group(1)) if m else p.stem
    desc = ""
    md = DESC_RE.search(src)
    if md:
        mc = CONTENT_RE.search(md.group(0))
        if mc:
            desc = clean(mc.group(2))
    return title, desc


def esc(text: str) -> str:
    return html.escape(text, quote=False).replace('"', "&quot;")


def main() -> int:
    tree = ET.parse(SITEMAP)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = []
    missing = []
    for url in tree.getroot().findall("s:url", ns):
        loc_el = url.find("s:loc", ns)
        if loc_el is None or not loc_el.text:
            continue
        loc = loc_el.text.strip()
        lm_el = url.find("s:lastmod", ns)
        lastmod = (lm_el.text or "").strip() if lm_el is not None else ""
        p = local_path(loc)
        if p is None:
            missing.append(loc)
            continue
        title, desc = extract(p)
        entries.append({"loc": loc, "lastmod": lastmod,
                        "title": title, "desc": desc})

    if missing:
        print("[warn] 로컬 파일을 못 찾은 loc %d 건" % len(missing))
        for loc in missing[:5]:
            print("  -", loc)

    entries.sort(key=lambda e: (e["lastmod"], e["loc"]), reverse=True)
    entries = entries[:MAX_ITEMS]

    index = ROOT / "index.html"
    _, channel_desc = extract(index)

    now = datetime.now(KST)
    build_date = "%s, %02d %s %04d %02d:%02d:%02d +0900" % (
        WDAY[now.weekday()], now.day, MON[now.month - 1], now.year,
        now.hour, now.minute, now.second)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        "<title>%s</title>" % esc(CHANNEL_TITLE),
        "<link>%s</link>" % SITE,
        "<description>%s</description>" % esc(channel_desc),
        "<language>ko</language>",
        "<lastBuildDate>%s</lastBuildDate>" % build_date,
        '<atom:link href="%srss.xml" rel="self" type="application/rss+xml" />'
        % SITE,
    ]
    for e in entries:
        parts.append("<item>")
        parts.append("<title>%s</title>" % esc(e["title"]))
        parts.append("<link>%s</link>" % esc(e["loc"]))
        if e["desc"]:
            parts.append("<description>%s</description>" % esc(e["desc"]))
        if e["lastmod"]:
            parts.append("<pubDate>%s</pubDate>" % rfc822(e["lastmod"]))
        parts.append('<guid isPermaLink="true">%s</guid>' % esc(e["loc"]))
        parts.append("</item>")
    parts.append("</channel>")
    parts.append("</rss>")

    doc = "\n".join(parts) + "\n"
    OUT.write_text(doc, encoding="utf-8")

    ET.parse(OUT)  # well-formed 확인
    print("[ok] %s — item %d 건" % (OUT.name, len(entries)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
