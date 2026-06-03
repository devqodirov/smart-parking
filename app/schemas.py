from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    phone_number: str
    full_name: str
    role: Optional[str] = "driver"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone_number: str
    full_name: str
    role: str
    balance: float

# --- RESERVATION SCHEMAS ---
class ReservationCreate(BaseModel):
    driver_id: int
    parking_spot_id: int
    hours: int  # Necha soatga joy kerakligi

class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_id: int
    parking_spot_id: int
    start_time: datetime
    end_time: datetime
    total_price: float
    status: str

class ParkingSpotCreate(BaseModel):
    owner_id: Optional[int] = None
    address: str
    latitude: float
    longitude: float
    hourly_rate: float = 5000.0
    gas_type_allowed: Optional[str] = "all"  # all, benzin, gaz, dizel
    is_underground: bool = False

class ParkingSpotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: Optional[int] = None
    address: str
    latitude: float
    longitude: float
    hourly_rate: float
    is_occupied: bool
    is_active: bool
    gas_type_allowed: str
    is_underground: bool 