"""
Feature engineering script for building ML features from weather data.
This script demonstrates the feature engineering pipeline.
"""

import os
import sys
import argparse
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from features import FeatureEngine
from weather_api import WeatherAPI


def main():
    """Demonstrate feature engineering pipeline."""
    parser = argparse.ArgumentParser(description="Feature engineering demo")
    parser.add_argument('--lat', type=float, default=18.5204,
                       help='Latitude for demo')
    parser.add_argument('--lon', type=float, default=73.8567,
                       help='Longitude for demo')
    
    args = parser.parse_args()
    
    print("Feature Engineering Demo")
    print("=" * 50)
    
    # Fetch weather data
    print(f"\n1. Fetching weather data for ({args.lat}, {args.lon})...")
    weather_api = WeatherAPI()
    
    try:
        weather_df, location_meta = weather_api.get_weather_for_prediction(
            args.lat, args.lon
        )
        print(f"   Fetched {len(weather_df)} hourly records")
        print(f"   Date range: {weather_df.index.min()} to {weather_df.index.max()}")
    except Exception as e:
        print(f"   Error fetching weather: {e}")
        return
    
    # Engineer features
    print("\n2. Engineering features...")
    feature_engine = FeatureEngine()
    
    try:
        feature_df = feature_engine.engineer_features(weather_df)
        print(f"   Created {len(feature_df.columns)} features")
        print(f"   Feature shape: {feature_df.shape}")
        print(f"\n   Sample features:")
        print(feature_df.head())
        
        # Show feature statistics
        print(f"\n   Feature statistics:")
        print(feature_df.describe())
        
    except Exception as e:
        print(f"   Error engineering features: {e}")
        return
    
    # Prepare features for prediction
    print("\n3. Preparing features for prediction (Days 1-7)...")
    lead_days = [1, 2, 3, 4, 5, 6, 7]
    
    try:
        lead_day_features = feature_engine.prepare_features_for_prediction(
            weather_df, lead_days
        )
        
        for day, features in lead_day_features.items():
            print(f"   Day {day}: {features.shape[1]} features")
            
    except Exception as e:
        print(f"   Error preparing prediction features: {e}")
        return
    
    print("\n" + "=" * 50)
    print("Feature engineering demo complete!")


if __name__ == '__main__':
    main()
