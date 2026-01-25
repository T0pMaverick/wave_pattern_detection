from collections import Counter
from utils import calculate_baseline

SIDEWAYS = "Stage Sideways"
STAGE_1A = "Stage 1A"
STAGE_1B = "Stage 1B"
STAGE_2  = "Stage 2"


def classify_day(volume, baseline):
    deviation = abs(volume - baseline) / baseline

    if deviation <= 0.05:
        return SIDEWAYS
    if volume >= 5 * baseline:
        return STAGE_1A
    if volume <= 1.5 * baseline:
        return STAGE_1B
    return SIDEWAYS


def detect_patterns(data):
    volumes = data["volume"].tolist()
    closes = data["close"].tolist()
    dates = list(data.index)

    daily_labels = []

    # classify each valid day
    for i in range(20, len(data)):
        baseline = calculate_baseline(volumes, i)
        label = classify_day(volumes[i], baseline)
        daily_labels.append({
            "index": i,
            "date": dates[i],
            "label": label,
            "baseline": baseline
        })

    # ------------------------------
    # FIND DOMINANT PATTERN (LAST 20 DAYS)
    # ------------------------------
    last_20 = daily_labels[-20:]
    label_counts = Counter(d["label"] for d in last_20)
    dominant_stage = label_counts.most_common(1)[0][0]

    # find start of dominant stage
    start_idx = None
    for d in reversed(daily_labels):
        if d["label"] == dominant_stage:
            start_idx = d["index"]
        else:
            break

    if start_idx is None:
        start_idx = last_20[0]["index"]

    start_close = closes[start_idx]
    last_close = closes[-1]

    baseline_at_start = calculate_baseline(volumes, start_idx)
    last_volume = volumes[-1]

    price_change = ((last_close - start_close) / start_close) * 100
    volume_change = ((last_volume - baseline_at_start) / baseline_at_start) * 100

    return [{
        "stage": dominant_stage,
        "start_date": dates[start_idx],
        "end_date": None,
        "price_change_pct": round(price_change, 2),
        "volume_change_pct": round(volume_change, 2)
    }]
