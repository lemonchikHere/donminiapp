import pytest
from sqlalchemy import create_engine, Column, UUID as UUID_TYPE
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.user import User, Favorite
from src.models.appointment import Appointment
import uuid
from datetime import datetime

# Mock Property model for testing purposes
class Property(Base):
    __tablename__ = 'properties'
    id = Column(UUID_TYPE(as_uuid=True), primary_key=True, default=uuid.uuid4)

from sqlalchemy import event

# Setup the in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_cascade_delete_on_user(db_session):
    # Arrange
    user_id = uuid.uuid4()
    prop_id = uuid.uuid4()
    user = User(id=user_id, telegram_user_id=123)
    prop = Property(id=prop_id)
    fav = Favorite(user_id=user_id, property_id=prop_id)
    appt = Appointment(user_id=user_id, property_id=prop_id, requested_datetime=datetime.utcnow())

    db_session.add(user)
    db_session.add(prop)
    db_session.commit()

    db_session.add(fav)
    db_session.add(appt)
    db_session.commit()

    # Act
    db_session.delete(user)
    db_session.commit()

    # Assert
    assert db_session.query(Favorite).count() == 0
    assert db_session.query(Appointment).count() == 0

def test_cascade_delete_on_property(db_session):
    # Arrange
    user_id = uuid.uuid4()
    prop_id = uuid.uuid4()
    user = User(id=user_id, telegram_user_id=123)
    prop = Property(id=prop_id)
    fav = Favorite(user_id=user_id, property_id=prop_id)
    appt = Appointment(user_id=user_id, property_id=prop_id, requested_datetime=datetime.utcnow())

    db_session.add(user)
    db_session.add(prop)
    db_session.commit()

    db_session.add(fav)
    db_session.add(appt)
    db_session.commit()

    # Act
    db_session.delete(prop)
    db_session.commit()

    # Assert
    assert db_session.query(Favorite).count() == 0
    assert db_session.query(Appointment).count() == 0
