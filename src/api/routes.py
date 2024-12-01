"""API routes for the Pharmiliar service."""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas, services
from .database import get_db

app = FastAPI(
    title="Pharmiliar API",
    description="API for transparent healthcare pricing and service comparison",
    version="1.0.0"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Price Estimation Routes
@app.post("/estimate/from-symptoms", response_model=schemas.CostEstimate)
async def estimate_from_symptoms(
    symptoms: List[str],
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Estimate treatment costs based on symptoms."""
    return await services.estimate_costs_from_symptoms(symptoms, location, db)

@app.post("/estimate/from-condition", response_model=schemas.CostEstimate)
async def estimate_from_condition(
    condition: str,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Estimate treatment costs for a specific condition."""
    return await services.estimate_costs_from_condition(condition, location, db)

# Hospital Comparison Routes
@app.get("/hospitals", response_model=List[schemas.Hospital])
async def list_hospitals(
    location: Optional[str] = None,
    service: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List hospitals with optional filtering."""
    return await services.get_hospitals(location, service, db)

@app.get("/hospitals/{hospital_id}/services", response_model=List[schemas.Service])
async def list_hospital_services(
    hospital_id: int,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List services offered by a hospital."""
    return await services.get_hospital_services(hospital_id, department, db)

# Price Comparison Routes
@app.get("/compare/service/{service_id}", response_model=schemas.ServiceComparison)
async def compare_service_prices(
    service_id: int,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Compare prices for a specific service across hospitals."""
    return await services.compare_service_prices(service_id, location, db)

@app.get("/compare/condition/{condition}", response_model=schemas.ConditionComparison)
async def compare_condition_costs(
    condition: str,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Compare total treatment costs for a condition across hospitals."""
    return await services.compare_condition_costs(condition, location, db)

# Crowdsourcing Routes
@app.post("/contribute/price", response_model=schemas.PriceContribution)
async def contribute_price(
    contribution: schemas.PriceContributionCreate,
    user = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Contribute price information for a service."""
    return await services.add_price_contribution(contribution, user, db)

@app.post("/reviews", response_model=schemas.HospitalReview)
async def add_review(
    review: schemas.HospitalReviewCreate,
    user = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Add a hospital review."""
    return await services.add_hospital_review(review, user, db)

# User Management Routes
@app.post("/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user account."""
    return await services.create_user(user, db)

@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login to get access token."""
    return await services.authenticate_user(form_data, db)
