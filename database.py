from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PATTERN_DB_URL = "postgresql://neondb_owner:npg_b2nSRLlzvtT1@ep-withered-sea-ady2yzev-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
LOG_DB_URL = "postgresql://neondb_owner:npg_8ksy5LGPnjJD@ep-quiet-glade-a18rsovg-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

pattern_engine = create_engine(PATTERN_DB_URL, pool_pre_ping=True)
log_engine = create_engine(LOG_DB_URL, pool_pre_ping=True)

PatternSession = sessionmaker(bind=pattern_engine)
LogSession = sessionmaker(bind=log_engine)
