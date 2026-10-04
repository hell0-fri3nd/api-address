from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import Base, get_db, reset_rate_limits
from app.main import app


@pytest.fixture(autouse=True)
def reset_rate_limit() -> None:
    reset_rate_limits()


@pytest.fixture
def session_factory() -> Iterator[sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(session_factory: sessionmaker) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory: sessionmaker) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def address_payload() -> dict:
    return {
        "street": "1 Rizal Park",
        "city": "Manila",
        "state": None,
        "postal_code": "1000",
        "country": "Philippines",
        "latitude": 14.5995,
        "longitude": 120.9842,
    }


@pytest.fixture
def create_address(client: TestClient, address_payload: dict) -> Callable[..., dict]:
    def _create_address(**overrides) -> dict:
        response = client.post("/api/v1/addresses", json=address_payload | overrides)
        assert response.status_code == 201
        return response.json()

    return _create_address
