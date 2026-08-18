# -*- coding: utf-8 -*-
"""content/blog/*.md 를 읽어 블로그 목록(blog.html)과 글 페이지(blog-{slug}.html)를 만든다.

네비·푸터·브랜드 CSS는 qna.html 에서 빌드 시점에 그대로 떠 온다.
따라서 사이트 네비가 바뀌면 이 스크립트를 다시 돌리기만 하면 블로그도 따라온다.

사용:  python website/scripts/build_blog.py
"""
import io, os, re, sys, json, html, glob

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
ROOT = os.path.abspath(ROOT)
SRC = os.path.join(ROOT, "content", "blog")
DONOR = os.path.join(ROOT, "qna.html")
BASE = "https://outoffocus-edu.vercel.app/"

# 대표 승인 전에는 색인을 막는다. 승인 후 True 로 바꾸고 다시 빌드하면 noindex 가 빠진다.
PUBLISHED = False


# ───────────────────────────────── 껍데기 추출 ─────────────────────────────────
def slice_between(s, start, end, what):
    i = s.find(start)
    if i < 0:
        sys.exit("qna.html 에서 %s 시작점(%s)을 찾지 못했습니다." % (what, start))
    j = s.find(end, i)
    if j < 0:
        sys.exit("qna.html 에서 %s 끝점(%s)을 찾지 못했습니다." % (what, end))
    return s[i:j + len(end)]


def load_shell():
    s = io.open(DONOR, encoding="utf-8").read()
    return {
        "css": slice_between(s, "<style>", "</style>", "스타일 블록"),
        "symbol": slice_between(s, '<svg width="0" height="0"', "</svg>", "조리개 심볼"),
        # 도너 페이지의 활성 표시(class="active")는 떼고 가져온다
        "nav": slice_between(s, '<nav class="nav" id="nav">', "</nav>", "네비")
                   .replace(' class="active"', ''),
        "foot": slice_between(s, '<footer class="foot">', "</footer>", "푸터"),
        "script": slice_between(s, "<script>\n// nav scrolled", "</script>", "공통 스크립트"),
        "fonts": slice_between(s, '<link rel="preconnect"', "pretendardvariable-dynamic-subset.min.css\">",
                               "폰트 링크"),
    }


# ───────────────────────────────── 마크다운 변환 ─────────────────────────────────
# 초안 형식이 제한적(blog-routine.md)이라 필요한 문법만 다룬다.
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"==(.+?)==", r'<mark class="pen">\1</mark>', t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md_to_html(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()

        if not st:
            i += 1
            continue

        if st == "---":
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{2,4})\s+(.*)$", st)
        if m:
            lv = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv))
            i += 1
            continue

        # 인용 = 두괄식 핵심 답변 박스 (AI 인용을 노리는 자리)
        if st.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                buf.append(lines[i].strip()[2:])
                i += 1
            out.append('<div class="answer"><span class="answer-tag">한 줄 답</span><p>%s</p></div>'
                       % inline(" ".join(buf)))
            continue

        # 표
        if st.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if len(rows) >= 2 and set("".join(rows[1]).replace(" ", "")) <= set("-:"):
                head, body = rows[0], rows[2:]
            else:
                head, body = None, rows
            t = ['<div class="tw"><table>']
            if head:
                t.append("<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in head) + "</tr></thead>")
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        # 목록
        m = re.match(r"^(\d+)\.\s+", st)
        if st.startswith("- ") or m:
            tag = "ol" if m else "ul"
            pat = r"^\d+\.\s+" if m else r"^-\s+"
            items = []
            while i < len(lines):
                s2 = lines[i].strip()
                if not re.match(pat, s2):
                    break
                items.append(re.sub(pat, "", s2))
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
            continue

        # 문단
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{2,4}\s|>\s|\||-\s|\d+\.\s|---$)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    return "\n".join(out)


# ───────────────────────────────── 원고 읽기 ─────────────────────────────────
def read_posts():
    posts = []
    for f in sorted(glob.glob(os.path.join(SRC, "*.md"))):
        raw = io.open(f, encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            sys.exit("%s: 앞머리(--- ... ---)가 없습니다." % os.path.basename(f))
        meta = {}
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2).strip()
        for need in ("title", "slug", "date", "desc", "tag"):
            if not meta.get(need):
                sys.exit("%s: 앞머리에 %s 가 없습니다." % (os.path.basename(f), need))
        if meta.get("draft", "").lower() in ("true", "1", "y"):
            print("  건너뜀(초안): %s" % meta["slug"])
            continue
        plain = re.sub(r"[#>*=`|\-\[\]()]", "", body)
        meta["body"] = body
        meta["html"] = md_to_html(body)
        meta["mins"] = max(1, round(len(plain) / 500.0))
        meta["file"] = "blog-%s.html" % meta["slug"]
        posts.append(meta)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ───────────────────────────────── 블로그 전용 CSS ─────────────────────────────────
