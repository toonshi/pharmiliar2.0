from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Department(Base):
    """Represents a hospital department or section (e.g., ADMISSION FEES, ADULT PHARMACY)"""
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    gl_account = Column(String)  # General Ledger account for the department
    services = relationship("Service", back_populates="department")

class Service(Base):
    """Represents a medical service with its various pricing tiers"""
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)  # Original service code (e.g., ADM0001, PH010117)
    description = Column(String, nullable=False)
    
    # Pricing tiers
    normal_rate = Column(Float)  # E.A. (East Africa) rate
    special_rate = Column(Float)  # Private rate
    non_ea_rate = Column(Float)  # Non-East Africa rate
    
    # Foreign key to department
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    department = relationship("Department", back_populates="services")
    
    # For services with variants (-K, -NK, -P suffixes)
    base_service_id = Column(Integer, ForeignKey('services.id'), nullable=True)
    variant_type = Column(String)  # K: Kenyan, NK: Non-Kenyan, P: Private
    
    # GL Account specific to this service (if different from department)
    gl_account = Column(String)

    def __repr__(self):
        return f"<Service(code='{self.code}', description='{self.description}')>"

class PriceHistory(Base):
    """Tracks historical changes in service prices"""
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    effective_date = Column(String, nullable=False)
    normal_rate = Column(Float)
    special_rate = Column(Float)
    non_ea_rate = Column(Float)
    
    service = relationship("Service")

def init_db(db_path):
    """Initialize the database with these models"""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine
