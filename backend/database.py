from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

try:
    from .config import Config
except ImportError:  # Running as script
    from config import Config


db_url = Config.SQLALCHEMY_DATABASE_URI
if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = scoped_session(
    sessionmaker(bind=engine, autocommit=False, autoflush=False)
)

Base = declarative_base()


