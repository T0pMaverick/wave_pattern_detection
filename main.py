from fastapi import FastAPI, HTTPException
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
import time
from pandas.tseries.offsets import BDay
from fastapi.middleware.cors import CORSMiddleware


# =========================================================
# App
# =========================================================

app = FastAPI(title="CSE Stage Detection API")
tv = TvDatafeed()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Indicators
# =========================================================

def ema(s, n): 
    return s.ewm(span=n, adjust=False).mean()

def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(df, n=14):
    tr = pd.concat([
        df.high - df.low,
        (df.high - df.close.shift()).abs(),
        (df.low - df.close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

# =========================================================
# Stage + Substage Detection (UNCHANGED LOGIC)
# =========================================================

def label_stage_substage(df):
    df = df.copy()

    df["ema20"] = ema(df.close, 20)
    df["ema50"] = ema(df.close, 50)
    df["ema150"] = ema(df.close, 150)
    df["rsi14"] = rsi(df.close)
    df["atr14"] = atr(df)
    df["vol_sma20"] = df.volume.rolling(20).mean()
    df["ema50_slope"] = (df.ema50 - df.ema50.shift(10)) / df.ema50.shift(10)

    df["range_hi"] = df.high.rolling(30).max()
    df["range_lo"] = df.low.rolling(30).min()
    df["range_pct"] = (df.range_hi - df.range_lo) / df.close
    df["atr_pct"] = df.atr14 / df.close
    df["dist_ema50"] = (df.close - df.ema50) / df.ema50
    df["vol_rel"] = df.volume / df.vol_sma20

    out = []

    for i in range(len(df)):
        row = df.iloc[i]
        reasons = []

        # ---------- Stage 2 ----------
        s2 = 0
        if row.ema50_slope > 0.005: s2 += 1; reasons.append("EMA50 slope up")
        if row.ema50 > row.ema150: s2 += 1; reasons.append("EMA50 > EMA150")
        if row.close > row.ema50: s2 += 1; reasons.append("Close > EMA50")
        if row.close > row.ema20: s2 += 1; reasons.append("Close > EMA20")
        if i >= 10 and (df.close.iloc[i-9:i+1] > df.ema50.iloc[i-9:i+1]).sum() >= 7:
            s2 += 1; reasons.append("Above EMA50 (>=7/10)")

        # ---------- Stage 4 ----------
        s4 = 0
        if row.ema50_slope < -0.005: s4 += 1
        if row.ema50 < row.ema150: s4 += 1
        if row.close < row.ema50: s4 += 1

        if s2 >= 4:
            stage = 2
        elif s4 >= 2:
            stage = 4
        else:
            s1 = 0
            if abs(row.ema50_slope) < 0.003: s1 += 1
            if row.atr_pct < 0.025: s1 += 1
            if row.range_pct < 0.12: s1 += 1
            stage = 1 if s1 >= 2 else 3

        # ---------- Substage ----------
        sub = None
        if stage == 2 and i >= 31:
            breakout = row.close > df.range_hi.iloc[i-1] * 1.015 and row.vol_rel > 1.5
            accel = row.dist_ema50 > 0.12 and row.rsi14 > 85
            exhaust = accel and row.vol_rel > 2.5
            tight = row.range_pct < 0.10 and row.atr_pct < 0.025 and row.range_lo > row.ema50

            if breakout:
                sub = "2A"
            elif exhaust:
                sub = "2E"
            elif accel:
                sub = "2D"
            elif tight:
                sub = "2C"
            else:
                sub = "2B"

        out.append({
            "stage": stage,
            "substage": sub,
            "reasons": reasons
        })

    return pd.DataFrame(out, index=df.index)

# =========================================================
# Safe fetch
# =========================================================

def safe_get_hist(symbol):
    for _ in range(3):
        try:
            return tv.get_hist(
                symbol=symbol,
                exchange="CSELK",
                interval=Interval.in_daily,
                n_bars=400
            )
        except:
            time.sleep(2)
    return None

# =========================================================
# API (FINAL, CYCLE-AWARE)
# =========================================================

@app.get("/stage/{symbol}")
def get_stage(symbol: str):
    print(symbol)
    df = safe_get_hist(symbol)
    if df is None or len(df) < 120:
        raise HTTPException(400, "Insufficient data")

    df = df.copy()
    df.columns = df.columns.str.lower()

    labeled = label_stage_substage(df)
    labeled["stage_change"] = labeled.stage != labeled.stage.shift()

    # ---------- Build stage blocks ----------
    blocks = []
    start = labeled.index[0]

    for i in range(1, len(labeled)):
        if labeled.iloc[i].stage_change:
            blocks.append(labeled.loc[start:labeled.index[i-1]])
            start = labeled.index[i]
    blocks.append(labeled.loc[start:])

    blocks = [b for b in blocks if len(b) >= 2]
    current_block = blocks[-1]
    current_stage = int(current_block.iloc[-1].stage)
    current_stage_started = current_block.index[0]

    # ---------- Enforce cycle predecessor ----------
    CYCLE_PREV = {1: 4, 2: 1, 3: 2, 4: 3}
    expected_prev = CYCLE_PREV[current_stage]

    prev_block = None
    for b in reversed(blocks[:-1]):
        if int(b.iloc[-1].stage) == expected_prev:
            prev_block = b
            break

    # ---------- Clamp dates ----------
    last_stage_ended = current_stage_started - BDay(1)
    last_stage_started = prev_block.index[0]

    if last_stage_started >= last_stage_ended:
        last_stage_started = last_stage_ended - BDay(1)

    # ---------- Substages (ONLY inside current Stage-2) ----------
    current_sub_block = None
    last_sub_block = None

    if current_stage == 2:
        s2 = current_block.copy()
        s2["chg"] = s2.substage != s2.substage.shift()

        sub_blocks = []
        ss = s2.index[0]
        for i in range(1, len(s2)):
            if s2.iloc[i].chg:
                sub_blocks.append(s2.loc[ss:s2.index[i-1]])
                ss = s2.index[i]
        sub_blocks.append(s2.loc[ss:])
        sub_blocks = [b for b in sub_blocks if len(b) >= 2]

        if sub_blocks:
            current_sub_block = sub_blocks[-1]
            if len(sub_blocks) >= 2:
                last_sub_block = sub_blocks[-2]

    cur = current_block.iloc[-1]
    
    ohlcv = [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "open": float(df.loc[idx, "open"]),
                "high": float(df.loc[idx, "high"]),
                "low": float(df.loc[idx, "low"]),
                "close": float(df.loc[idx, "close"]),
                "volume": float(df.loc[idx, "volume"])
            }
            for idx in df.index
        ]


    return {
        
        "symbol": symbol,

        "current_stage": current_stage,
        "current_stage_started": current_stage_started.strftime("%Y-%m-%d"),

        "current_substage": cur.substage,
        "current_substage_started": (
            current_sub_block.index[0].strftime("%Y-%m-%d")
            if current_sub_block is not None else None
        ),

        "last_substage": (
            last_sub_block.iloc[-1].substage if last_sub_block is not None else None
        ),
        "last_substage_started": (
            last_sub_block.index[0].strftime("%Y-%m-%d") if last_sub_block is not None else None
        ),
        "last_substage_ended": (
            last_sub_block.index[-1].strftime("%Y-%m-%d") if last_sub_block is not None else None
        ),

        "substage_reasons": cur.reasons,

        "last_stage": expected_prev,
        "last_stage_started": last_stage_started.strftime("%Y-%m-%d"),
        "last_stage_ended": last_stage_ended.strftime("%Y-%m-%d"),
        "ohlcv": ohlcv
    }
