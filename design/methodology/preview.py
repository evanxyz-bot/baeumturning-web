# -*- coding: utf-8 -*-
"""*.dc.html 을 브라우저에서 그냥 열리는 정적 HTML 로 바꿔 미리보기한다."""
import io, re, sys, os
sys.stdout.reconfigure(encoding="utf-8")
src = sys.argv[1]
s = io.open(src, encoding="utf-8").read()
helmet = re.search(r"<helmet>(.*?)</helmet>", s, re.S).group(1)
body = re.search(r"<x-dc>(.*?)</x-dc>", s, re.S).group(1)
body = body.replace(helmet, "").replace("<helmet>", "").replace("</helmet>", "")
out = "<!doctype html><html lang=ko><head><meta charset=utf-8>%s</head><body>%s</body></html>" % (helmet, body)
dst = os.path.splitext(os.path.basename(src))[0] + ".preview.html"
io.open(dst, "w", encoding="utf-8").write(out)
print(dst)
