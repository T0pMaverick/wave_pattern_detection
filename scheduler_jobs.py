# scheduler_jobs.py

from services import fetch_ohlcv
from pattern_engine import detect_patterns
from database import PatternSession, LogSession
from pattern_writer import save_pattern
from log_writer import write_agent_log
from tvDatafeed import Interval

def hourly_pattern_job():
    pattern_session = PatternSession()
    log_session = LogSession()

    try:
        symbol = "OSEA.N0000"

        data = fetch_ohlcv(symbol, bars=200,intval=Interval.in_30_minute)  # 30 min
        pattern = detect_patterns(data)[0]

        save_pattern(pattern_session, {
            "company_symbol": symbol,
            "timeframe": "hourly",
            "stage": pattern["stage"],
            "start_date": pattern["start_date"],
            "end_date": pattern["end_date"],
            "price_change": pattern["price_change_pct"],
            "volume_change": pattern["volume_change_pct"]
        })

        write_agent_log(
            log_session,
            activity="30_MIN_PATTERN_DETECTION",
            status="SUCCESS",
            description=f"Hourly pattern detected for {symbol}",
            metadata=pattern
        )

    except Exception as e:
        write_agent_log(
            log_session,
            activity="30_MIN_PATTERN_DETECTION",
            status="FAILURE",
            description=str(e)
        )
    finally:
        pattern_session.close()
        log_session.close()


def daily_pattern_job():
    pattern_session = PatternSession()
    log_session = LogSession()

    try:
        symbol = "OSEA.N0000"

        data = fetch_ohlcv(symbol, intval=Interval.in_daily,bars=400)  # daily
        pattern = detect_patterns(data)[0]

        save_pattern(pattern_session, {
            "company_symbol": symbol,
            "timeframe": "daily",
            "stage": pattern["stage"],
            "start_date": pattern["start_date"],
            "end_date": pattern["end_date"],
            "price_change": pattern["price_change_pct"],
            "volume_change": pattern["volume_change_pct"]
        })

        write_agent_log(
            log_session,
            activity="DAILY_PATTERN_DETECTION",
            status="SUCCESS",
            description=f"Daily pattern detected for {symbol}",
            metadata=pattern
        )

    except Exception as e:
        write_agent_log(
            log_session,
            activity="DAILY_PATTERN_DETECTION",
            status="FAILURE",
            description=str(e)
        )
    finally:
        pattern_session.close()
        log_session.close()
