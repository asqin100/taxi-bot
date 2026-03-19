"""Pydantic schemas for API responses."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ShiftResponse(BaseModel):
    """Single shift data"""
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_hours: float
    gross_earnings: float
    net_earnings: float
    trips_count: int
    distance_km: float
    fuel_cost: float
    commission: float
    rent_cost: float
    other_expenses: float
    notes: Optional[str]

    class Config:
        from_attributes = True


class ShiftExportResponse(BaseModel):
    """Response for shift export endpoint"""
    total_shifts: int
    completed_shifts: int
    active_shifts: int
    total_gross: float
    total_net: float
    shifts: List[ShiftResponse]
    period_start: datetime
    period_end: datetime


class StatsResponse(BaseModel):
    """Statistics summary response"""
    shifts_count: int
    total_hours: float
    gross_earnings: float
    net_earnings: float
    total_distance: float
    total_trips: int
    avg_hourly_rate: float
    expenses: dict
    period_days: int


class PredictionResponse(BaseModel):
    """Demand prediction response"""
    zone_id: str
    tariff: str
    predicted_coefficient: float
    demand_level: str = Field(description="high, medium, or low")
    confidence: float = Field(ge=0.0, le=1.0, description="R² score of the model")
    target_time: datetime
    current_coefficient: float
    model_trained_at: Optional[datetime]
