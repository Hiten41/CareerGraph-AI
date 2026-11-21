from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"prepare_threshold": None},
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)
Session = sessionmaker(engine)


def database():
    with Session.begin() as session:
        yield session
