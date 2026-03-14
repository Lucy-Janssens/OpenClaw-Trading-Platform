from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="OpenClaw Trading Platform API",
    description="Backend for autonomous AI trading agents",
    version="0.1.0"
)

# CORS configuration for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "OpenClaw Trading API is live"}

@app.get("/health")
async def health():
    return {"status": "healthy", "services": {"db": "up", "adapters": "running"}}

# TODO: Add routers for /trading, /account, /guardrails, /admin

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
