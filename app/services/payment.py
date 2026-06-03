from sqlalchemy.orm import Session
from .. import models

COMMISSION_PERCENT = 0.12  # 12% startap komissiyasi


def hold_payment(db: Session, driver_id: int, amount: float) -> bool:
    driver = db.query(models.User).filter(models.User.id == driver_id).first()
    if not driver or driver.balance < amount:
        return False
    driver.balance -= amount
    db.commit()
    return True


def release_payment(db: Session, reservation_id: int):
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not reservation or reservation.status != "active":
        return False

    spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.id == reservation.parking_spot_id).first()
    if not spot:
        return False

    commission = reservation.total_price * COMMISSION_PERCENT
    owner_payout = reservation.total_price - commission

    if spot.owner_id:
        owner = db.query(models.User).filter(models.User.id == spot.owner_id).first()
        if owner:
            owner.balance += owner_payout

    reservation.status = "completed"
    spot.is_occupied = False
    db.commit()
    return True


def refund_payment(db: Session, reservation_id: int):
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not reservation or reservation.status != "active":
        return False

    driver = db.query(models.User).filter(models.User.id == reservation.driver_id).first()
    if not driver:
        return False

    driver.balance += reservation.total_price
    reservation.status = "cancelled"

    spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.id == reservation.parking_spot_id).first()
    if spot:
        spot.is_occupied = False
    db.commit()
    return True
