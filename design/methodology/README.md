# 분석 방법론 섹션 디자인 원본

`index.html` 의 `#analysis` 섹션(분석 파이프라인)을 만들 때 쓴 시안입니다.

| 파일 | 내용 |
|---|---|
| `Main.dc.html` | A · 명세 시트 (미채택) |
| `B.dc.html` | B · 3단계 그룹 (미채택) |
| `C.dc.html` | **C · 파이프라인 (채택 — 홈페이지 반영됨)** |
| `canvas.json` | 캔버스 배치·메모 |
| `preview.py` | `.dc.html` 을 브라우저에서 열리는 정적 HTML 로 변환 |

## 색 체계 (2계열 고정)

| 계열 | 색 | 뜻 | 쓰는 곳 |
|---|---|---|---|
| 관측 | `#dfba85` (`--s-amber`) | 기록에서 사실을 집계 | INPUT, STEP 1 진단 |
| 판단 | `#63d6bd` (`--s-teal`) | 사실에서 순서를 결정 | STEP 2 판정, STEP 3 처방, OUTPUT |

앰버는 새로 만든 색이 아니라 사이트 다크존 토큰에 이미 있던 값입니다.

## 다시 만들 때

```
python website/design/methodology/preview.py C.dc.html   # 정적 미리보기 생성
```

캔버스: https://claude.ai/code/artifact/6d312bab-20da-4017-9800-24fe959b9cda
