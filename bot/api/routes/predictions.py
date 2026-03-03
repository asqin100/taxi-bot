"""Predictions API route for demand forecasting."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException

from bot.api.auth import get_current_user
from bot.api.schemas import PredictionResponse
from bot.models.user import User
from bot.services.ml.predictor import get_predictor
from bot.services.yandex_api import get_cached_coefficients

router = APIRouter()


@router.get("/predictions/demand", response_model=PredictionResponse)
async def predict_demand(
    zone_id: str = Query(..., description="Zone ID to predict for"),
    tariff: str = Query(default="econom", description="Tariff class (econom, comfort, business)"),
    current_user: User = Depends(get_current_user)
):
    """
    Predict demand (surge coefficient) 24 hours ahead for a specific zone.

    - **zone_id**: Zone identifier (e.g., 'center', 'sheremetyevo')
    - **tariff**: Tariff class (econom, comfort, business)

    Returns predicted coefficient, demand level (high/medium/low), and confidence score.

    **Note**: Model must be trained first. If not trained, returns an error.
    """
    predictor = get_predictor()

    # Check if model is trained
    if not predictor.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Prediction model not trained yet. Please train the model first or wait for automatic training."
        )

    # Get current coefficient from cache
    cached_data = get_cached_coefficients(tariff=tariff)
    current_coef = 1.0

    for data in cached_data:
        if data.zone_id == zone_id:
            current_coef = data.coefficient
            break

    # Predict 24 hours ahead
    target_time = datetime.utcnow() + timedelta(hours=24)

    try:
        prediction = predictor.predict(current_coef, target_time)

        return PredictionResponse(
            zone_id=zone_id,
            tariff=tariff,
            predicted_coefficient=prediction['predicted_coefficient'],
            demand_level=prediction['demand_level'],
            confidence=prediction['confidence'],
            target_time=prediction['target_time'],
            current_coefficient=current_coef,
            model_trained_at=prediction['model_trained_at']
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/predictions/train")
async def train_model(
    zone_id: str = Query(..., description="Zone ID to train for"),
    tariff: str = Query(default="econom", description="Tariff class"),
    days: int = Query(default=90, ge=60, le=180, description="Days of historical data to use"),
    current_user: User = Depends(get_current_user)
):
    """
    Train the prediction model on historical data.

    - **zone_id**: Zone to train for
    - **tariff**: Tariff class
    - **days**: Number of days of historical data (60-180)

    Returns training metrics including R² score and MAE.

    **Note**: Requires at least 60 days of historical coefficient data.
    """
    predictor = get_predictor()

    try:
        metrics = await predictor.train(zone_id, tariff, days)

        # Save trained model
        predictor.save_model()

        return {
            "status": "success",
            "message": f"Model trained successfully for {zone_id}/{tariff}",
            "metrics": metrics
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Training failed: {str(e)}"
        )
