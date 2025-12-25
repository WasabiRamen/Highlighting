from fastapi import FastAPI

app = FastAPI(title="News Service")


@app.get("/")
async def root():
    return {"service": "news", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
