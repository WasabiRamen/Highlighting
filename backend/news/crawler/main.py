import sys
from pathlib import Path

# backend 디렉토리를 Python 경로에 추가
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from contextlib import asynccontextmanager

from fastapi import FastAPI

from tools.naver_news import NaverNews
from tools.settings import settings

from shared.core.rabbitmq import RabbitMQClient, init_rabbitmq, get_rabbitmq

naver_news = NaverNews(
    client_id=settings.naver_client_id,
    client_secret=settings.naver_client_secret
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize RabbitMQ connection
    print(settings.rabbitmq_url)

    await init_rabbitmq(settings.rabbitmq_url, connection_name="news-crawler-service")
    yield
    # Shutdown: Close RabbitMQ connection
    rabbitmq = get_rabbitmq()
    await rabbitmq.close()


app = FastAPI(
    title="News Crawler Service",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """
    Root endpoint returning service status.
    """
    return {"service": "news-crawler", "status": "running"}


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


@app.get("/last-news/{stock}")
async def read_last_news(stock: str):
    """
    Retrieve the last 5 news articles for a given stock.
    """
    news = await naver_news.recent_5_news(stock)
    return news
