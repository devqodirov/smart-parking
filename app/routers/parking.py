from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from .. import models, schemas
from ..services.nearby import find_nearby_spots
from ..services.redis_cache import redis_cache

router = APIRouter(prefix="/api/v1/parking", tags=["Parking Spots"])


@router.get("/", response_model=List[schemas.ParkingSpotResponse])
def get_all_spots(db: Session = Depends(get_db)):
    spots = db.query(models.ParkingSpot).filter(models.ParkingSpot.is_active == True).all()
    return spots


@router.get("/nearby", response_model=List[schemas.ParkingSpotResponse])
def get_nearby_spots(
    lat: float = Query(41.2995),
    lon: float = Query(69.2401),
    radius: float = Query(2.0),
    gas_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    spots = find_nearby_spots(db, lat, lon, radius, gas_type=gas_type)
    return spots


@router.post("/", response_model=schemas.ParkingSpotResponse, status_code=status.HTTP_201_CREATED)
def create_spot(spot: schemas.ParkingSpotCreate, db: Session = Depends(get_db)):
    db_spot = models.ParkingSpot(**spot.model_dump())
    db.add(db_spot)
    db.commit()
    db.refresh(db_spot)
    return db_spot


@router.get("/{spot_id}", response_model=schemas.ParkingSpotResponse)
def get_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Parking joyi topilmadi")
    return spot


@router.patch("/{spot_id}/sensor-update")
def sensor_update(spot_id: int, occupied: bool = None, battery: float = None, db: Session = Depends(get_db)):
    spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Parking joyi topilmadi")
    if occupied is not None:
        spot.is_occupied = occupied
        redis_cache.set_spot_status(spot_id, occupied)
    if battery is not None:
        spot.battery_level = battery
        redis_cache.set_spot_battery(spot_id, battery)
        if battery < 15.0:
            from ..services.notifications import notify_low_battery
            notify_low_battery(spot_id, battery)
    db.commit()
    return {"status": "updated", "occupied": spot.is_occupied, "battery": spot.battery_level}
