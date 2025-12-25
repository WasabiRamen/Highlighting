# News Crawler

네이버 뉴스 검색 API를 활용한 주식 뉴스 크롤러

## 기술 스택

- **FastAPI** - 웹 프레임워크
- **Pydantic** - 데이터 검증
- **httpx** - HTTP 클라이언트
- **BeautifulSoup4** - HTML 파싱

## 주요 기능

- 네이버 뉴스 검색 API 연동
- 주식 종목별 최신 뉴스 5개 조회
- HTML 태그 제거 및 본문 추출
- API 파라미터 자동 검증

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 네이버 API 키를 입력:

```env
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
```

### 3. 서버 실행

```bash
fastapi run
```

또는 개발 모드:

```bash
fastapi dev
```

## API 엔드포인트

### GET `/last-news/{stock}`

특정 주식 종목의 최신 뉴스 5개를 조회합니다.

**요청 예시:**
```bash
curl http://localhost:8000/last-news/삼성전자
```

**응답 예시:**
```json
[
  {
    "title": "삼성전자, 신규 반도체 공장 건설 발표",
    "link": "https://...",
    "content": "삼성전자가 오늘..."
  }
]
```

## 프로젝트 구조

```
news_crawler/
├── app/
│   ├── main.py              # FastAPI 앱
│   └── tools/
│       ├── naver_news.py    # 네이버 뉴스 API 클라이언트
│       └── settings.py      # 환경 변수 설정
├── .env                     # 환경 변수 (gitignore)
├── requirements.txt         # 의존성
└── README.md
```

## 네이버 뉴스 API

- **문서**: https://developers.naver.com/docs/serviceapi/search/news/news.md
- **파라미터 검증**:
  - `display`: 1~100
  - `start`: 1~1000
  - `sort`: 'sim' (정확도순) 또는 'date' (날짜순)


** 이 문서는 AI로 생성된 README 입니다. **