BLOG_CSS = """
<style>
/* ===== 블로그 — 읽기 위주 밝은 톤 ===== */
.bl-head{padding:56px 0 26px;background:linear-gradient(180deg,#f6faf9 0%,#fbfdfd 100%);
  border-bottom:1px solid var(--border)}
.bl-head .wrap{max-width:760px}
.bl-crumb{font-size:13px;color:var(--text-3);margin-bottom:16px}
.bl-crumb a{color:var(--text-3);text-decoration:none}
.bl-crumb a:hover{color:var(--accent-strong)}
.bl-head h1{font-family:'GmarketSans',sans-serif;font-weight:700;letter-spacing:-.02em;
  font-size:clamp(27px,3.4vw,40px);line-height:1.34;color:var(--text);
  text-wrap:balance;word-break:keep-all}
.bl-head .lead{margin-top:14px;font-size:16px;line-height:1.8;color:var(--text-2);
  text-wrap:pretty;word-break:keep-all}
.bl-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:20px;
  font-size:13px;color:var(--text-3)}
.bl-tag{background:var(--accent-soft);color:var(--accent-strong);font-weight:700;
  font-size:12px;padding:4px 11px;border-radius:20px}
.bl-dot{color:var(--border-strong)}

/* 본문 */
.bl-body{padding:44px 0 76px}
.bl-body .wrap{max-width:760px}
.article{background:#fff;border:1px solid var(--border);border-radius:18px;
  padding:clamp(24px,4vw,52px);box-shadow:0 1px 2px rgba(20,40,36,.04),0 10px 30px rgba(20,40,36,.045)}
.article>*:first-child{margin-top:0}
.article p{font-size:17px;line-height:1.92;color:#2b3038;margin:0 0 22px;
  text-wrap:pretty;word-break:keep-all}
.article h2{font-family:'GmarketSans',sans-serif;font-weight:700;font-size:22px;line-height:1.5;
  color:var(--text);margin:42px 0 16px;padding-left:14px;border-left:4px solid var(--accent);
  word-break:keep-all}
.article h3{font-weight:800;font-size:17.5px;color:var(--text);margin:30px 0 12px;word-break:keep-all}
.article b{font-weight:700;color:#1b1f26}
.article a{color:var(--accent-strong);text-decoration:none;
  border-bottom:1.5px solid var(--accent-mid);padding-bottom:1px}
.article a:hover{border-bottom-color:var(--accent)}
.article ul,.article ol{margin:0 0 22px;padding-left:22px}
.article li{font-size:17px;line-height:1.86;color:#2b3038;margin-bottom:9px;word-break:keep-all}
.article li::marker{color:var(--accent)}
.article hr{border:0;border-top:1px dashed var(--border-strong);margin:38px 0}
.article code{background:var(--surface-3);padding:2px 6px;border-radius:5px;font-size:14.5px}
/* 형광펜 — 앱과 같은 결 */
.article mark.pen{background:linear-gradient(transparent 58%,rgba(154,215,205,.62) 58%,
  rgba(154,215,205,.62) 94%,transparent 94%);color:inherit;padding:0 2px}

/* 두괄식 핵심 답변 — AI 인용을 노리는 자리 */
.answer{background:#f0f8f6;border-left:4px solid var(--accent);border-radius:0 12px 12px 0;
  padding:20px 24px;margin:0 0 30px}
.answer-tag{display:inline-block;font-size:11.5px;font-weight:800;letter-spacing:.05em;
  color:var(--accent-strong);margin-bottom:8px}
.answer p{margin:0;font-size:17px;line-height:1.85;color:#1f2a28;font-weight:500}

/* 표 */
.tw{overflow-x:auto;margin:0 0 26px}
.article table{border-collapse:collapse;width:100%;min-width:420px;font-size:15.5px}
.article th{text-align:left;font-weight:800;color:var(--text-3);font-size:12.5px;
  letter-spacing:.03em;padding:0 14px 10px;border-bottom:1px solid var(--border-strong)}
.article td{padding:14px;border-bottom:1px solid var(--border);color:#2b3038;
  line-height:1.7;vertical-align:top;word-break:keep-all}
.article tbody tr:last-child td{border-bottom:0}

/* 글 하단 */
.bl-foot{max-width:760px;margin:30px auto 0}
.bl-src{font-size:13.6px;line-height:1.88;color:var(--text-2);
  padding:18px 22px;background:var(--surface-2);border-radius:12px}
.bl-cta{margin-top:20px;display:flex;align-items:center;gap:18px;flex-wrap:wrap;
  background:#fff;border:1px solid var(--border);border-radius:16px;padding:24px 26px}
.bl-cta .t{flex:1;min-width:240px}
.bl-cta b{display:block;font-size:16.5px;margin-bottom:6px;color:var(--text)}
.bl-cta p{font-size:14.4px;line-height:1.72;color:var(--text-2);margin:0;word-break:keep-all}
.bl-cta a{flex-shrink:0;background:var(--accent);color:#fff;text-decoration:none;
  font-weight:700;font-size:14.6px;padding:12px 22px;border-radius:11px;
  box-shadow:0 3px 0 var(--accent-strong)}
.bl-cta a:hover{transform:translateY(1px);box-shadow:0 2px 0 var(--accent-strong)}
.bl-nav{margin-top:26px;text-align:center}
.bl-nav a{color:var(--accent-strong);text-decoration:none;font-weight:700;font-size:14.6px}

/* 목록 */
.bl-list{display:flex;flex-direction:column;gap:14px;max-width:760px;margin:0 auto}
.bl-card{display:block;text-decoration:none;background:#fff;border:1px solid var(--border);
  border-radius:16px;padding:24px 26px;transition:border-color .2s,box-shadow .2s,transform .2s}
.bl-card:hover{border-color:var(--accent-mid);transform:translateY(-2px);
  box-shadow:0 8px 22px rgba(20,40,36,.07)}
.bl-card h2{font-family:'GmarketSans',sans-serif;font-weight:700;font-size:19.5px;line-height:1.5;
  color:var(--text);margin:10px 0 8px;word-break:keep-all}
.bl-card p{font-size:14.8px;line-height:1.75;color:var(--text-2);margin:0;word-break:keep-all}
.bl-empty{max-width:760px;margin:0 auto;text-align:center;background:#fff;
  border:1px dashed var(--border-strong);border-radius:16px;padding:56px 24px}
.bl-empty b{display:block;font-size:17px;margin-bottom:10px;color:var(--text)}
.bl-empty p{font-size:14.6px;line-height:1.75;color:var(--text-2);margin:0}
@media (max-width:640px){
  .article p,.article li{font-size:16.2px}
  .bl-cta{flex-direction:column;align-items:flex-start}
}
</style>
"""


