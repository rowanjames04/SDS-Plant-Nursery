from typing import Optional
from sqlalchemy import String, Float, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app import db

class Plant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    common_name: Mapped[str] = mapped_column(String(100))
    scientific_name: Mapped[Optional[str]] = mapped_column(String(100))
    size: Mapped[Optional[int]] = mapped_column(Integer)
    #categorization
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey('category.id'))
    species_id: Mapped[Optional[int]] = mapped_column(ForeignKey('species.id'))
    variety_id: Mapped[Optional[int]] = mapped_column(ForeignKey('variety.id'))
    
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

class User(db.Model):
    email: Mapped[str] = mapped_column(String(120), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)

class Species(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

class Variety(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))