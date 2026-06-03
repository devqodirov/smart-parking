import math
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, text as sa_text
from .. import models
from ..database import is_postgres


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearby_spots(
    db: Session,
    lat: float,
    lon: float,
    radius_km: float = 2.0,
    gas_type: Optional[str] = None,
    limit: int = 20,
) -> List[models.ParkingSpot]:
    query = db.query(models.ParkingSpot).filter(
        models.ParkingSpot.is_active == True,
        models.ParkingSpot.is_occupied == False,
    )
    if gas_type and gas_type != "all":
        query = query.filter(models.ParkingSpot.gas_type_allowed.in_(["all", gas_type]))

    if is_postgres():
        radius_m = radius_km * 1000
        query = query.filter(
            sa_func.ST_DWithin(
                sa_func.ST_MakePoint(models.ParkingSpot.longitude, models.ParkingSpot.latitude),
                sa_func.ST_MakePoint(lon, lat),
                radius_m,
            )
        ).order_by(
            sa_func.ST_Distance(
                sa_func.ST_MakePoint(models.ParkingSpot.longitude, models.ParkingSpot.latitude),
                sa_func.ST_MakePoint(lon, lat),
            )
        ).limit(limit)
        return query.all()
    else:
        spots = query.all()
        nearby = []
        for spot in spots:
            dist = _haversine(lat, lon, spot.latitude, spot.longitude)
            if dist <= radius_km:
                nearby.append((spot, round(dist, 2)))
        nearby.sort(key=lambda x: x[1])
        return [spot for spot, _ in nearby[:limit]]
