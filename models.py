from typing import Optional
from sqlalchemy import String, Float, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app import db

class Plant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    common_name: Mapped[str] = mapped_column(String(100))
    scientific_name: Mapped[Optional[str]] = mapped_column(String(100))
    size: Mapped[Optional[int]] = mapped_column(Integer)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    species: Mapped[Optional[str]] = mapped_column(String(100))
    variety: Mapped[Optional[str]] = mapped_column(String(100))
    pot_container: Mapped[Optional[str]] = mapped_column(String(100))
    price: Mapped[Optional[float]] = mapped_column(Float, default=0.00)
    description: Mapped[Optional[str]] = mapped_column(String(200))
    #key info
    colour: Mapped[Optional[str]] = mapped_column(String(50))
    growth_width: Mapped[Optional[float]] = mapped_column(Float)
    growth_height: Mapped[Optional[float]] = mapped_column(Float)
    fragrant: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    frost_sensitive: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    flowering_period: Mapped[Optional[str]] = mapped_column(String(200))
    light_requirements: Mapped[Optional[str]] = mapped_column(String(200))
    soil_requirements: Mapped[Optional[str]] = mapped_column(String(200))
    #care advice
    planting_advice: Mapped[Optional[str]] = mapped_column(String(200))
    watering_needs: Mapped[Optional[str]] = mapped_column(String(200))
    pruning_needs: Mapped[Optional[str]] = mapped_column(String(200))
