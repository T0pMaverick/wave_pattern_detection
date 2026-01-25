def calculate_baseline(volumes, index, window=20):
    start = index - window
    end = index
    return sum(volumes[start:end]) / window
