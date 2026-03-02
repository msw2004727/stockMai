from __future__ import annotations


def compute_indicator_series(price_series: list[dict]) -> list[dict]:
    closes = [_to_float(item.get("close")) for item in price_series]
    dates = [str(item.get("date", "")) for item in price_series]

    sma5 = _sma(closes, period=5)
    sma20 = _sma(closes, period=20)
    rsi14 = _rsi(closes, period=14)
    macd_line, macd_signal, macd_hist = _macd(closes, fast_period=12, slow_period=26, signal_period=9)

    rows: list[dict] = []
    for idx, close in enumerate(closes):
        rows.append(
            {
                "date": dates[idx],
                "close": close,
                "sma5": _round_or_none(sma5[idx]),
                "sma20": _round_or_none(sma20[idx]),
                "rsi14": _round_or_none(rsi14[idx]),
                "macd": _round_or_none(macd_line[idx]),
                "macd_signal": _round_or_none(macd_signal[idx]),
                "macd_hist": _round_or_none(macd_hist[idx]),
            }
        )
    return rows


def compute_latest_indicators(price_series: list[dict]) -> dict:
    rows = compute_indicator_series(price_series)
    if not rows:
        return {
            "sma5": None,
            "sma20": None,
            "rsi14": None,
            "macd": None,
            "macd_signal": None,
            "macd_hist": None,
        }

    latest = rows[-1]
    return {
        "sma5": latest["sma5"],
        "sma20": latest["sma20"],
        "rsi14": latest["rsi14"],
        "macd": latest["macd"],
        "macd_signal": latest["macd_signal"],
        "macd_hist": latest["macd_hist"],
    }


def _sma(values: list[float], period: int) -> list[float | None]:
    if period <= 0:
        return [None] * len(values)

    result: list[float | None] = [None] * len(values)
    rolling_sum = 0.0
    for idx, value in enumerate(values):
        rolling_sum += value
        if idx >= period:
            rolling_sum -= values[idx - period]
        if idx >= period - 1:
            result[idx] = rolling_sum / period
    return result


def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    if period <= 0:
        return values[:]

    alpha = 2.0 / (period + 1.0)
    ema: list[float] = [values[0]]
    for idx in range(1, len(values)):
        ema.append(alpha * values[idx] + (1.0 - alpha) * ema[-1])
    return ema


def _rsi(values: list[float], period: int) -> list[float | None]:
    length = len(values)
    if length == 0:
        return []
    if period <= 0:
        return [None] * length
    if length < period + 1:
        return [None] * length

    result: list[float | None] = [None] * length

    gains = [0.0] * length
    losses = [0.0] * length
    for idx in range(1, length):
        delta = values[idx] - values[idx - 1]
        gains[idx] = max(delta, 0.0)
        losses[idx] = max(-delta, 0.0)

    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    result[period] = _calc_rsi(avg_gain, avg_loss)

    for idx in range(period + 1, length):
        avg_gain = ((avg_gain * (period - 1)) + gains[idx]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[idx]) / period
        result[idx] = _calc_rsi(avg_gain, avg_loss)

    return result


def _calc_rsi(avg_gain: float, avg_loss: float) -> float:
    if avg_gain == 0.0 and avg_loss == 0.0:
        return 50.0
    if avg_loss == 0.0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(
    values: list[float],
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    if not values:
        return [], [], []

    fast = _ema(values, fast_period)
    slow = _ema(values, slow_period)

    macd_line: list[float | None] = [fast[idx] - slow[idx] for idx in range(len(values))]
    macd_signal_raw = _ema([item for item in macd_line if item is not None], signal_period)

    macd_signal: list[float | None] = [None] * len(values)
    signal_start = len(macd_line) - len(macd_signal_raw)
    for idx, value in enumerate(macd_signal_raw):
        macd_signal[signal_start + idx] = value

    macd_hist: list[float | None] = [None] * len(values)
    for idx in range(len(values)):
        line = macd_line[idx]
        signal = macd_signal[idx]
        if line is None or signal is None:
            continue
        macd_hist[idx] = line - signal

    return macd_line, macd_signal, macd_hist


def _to_float(raw: object) -> float:
    try:
        return float(raw)
    except Exception:
        return 0.0


def _round_or_none(raw: float | None) -> float | None:
    if raw is None:
        return None
    return round(raw, 6)
