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

        data = fetch_ohlcv(
            symbol,
            bars=200,
            intval=Interval.in_30_minute
        )

        pattern = detect_patterns(data)[0]
        
        save_pattern(pattern_session, {
            "company_symbol": symbol,
            "timeframe": "30_min",
            "stage": pattern["stage"],
            "start_date": pattern["start_date"],
            "end_date": pattern["end_date"],
            "price_change": pattern["price_change_pct"],
            "volume_change": pattern["volume_change_pct"]
        })
        
        write_agent_log(
            log_session,
            label="30_MIN_PATTERN_DETECTION",
            description=f"30-min pattern detected for {symbol} | Stage: {pattern['stage']}",
            status="SUCCESS"
        )
        

    except Exception as e:
        write_agent_log(
            log_session,
            label="30_MIN_PATTERN_DETECTION",
            description=str(e),
            status="FAILURE"
        )

    finally:
        pattern_session.close()
        log_session.close()


def daily_pattern_job():
    pattern_session = PatternSession()
    log_session = LogSession()

    try:
        symbol = "OSEA.N0000"

        data = fetch_ohlcv(
            symbol,
            bars=400,
            intval=Interval.in_daily
        )

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
            label="DAILY_PATTERN_DETECTION",
            description=f"Daily pattern detected for {symbol} | Stage: {pattern['stage']}",
            status="SUCCESS"
        )

    except Exception as e:
        write_agent_log(
            log_session,
            label="DAILY_PATTERN_DETECTION",
            description=str(e),
            status="FAILURE"
        )

    finally:
        pattern_session.close()
        log_session.close()
