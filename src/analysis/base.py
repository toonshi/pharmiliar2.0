"""Base models and database setup for price analysis."""

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os

Base = declarative_base()

class Department(Base):
    """Represents a hospital department or section."""
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    gl_account = Column(String)
    services = relationship("Service", back_populates="department")

class Service(Base):
    """Represents a medical service with pricing tiers."""
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
    normal_rate = Column(Float)
    special_rate = Column(Float)
    non_ea_rate = Column(Float)
    
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    department = relationship("Department", back_populates="services")
    
    base_service_id = Column(Integer, ForeignKey('services.id'), nullable=True)
    variant_type = Column(String)
    gl_account = Column(String)

    def __repr__(self):
        return f"<Service(code='{self.code}', description='{self.description}')>"

def get_db_path():
    """Get the path to the SQLite database."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data',
        'processed',
        'hospital_services.db'
    )

def init_db():
    """Initialize the database with these models."""
    engine = create_engine(f'sqlite:///{get_db_path()}')
    Base.metadata.create_all(engine)
    return engine
