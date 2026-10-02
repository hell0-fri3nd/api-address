from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import config as settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })
    __mapper_args__ = {"eager_defaults": True}


connect_args = {}
if settings.database_uri.startswith("sqlite"):
    # SQLite needs check_same_thread=False for FastAPI async support
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_uri,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)


# Enable foreign key support for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.database_uri.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    """Dependency that provides a database session."""
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)