from .celery_app import celery_app
from ..database import SessionLocal
from ..services.payment import release_payment
from ..services.notifications import notify_low_battery
from .. import models
from datetime import datetime, timezone


@celery_app.task
def expire_booking(reservation_id: int):
    db = SessionLocal()
    try:
        reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if reservation and reservation.status == "active" and reservation.end_time < datetime.now(timezone.utc):
            release_payment(db, reservation_id)
    finally:
        db.close()


@celery_app.task
def check_battery_levels():
    db = SessionLocal()
    try:
        spots = db.query(models.ParkingSpot).filter(
            models.ParkingSpot.is_active == True,
            models.ParkingSpot.battery_level < 15.0,
        ).all()
        for spot in spots:
            notify_low_battery(spot.id, spot.battery_level)
    finally:
        db.close()
