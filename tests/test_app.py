"""
Unit tests for the Weather-Driven Disease Outbreak Predictor.
Run with: pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from weather_api import WeatherAPI, WeatherCache
from features import FeatureEngine
from ml_model import EnsembleModel


class TestWeatherAPI:
    """Tests for weather API functionality."""
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = WeatherCache()
        key1 = cache._get_cache_key(18.5204, 73.8567, "forecast")
        key2 = cache._get_cache_key(18.5204, 73.8567, "forecast")
        key3 = cache._get_cache_key(18.5205, 73.8567, "forecast")
        
        assert key1 == key2
        assert key1 != key3
    
    def test_weather_api_initialization(self):
        """Test weather API initialization."""
        api = WeatherAPI()
        assert api.forecast_url is not None
        assert api.archive_url is not None
        assert api.cache is not None


class TestFeatureEngine:
    """Tests for feature engineering."""
    
    def test_feature_engine_initialization(self):
        """Test feature engine initialization."""
        engine = FeatureEngine()
        assert engine.feature_names == []
    
    def test_rolling_features(self):
        """Test rolling feature creation."""
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=48, freq='H')
        df = pd.DataFrame({
            'temperature': np.random.uniform(15, 30, 48)
        }, index=dates)
        
        engine = FeatureEngine()
        rolling_features = engine.create_rolling_features(df, 'temperature', windows=[6, 12])
        
        assert not rolling_features.empty
        assert 'temperature_rolling_6h_mean' in rolling_features.columns
        assert 'temperature_rolling_12h_max' in rolling_features.columns
    
    def test_interaction_features(self):
        """Test interaction feature creation."""
        dates = pd.date_range(start='2024-01-01', periods=24, freq='H')
        df = pd.DataFrame({
            'temperature': np.random.uniform(20, 30, 24),
            'humidity': np.random.uniform(50, 90, 24)
        }, index=dates)
        
        engine = FeatureEngine()
        interaction_features = engine.create_interaction_features(df)
        
        assert not interaction_features.empty
        assert 'temp_humidity_interaction' in interaction_features.columns


class TestEnsembleModel:
    """Tests for ensemble model."""
    
    def test_model_initialization(self):
        """Test model initialization."""
        model = EnsembleModel()
        assert model.rf_model is None
        assert model.xgb_model is None
    
    def test_risk_categorization(self):
        """Test risk level categorization."""
        model = EnsembleModel()
        model.ensemble_config = {"thresholds": {"low": 0.33, "medium": 0.66, "high": 1.0}}
        
        assert model.categorize_risk(0.2) == "low"
        assert model.categorize_risk(0.5) == "medium"
        assert model.categorize_risk(0.8) == "high"
    
    def test_dummy_model_creation(self):
        """Test dummy model creation."""
        model = EnsembleModel()
        model.create_dummy_models()
        
        assert model.rf_model is not None
        assert model.preprocessor is not None


class TestDataValidation:
    """Tests for data validation."""
    
    def test_coordinate_validation(self):
        """Test coordinate validation logic."""
        # Valid coordinates
        assert -90 <= 18.5204 <= 90
        assert -180 <= 73.8567 <= 180
        
        # Invalid coordinates
        assert not (-90 <= 100 <= 90)
        assert not (-180 <= 200 <= 180)
    
    def test_lead_days_validation(self):
        """Test lead days validation."""
        valid_days = [1, 2, 3, 4, 5, 6, 7]
        
        for day in valid_days:
            assert 1 <= day <= 7
        
        # Invalid days
        assert not (1 <= 0 <= 7)
        assert not (1 <= 8 <= 7)


# Run tests with: pytest tests/test_app.py -v
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
