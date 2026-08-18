# -*- coding: utf-8 -*-
"""news.html 의 var NEWS=[...] 배열을 읽어 동일 내용을 정적 HTML 로 렌더해
   <!--NEWS_STATIC_START--> ~ <!--NEWS_STATIC_END--> 사이에 채워 넣는다.
   항목을 추가·수정한 뒤 다시 실행하면 정적 블록도 그대로 갱신된다."""
import json, re, io, sys

PATH = r"C:/Users/dol37/Desktop/GED App/website/news.html"

s = io.open(PATH, encoding="utf-8").read()
i = s.index("var NEWS=[")
j = s.index("\n];", i)
data = json.loads(s[i + len("var NEWS="):j + 2])

# JS 정렬과 동일: 고정 글 우선 → 날짜 내림차순
data.sort(key=lambda n: (0 if n.get("pinned") else 1, [-int(x) for x in n["date"].split("-")]))


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(t):
    return esc(t).replace('"', "&quot;")


def fmt_k(d):
    y, m, dd = d.split("-")
    return "%s년 %d월 %d일" % (y, int(m), int(dd))


out = []
out.append('    <div class="news-static" id="news-static">')
out.append('      <h2 class="ns-h">자료 전체 목록</h2>')
out.append('      <p class="ns-lead">공식 기관 출처 자료 %d건 · 최신순</p>' % len(data))

seen = {}
for n in data:
    base = "n-" + n["date"]
    seen[base] = seen.get(base, 0) + 1
    nid = base if seen[base] == 1 else "%s-%d" % (base, seen[base])

    out.append('      <article class="ns-item" id="%s">' % nid)
    out.append('        <h3>%s</h3>' % esc(n["title"]))
    meta = '        <p class="ns-meta">'
    if n.get("pinned"):
        meta += '<span class="ns-pin">고정 공지</span>'
    meta += '<span class="ns-tag">%s</span><time datetime="%s">%s</time></p>' % (
        esc(n["tag"]), n["date"], fmt_k(n["date"]))
    out.append(meta)
    out.append('        <ul class="ns-sum">')
    for x in n["sum"]:
        out.append('          <li>%s</li>' % x)
    out.append('        </ul>')
    out.append('        <p class="ns-src">출처 · <cite>%s</cite></p>' % esc(n["src"]))
    links = n.get("links") or []
    if links:
        out.append('        <p class="ns-links">' + "".join(
            '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc_attr(l["u"]), esc(l["t"]))
            for l in links) + '</p>')
    out.append('      </article>')

out.append('    </div>')

block = "\n" + "\n".join(out) + "\n"
new = re.sub(r"<!--NEWS_STATIC_START-->.*?<!--NEWS_STATIC_END-->",
             lambda m: "<!--NEWS_STATIC_START-->" + block + "<!--NEWS_STATIC_END-->",
             s, flags=re.S)
if new == s:
    print("marker not found / unchanged")
    sys.exit(1)
io.open(PATH, "w", encoding="utf-8", newline="").write(new)
print("ok: %d items, static block %d chars" % (len(data), len(block)))
