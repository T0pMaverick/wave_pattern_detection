from collections import Counter
from utils import calculate_baseline

SIDEWAYS = "Stage Sideways"
STAGE_1A = "Stage 1A"
STAGE_1B = "Stage 1B"
STAGE_2  = "Stage 2"

HIGH = "HIGH"
LOW = "LOW"


def classify_raw(volume, baseline):
    deviation = abs(volume - baseline) / baseline

    if deviation <= 0.05:
        return SIDEWAYS
    if volume >= 5 * baseline:
        return HIGH
    if volume <= 1.5 * baseline:
        return LOW
    return SIDEWAYS


def detect_patterns(data):
    volumes = data["volume"].tolist()
    closes = data["close"].tolist()
    dates = list(data.index)

    day_states = []
    current_stage = SIDEWAYS

    # ------------------------------
    # BUILD STAGE SEQUENCE (STATE MACHINE)
    # ------------------------------
    for i in range(20, len(data)):
        baseline = calculate_baseline(volumes, i)
        raw = classify_raw(volumes[i], baseline)

        if current_stage == SIDEWAYS:
            if raw == HIGH:
                current_stage = STAGE_1A

        elif current_stage == STAGE_1A:
            if raw == LOW:
                current_stage = STAGE_1B
            elif raw == SIDEWAYS:
                current_stage = SIDEWAYS

        elif current_stage == STAGE_1B:
            if raw == HIGH:
                current_stage = STAGE_2
            elif raw == SIDEWAYS:
                current_stage = SIDEWAYS

        elif current_stage == STAGE_2:
            if raw == SIDEWAYS:
                current_stage = SIDEWAYS

        day_states.append({
            "index": i,
            "date": dates[i],
            "stage": current_stage,
            "baseline": baseline
        })

    # ------------------------------
    # DOMINANT PATTERN (LAST 20 DAYS)
    # ------------------------------
    last_20 = day_states[-20:]
    stage_counts = Counter(d["stage"] for d in last_20)
    dominant_stage = stage_counts.most_common(1)[0][0]

    # find start of dominant stage (continuous)
    start_idx = None
    for d in reversed(day_states):
        if d["stage"] == dominant_stage:
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
