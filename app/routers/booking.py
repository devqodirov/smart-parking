from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
from ..database import get_db
from .. import models, schemas
from ..services.payment import hold_payment, release_payment, refund_payment

router = APIRouter(prefix="/api/v1/booking", tags=["Reservations"])


@router.post("/", response_model=schemas.ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking_info: schemas.ReservationCreate, db: Session = Depends(get_db)):
    driver = db.query(models.User).filter(models.User.id == booking_info.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.id == booking_info.parking_spot_id).first()
    if not spot or not spot.is_active:
        raise HTTPException(status_code=404, detail="Parking joyi topilmadi yoki noaktiv")

    now = datetime.now(timezone.utc)
    active_booking = db.query(models.Reservation).filter(
        models.Reservation.parking_spot_id == spot.id,
        models.Reservation.status == "active",
        models.Reservation.end_time > now
    ).first()

    if active_booking:
        raise HTTPException(status_code=400, detail="Bu parking joyi ayni damda band")

    total_cost = spot.hourly_rate * booking_info.hours
    if not hold_payment(db, driver.id, total_cost):
        raise HTTPException(status_code=400, detail="Mablag' yetarli emas")

    end_booking_time = now + timedelta(hours=booking_info.hours)

    new_reservation = models.Reservation(
        driver_id=driver.id,
        parking_spot_id=spot.id,
        start_time=now,
        end_time=end_booking_time,
        total_price=total_cost,
        status="active",
    )
    spot.is_occupied = True
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return new_reservation


@router.post("/{reservation_id}/release")
def release_booking(reservation_id: int, db: Session = Depends(get_db)):
    success = release_payment(db, reservation_id)
    if not success:
        raise HTTPException(status_code=400, detail="Bronni yakunlab bo'lmadi")
    return {"status": "completed", "message": "To'lov joy egasiga o'tkazildi"}


@router.post("/{reservation_id}/cancel")
def cancel_booking(reservation_id: int, db: Session = Depends(get_db)):
    success = refund_payment(db, reservation_id)
    if not success:
        raise HTTPException(status_code=400, detail="Bronni bekor qilib bo'lmadi")
    return {"status": "cancelled", "message": "Bron bekor qilindi, pul qaytarildi"}


@router.get("/active/{user_id}", response_model=List[schemas.ReservationResponse])
def get_active_bookings(user_id: int, db: Session = Depends(get_db)):
    bookings = db.query(models.Reservation).filter(
        models.Reservation.driver_id == user_id,
        models.Reservation.status == "active",
    ).all()
    return bookings