def head(title, desc, url, extra_ld=""):
    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:type" content="article">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:locale" content="ko_KR">
<meta property="og:image" content="%sbrand/outfocus-mark-2048.png">
<meta name="robots" content="%s">
<meta name="theme-color" content="#0b7a6a">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
%s
%s
%s
</head>
""" % (html.escape(title), html.escape(desc), url, html.escape(title), html.escape(desc),
       BASE, "index,follow" if PUBLISHED else "noindex,nofollow",
       SHELL["fonts"], SHELL["css"], BLOG_CSS + extra_ld)


def page(inner):
    return "<body>\n\n%s\n\n%s\n\n%s\n\n%s\n</body>\n</html>\n" % (
        SHELL["symbol"], SHELL["nav"], inner, SHELL["foot"] + "\n" + SHELL["script"])


def build_post(p, posts):
    url = BASE + p["file"]
    ld = {"@context": "https://schema.org", "@type": "BlogPosting",
          "headline": p["title"], "description": p["desc"],
          "datePublished": p["date"], "dateModified": p.get("updated", p["date"]),
          "inLanguage": "ko-KR", "mainEntityOfPage": url,
          "author": {"@type": "Organization", "name": "아웃포커스", "url": BASE},
          "publisher": {"@id": BASE + "#organization"},
          "articleSection": p["tag"]}
    if p.get("keywords"):
        ld["keywords"] = p["keywords"]
    ldtag = '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(ld, ensure_ascii=False, indent=1)

    others = [q for q in posts if q["slug"] != p["slug"]][:3]
    rel = ""
    if others:
        rel = '<div class="bl-list" style="margin-top:34px">' + "".join(
            '<a class="bl-card" href="%s"><span class="bl-tag">%s</span><h2>%s</h2><p>%s</p></a>'
            % (q["file"], html.escape(q["tag"]), html.escape(q["title"]), html.escape(q["desc"]))
            for q in others) + "</div>"

    inner = """<header class="bl-head">
  <div class="wrap">
    <div class="bl-crumb"><a href="index.html">홈</a> · <a href="blog.html">배움 기록</a> · <b>%s</b></div>
    <h1>%s</h1>
    <div class="bl-meta"><span class="bl-tag">%s</span><span>%s</span>
      <span class="bl-dot">·</span><span>약 %d분</span></div>
  </div>
