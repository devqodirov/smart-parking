from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from ..services.payment import COMMISSION_PERCENT

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user


@router.post("/{user_id}/deposit")
def deposit_money(user_id: int, amount: float, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User topilmadi")
    user.balance += amount
    db.commit()
    return {"message": "Balans muvaffaqiyatli to'ldirildi", "new_balance": user.balance}


@router.get("/{user_id}/analytics")
def get_owner_analytics(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    spots = db.query(models.ParkingSpot).filter(models.ParkingSpot.owner_id == user_id).all()
    total_earnings = sum(
        r.total_price * (1 - COMMISSION_PERCENT) for spot in spots for r in spot.reservations if r.status == "completed"
    )
    active_spots = sum(1 for spot in spots if spot.is_occupied)
    total_spots = len(spots)
    return {
        "total_spots": total_spots,
        "active_spots": active_spots,
        "total_earnings": total_earnings,
        "spots": [{"id": s.id, "address": s.address, "occupied": s.is_occupied, "hourly_rate": s.hourly_rate} for s in spots],
    }
