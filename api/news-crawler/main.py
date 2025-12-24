from fastapi import FastAPI

app = FastAPI(title="News Crawler Service")


@app.get("/")
async def root():
    return {"service": "news-crawler", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
