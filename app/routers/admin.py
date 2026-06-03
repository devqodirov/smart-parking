from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total_users = db.query(func.count(models.User.id)).scalar()
    total_spots = db.query(func.count(models.ParkingSpot.id)).scalar()
    active_spots = db.query(func.count(models.ParkingSpot.id)).filter(models.ParkingSpot.is_occupied == True).scalar()
    active_bookings = db.query(func.count(models.Reservation.id)).filter(models.Reservation.status == "active").scalar()
    total_revenue = db.query(func.sum(models.Reservation.total_price)).filter(models.Reservation.status == "completed").scalar() or 0
    low_battery = db.query(func.count(models.ParkingSpot.id)).filter(
        models.ParkingSpot.is_active == True,
        models.ParkingSpot.battery_level < 15.0,
    ).scalar()
    return {
        "total_users": total_users,
        "total_spots": total_spots,
        "active_spots": active_spots,
        "available_spots": total_spots - active_spots,
        "active_bookings": active_bookings,
        "total_revenue": float(total_revenue),
        "low_battery_sensors": low_battery,
    }


@router.get("/spots/low-battery")
def get_low_battery_spots(db: Session = Depends(get_db)):
    spots = db.query(models.ParkingSpot).filter(
        models.ParkingSpot.is_active == True,
        models.ParkingSpot.battery_level < 15.0,
    ).all()
    return [
        {"id": s.id, "address": s.address, "battery_level": s.battery_level}
        for s in spots
    ]
