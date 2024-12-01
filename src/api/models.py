"""Database models for the Pharmiliar API."""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Hospital(Base):
    """Hospital information and metadata."""
    __tablename__ = 'hospitals'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String)
    contact = Column(String)
    rating = Column(Float, default=0.0)
    departments = relationship("Department", back_populates="hospital")
    reviews = relationship("HospitalReview", back_populates="hospital")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class Department(Base):
    """Hospital department/section."""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    gl_account = Column(String)
    hospital = relationship("Hospital", back_populates="departments")
    services = relationship("Service", back_populates="department")

class Service(Base):
    """Medical service with pricing tiers."""
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    code = Column(String)
    name = Column(String, nullable=False)
    description = Column(Text)
    normal_rate = Column(Float)
    special_rate = Column(Float)
    non_ea_rate = Column(Float)
    department = relationship("Department", back_populates="services")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class HospitalReview(Base):
    """User reviews and ratings for hospitals."""
    __tablename__ = 'hospital_reviews'
    
    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Float, nullable=False)
    review = Column(Text)
    hospital = relationship("Hospital", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class User(Base):
    """User account information."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    reviews = relationship("HospitalReview", back_populates="user")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Condition(Base):
    """Medical conditions and their typical treatments."""
    __tablename__ = 'conditions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    symptoms = Column(Text)  # JSON list of common symptoms
    typical_services = Column(Text)  # JSON list of typical service IDs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
