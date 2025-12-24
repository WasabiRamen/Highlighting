from fastapi import FastAPI

app = FastAPI(title="Accounts Service")


@app.get("/")
async def root():
    return {"service": "accounts", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
