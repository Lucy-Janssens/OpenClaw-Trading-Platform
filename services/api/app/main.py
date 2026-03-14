from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OpenClaw Trading Platform API",
    description="Backend for autonomous AI trading agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "OpenClaw Trading API is live"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/trades")
async def trades():
    return {
        "trades": [
            {"id": 1, "pair": "BTC-USD", "side": "buy", "qty": 0.5, "price": 48000.0},
            {"id": 2, "pair": "ETH-USD", "side": "sell", "qty": 2.0, "price": 3500.0},
        ]
    }


@app.get("/markets")
async def markets():
    return {
        "markets": [
            {"pair": "BTC-USD", "bid": 47980.0, "ask": 48020.0},
            {"pair": "ETH-USD", "bid": 3490.0, "ask": 3510.0},
        ]
    }
