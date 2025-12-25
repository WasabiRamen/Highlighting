from enum import Enum
from typing import Literal
import html
import re
import asyncio
import random

from httpx import AsyncClient
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------------


class NaverNewsURL(str, Enum):
    NEWS_SEARCH_JSON = "https://openapi.naver.com/v1/search/news.json"
    NEWS_SEARCH_XML = "https://openapi.naver.com/v1/search/news.xml"


# ---------------------------------------------------------------------------------


class NaverNewsErrorCode(str, Enum):
    """
    네이버 뉴스 검색 API 오류 코드
    
    자세한 오류 내용은 아래 링크에서
    https://developers.naver.com/docs/serviceapi/search/news/news.md
    """
    SE01 = "SE01"  # 400 - Incorrect query request (잘못된 쿼리요청입니다.)
    SE02 = "SE02"  # 400 - Invalid display value (부적절한 display 값입니다.)
    SE03 = "SE03"  # 400 - Invalid start value (부적절한 start 값입니다.)
    SE04 = "SE04"  # 400 - Invalid sort value (부적절한 sort 값입니다.)
    SE05 = "SE05"  # 404 - Invalid search api (존재하지 않는 검색 api 입니다.)
    SE06 = "SE06"  # 400 - Malformed encoding (잘못된 형식의 인코딩입니다.)
    SE99 = "SE99"  # 500 - System Error (시스템 에러)


# ---------------------------------------------------------------------------------


class NaverNewsParams(BaseModel):
    query: str = Field(..., description="검색을 원하는 질의어")
    display: int = Field(10, ge=1, le=100, description="한 번에 표시할 검색 결과 개수 (기본값: 10, 최댓값: 100)")
    start: int = Field(1, ge=1, le=1000, description="검색 시작 위치 (기본값: 1, 최댓값: 1000)")
    sort: Literal["sim", "date"] = Field("sim", description="검색 결과 정렬 방법 ('sim': 정확도순, 'date': 날짜순)")


# ---------------------------------------------------------------------------------
    

class NaverNews:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    def __clean_html_tags(self, text: str) -> str:
        text = html.unescape(text)
        return BeautifulSoup(text, "html.parser").get_text()
    

    async def __crawl_clean_news(self, url: str) -> str:
        async with AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        article = soup.find("div", {"id": "newsct_article"})
        if article:
            for selector in ['.media_end_head', '.ad', '.end_photo_org', 'script', 'style']:
                for tag in article.select(selector):
                    tag.decompose()

            text = article.get_text(separator="\n").strip()
            text = re.sub(r'\n.*?기자\n', '\n', text)

        else:
            text = soup.get_text(separator="\n").strip()

        text = re.sub(r'\n+', '\n', text).strip()
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        return text


    async def get_news(self, params: NaverNewsParams) -> dict:
        async with AsyncClient() as client:
            response = await client.get(NaverNewsURL.NEWS_SEARCH_JSON, headers=self.headers, params=params.model_dump())
            response.raise_for_status()
            return response.json()

    async def recent_5_news(self, query: str) -> dict:
        params = NaverNewsParams(
            query=query,
            display=5,
            start=1,
            sort="date"
        )

        response = await self.get_news(params)
        contents = []
        
        for item in response.get("items", []):
            content = await self.__crawl_clean_news(item["link"])
            await asyncio.sleep(random.uniform(0.2, 2))  # Be polite to the server
            title = self.__clean_html_tags(item["title"])

            contents.append({
                "title": title,
                "link": item["link"],
                "content": content
            })

        return contents

# ---------------------------------------------------------------------------------