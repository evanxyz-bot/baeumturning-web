# website/scripts

## gen_news_static.py
`news.html` 의 JS 배열(`NEWS`)을 읽어 정적 `<article>` 마크업으로 펼쳐
`<!--NEWS_STATIC_START-->` ~ `<!--NEWS_STATIC_END-->` 사이에 다시 써 넣습니다.

**왜 필요한가** — 검색엔진과 AI 크롤러 상당수가 JS를 실행하지 않습니다.
정적 블록이 없으면 뉴스 63건이 크롤러에 125자로만 보입니다(펼치면 약 19,000자).

**언제 돌리나** — `news.html` 의 `NEWS` 배열을 고친 직후 반드시 1회.

```bash
python website/scripts/gen_news_static.py
```

실행 후 `git diff website/news.html` 로 정적 블록이 갱신됐는지 확인하고 커밋하세요.

## build_rss.py
`sitemap.xml` 의 loc·lastmod 를 읽어 각 페이지의 `<title>`·meta description 으로
RSS 2.0 피드 `rss.xml` 을 만듭니다(lastmod 내림차순, 최대 100건).

**왜 필요한가** — 네이버 서치어드바이저는 사이트맵과 **별개로 RSS 제출**을 받습니다.

**언제 돌리나** — 새 페이지를 올리거나 `sitemap.xml` 을 고친 직후 1회.

```bash
python website/scripts/build_rss.py
```
