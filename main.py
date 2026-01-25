from fastapi import FastAPI, HTTPException
from schemas import PatternRequest
from services import fetch_ohlcv, fetch_latest_price
from pattern_engine import detect_patterns

app = FastAPI(title="CSE Volume Pattern Detection API")


@app.post("/analyze-pattern")
def analyze_pattern(payload: PatternRequest):
    try:
        print(1)
        data = fetch_ohlcv(payload.company_symbol)
        patterns = detect_patterns(data)
        print(2)
        latest_pattern = patterns[-1] if patterns else None
        print(3)
        latest_price = fetch_latest_price(payload.company_symbol)
        print(4)
        last_50 = data.tail(50).reset_index().to_dict(orient="records")

        return {
            "company_symbol": payload.company_symbol,
            "latest_price": latest_price,
            "latest_pattern": latest_pattern,
            "last_50_days_ohlcv": last_50
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
