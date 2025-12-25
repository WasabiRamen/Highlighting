from fastapi import FastAPI

app = FastAPI(title="Auth Service")


@app.get("/")
async def root():
    return {"service": "auth", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
