# pattern_writer.py

from sqlalchemy import text

def save_pattern(session, payload):
    query = text("""
        INSERT INTO stock_volume_patterns
        (
            company_symbol,
            timeframe,
            stage,
            pattern_start_date,
            pattern_end_date,
            price_change_pct,
            volume_change_pct
        )
        VALUES
        (
            :company_symbol,
            :timeframe,
            :stage,
            :start_date,
            :end_date,
            :price_change,
            :volume_change
        )
    """)

    session.execute(query, payload)
    session.commit()
