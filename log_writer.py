# log_writer.py

from sqlalchemy import text
import json

def write_agent_log(
    session,
    activity: str,
    status: str,
    description: str,
    metadata: dict = None
):
    query = text("""
        INSERT INTO agent_activity_logs
        (
            agent_name,
            agent_type,
            activity,
            status,
            description,
            metadata,
            created_at
        )
        VALUES
        (
            :agent_name,
            :agent_type,
            :activity,
            :status,
            :description,
            :metadata,
            NOW()
        )
    """)

    session.execute(query, {
        "agent_name": "PatternDetectionAgent",
        "agent_type": "MARKET_ANALYSIS",
        "activity": activity,
        "status": status,
        "description": description,
        "metadata": json.dumps(metadata or {})
    })

    session.commit()
