from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="driver")  # driver, owner, admin
    balance = Column(Float, default=0.0)

    # Munosabatlar
    spots = relationship("ParkingSpot", back_populates="owner")
    reservations = relationship("Reservation", back_populates="driver")

class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    hourly_rate = Column(Float, default=5000.0)
    is_occupied = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    gas_type_allowed = Column(String, default="all")  # all, benzin, gaz, dizel
    is_underground = Column(Boolean, default=False)
    has_barrier = Column(Boolean, default=False)
    battery_level = Column(Float, default=100.0)  # IoT datchik batareya holati

    # Munosabatlar
    owner = relationship("User", back_populates="spots")
    reservations = relationship("Reservation", back_populates="spot")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parking_spot_id = Column(Integer, ForeignKey("parking_spots.id"), nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="active")  # active, completed, cancelled

    # Munosabatlar
    driver = relationship("User", back_populates="reservations")
    spot = relationship("ParkingSpot", back_populates="reservations")