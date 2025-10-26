# tests/api/test_appointments_routes.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from src.models.property import Property
from src.models.appointment import Appointment
from src.models.user import User

@pytest.fixture
def test_property(db_session):
    prop = Property(
        id=uuid4(), address="123 Appointment St",
        telegram_message_id=int(uuid4().int % 100000),
        telegram_channel_id=12345,
        posted_at=datetime.utcnow()
    )
    db_session.add(prop)
    db_session.commit()
    return prop

@pytest.mark.asyncio
@patch('src.api.routes.appointments.send_telegram_notification', new_callable=AsyncMock)
async def test_create_appointment_success(mock_send_notification, db_session, test_user, test_property):
    user, client = test_user
    appointment_time = datetime.utcnow() + timedelta(days=3)
    appointment_data = {
        "property_id": str(test_property.id),
        "requested_datetime": appointment_time.isoformat(),
        "user_phone": "123-456-7890",
        "user_name": "Test User",
    }

    response = client.post("/api/appointments/", json=appointment_data)

    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == str(test_property.id)
    assert data["status"] == "pending"
    mock_send_notification.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_appointments(db_session, test_user, test_property):
    user, client = test_user
    db_user = db_session.query(User).filter(User.telegram_user_id == user.telegram_user_id).one()

    appointment = Appointment(
        user_id=db_user.id, property_id=test_property.id,
        requested_datetime=datetime.utcnow(), status="confirmed",
        user_name="Test User"
    )
    db_session.add(appointment)
    db_session.commit()

    response = client.get("/api/appointments/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(appointment.id)

@pytest.mark.asyncio
async def test_cancel_appointment_success(db_session, test_user, test_property):
    user, client = test_user
    db_user = db_session.query(User).filter(User.telegram_user_id == user.telegram_user_id).one()

    appointment = Appointment(
        user_id=db_user.id, property_id=test_property.id,
        requested_datetime=datetime.utcnow(), status="pending",
        user_name="Test User"
    )
    db_session.add(appointment)
    db_session.commit()

    response = client.patch(f"/api/appointments/{appointment.id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
