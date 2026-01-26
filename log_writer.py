# log_writer.py

from sqlalchemy import text
from datetime import datetime

def write_agent_log(
    session,
    label: str,
    description: str,
    status: str,
    agent: str = "PatternDetectionAgent"
):
    """
    Writes logs to the EXISTING activity_log table.
    Required columns filled:
    - label
    - name
    - description
    - timestamp
    - agent
    """

    query = text("""
        INSERT INTO activity_log
        (
            label,
            name,
            description,
            timestamp,
            agent
        )
        VALUES
        (
            :label,
            :name,
            :description,
            :timestamp,
            :agent
        )
    """)

    session.execute(query, {
        "label": label,
        "name": status,  # SUCCESS / FAILURE
        "description": description,
        "timestamp": datetime.now(),
        "agent": agent
    })

    session.commit()