</header>

<section class="bl-body">
  <div class="wrap">
    <article class="article">
%s
    </article>
    <div class="bl-foot">
      <p class="bl-src">이 글은 공개된 제도 정보와 배움터닝이 보유한 검정고시 기출 데이터를 바탕으로 작성했습니다.
        시험 일정·요강은 <b>거주지 관할 시·도교육청 공고</b>로 확정되며, 이 글은 공식 공고를 대체하지 않습니다.</p>
      <div class="bl-cta">
        <div class="t"><b>어디가 약한지부터 알고 시작하세요</b>
          <p>기출을 실제 시험처럼 풀면 자동 채점되고, 실점이 몰린 단원을 짚어 줍니다. 채점은 무료입니다.</p></div>
        <a href="app.html">배움터닝 보기</a>
      </div>
      %s
      <div class="bl-nav"><a href="blog.html">← 배움 기록 전체 보기</a></div>
    </div>
  </div>
</section>""" % (html.escape(p["tag"]), html.escape(p["title"]), html.escape(p["tag"]),
                 p["date"].replace("-", ". "), p["mins"], p["html"], rel)

    io.open(os.path.join(ROOT, p["file"]), "w", encoding="utf-8", newline="").write(
        head(p["title"] + " — 아웃포커스", p["desc"], url, ldtag) + page(inner))


def build_index(posts):
    url = BASE + "blog.html"
    ld = {"@context": "https://schema.org", "@type": "Blog", "url": url,
          "name": "배움 기록 — 아웃포커스", "inLanguage": "ko-KR",
          "description": "검정고시 제도와 공부법을 근거와 함께 정리합니다.",
          "publisher": {"@id": BASE + "#organization"},
          "blogPost": [{"@type": "BlogPosting", "headline": p["title"],
                        "url": BASE + p["file"], "datePublished": p["date"]} for p in posts]}
    ldtag = '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(ld, ensure_ascii=False, indent=1)

    if posts:
        body = '<div class="bl-list">' + "".join(
            '<a class="bl-card" href="%s"><span class="bl-tag">%s</span><h2>%s</h2><p>%s</p></a>'
            % (p["file"], html.escape(p["tag"]), html.escape(p["title"]), html.escape(p["desc"]))
            for p in posts) + "</div>"
    else:
        body = ('<div class="bl-empty"><b>첫 글을 준비하고 있습니다</b>'
                '<p>검정고시 제도와 공부법을 근거와 함께 하나씩 정리해 올릴 예정입니다.</p></div>')

    inner = """<header class="bl-head">
  <div class="wrap">
    <div class="bl-crumb"><a href="index.html">홈</a> · <b>배움 기록</b></div>
    <h1>배움 기록</h1>
    <p class="lead">검정고시 제도와 공부법을, 어디서 나온 이야기인지 밝히면서 정리합니다.
      혼자 준비하는 사람이 검색해서 바로 쓸 수 있는 글을 씁니다.</p>
  </div>
</header>

<section class="bl-body">
  <div class="wrap">
%s
  </div>
</section>""" % body

    io.open(os.path.join(ROOT, "blog.html"), "w", encoding="utf-8", newline="").write(
        head("배움 기록 — 검정고시 제도와 공부법 | 아웃포커스",
             "검정고시 합격 기준, 과목합격, 공부 순서 등 혼자 준비하는 사람에게 필요한 정보를 근거와 함께 정리합니다.",
             url, ldtag) + page(inner))


if __name__ == "__main__":
    if not os.path.isdir(SRC):
        os.makedirs(SRC)
    SHELL = load_shell()
    posts = read_posts()
    for p in posts:
        build_post(p, posts)
    build_index(posts)
    print("ok: 글 %d편 + 목록 1개 생성" % len(posts))
    for p in posts:
        print("   %s  (%s, 약 %d분)" % (p["file"], p["tag"], p["mins"]))
