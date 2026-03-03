"""ML Predictor for demand forecasting using historical coefficient data."""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

from bot.database.db import AsyncSessionLocal
from bot.services.coefficient_collector import get_historical_data

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "demand_model.joblib"
MIN_TRAINING_DAYS = 60


class DemandPredictor:
    """Predicts demand (surge coefficient) 24 hours ahead using RandomForest."""

    def __init__(self):
        self.model: RandomForestRegressor | None = None
        self.is_trained = False
        self.last_training = None
        self.r2_score = 0.0

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract time-based features from timestamp.

        Features:
        - hour: Hour of day (0-23)
        - day_of_week: Day of week (0=Monday, 6=Sunday)
        - is_weekend: Boolean (Saturday/Sunday)
        - is_rush_hour: Boolean (7-10 AM or 5-8 PM)
        """
        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_rush_hour'] = (
            ((df['hour'] >= 7) & (df['hour'] <= 10)) |
            ((df['hour'] >= 17) & (df['hour'] <= 20))
        ).astype(int)

        return df

    async def train(self, zone_id: str, tariff: str = "econom", days: int = 90) -> dict:
        """
        Train the model on historical data.

        Args:
            zone_id: Zone to train for
            tariff: Tariff class
            days: Number of days of historical data to use

        Returns:
            Dictionary with training metrics
        """
        if days < MIN_TRAINING_DAYS:
            raise ValueError(f"Need at least {MIN_TRAINING_DAYS} days of data for training")

        # Fetch historical data
        async with AsyncSessionLocal() as session:
            records = await get_historical_data(session, zone_id, tariff, days)

        if len(records) < 100:
            raise ValueError(f"Insufficient data: only {len(records)} records found")

        # Convert to DataFrame
        data = pd.DataFrame([
            {
                'timestamp': r.timestamp,
                'coefficient': r.coefficient
            }
            for r in records
        ])

        # Sort by timestamp
        data = data.sort_values('timestamp').reset_index(drop=True)

        # Prepare features
        data = self._prepare_features(data)

        # Create target: coefficient 24 hours ahead
        # Shift coefficient by ~24 hours (assuming hourly data)
        data['target'] = data['coefficient'].shift(-24)

        # Drop rows without target
        data = data.dropna(subset=['target'])

        if len(data) < 50:
            raise ValueError("Not enough data after creating 24h target")

        # Features and target
        feature_cols = ['hour', 'day_of_week', 'is_weekend', 'is_rush_hour', 'coefficient']
        X = data[feature_cols]
        y = data['target']

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        # Train RandomForest
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)

        self.is_trained = True
        self.last_training = datetime.utcnow()
        self.r2_score = r2

        metrics = {
            'r2_score': r2,
            'mae': mae,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'zone_id': zone_id,
            'tariff': tariff
        }

        logger.info(f"Model trained: R²={r2:.3f}, MAE={mae:.3f}")

        return metrics

    def predict(
        self,
        current_coefficient: float,
        target_time: datetime
    ) -> dict:
        """
        Predict demand 24 hours ahead.

        Args:
            current_coefficient: Current surge coefficient
            target_time: Time to predict for (should be ~24h from now)

        Returns:
            Dictionary with prediction and confidence
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Extract features from target time
        hour = target_time.hour
        day_of_week = target_time.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        is_rush_hour = 1 if (7 <= hour <= 10 or 17 <= hour <= 20) else 0

        # Create feature vector
        features = np.array([[
            hour,
            day_of_week,
            is_weekend,
            is_rush_hour,
            current_coefficient
        ]])

        # Predict
        predicted_coef = self.model.predict(features)[0]

        # Classify demand level
        if predicted_coef >= 1.5:
            demand_level = "high"
        elif predicted_coef >= 1.2:
            demand_level = "medium"
        else:
            demand_level = "low"

        return {
            'predicted_coefficient': float(predicted_coef),
            'demand_level': demand_level,
            'confidence': float(self.r2_score),
            'target_time': target_time,
            'model_trained_at': self.last_training
        }

    def save_model(self, path: Path | None = None):
        """Save trained model to disk."""
        if not self.is_trained or self.model is None:
            raise ValueError("No trained model to save")

        save_path = path or MODEL_PATH
        joblib.dump({
            'model': self.model,
            'r2_score': self.r2_score,
            'last_training': self.last_training
        }, save_path)

        logger.info(f"Model saved to {save_path}")

    def load_model(self, path: Path | None = None):
        """Load trained model from disk."""
        load_path = path or MODEL_PATH

        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")

        data = joblib.load(load_path)
        self.model = data['model']
        self.r2_score = data['r2_score']
        self.last_training = data['last_training']
        self.is_trained = True

        logger.info(f"Model loaded from {load_path}")


# Global predictor instance
_predictor = DemandPredictor()


def get_predictor() -> DemandPredictor:
    """Get global predictor instance."""
    return _predictor
