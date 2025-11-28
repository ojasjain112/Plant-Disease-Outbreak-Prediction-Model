"""
Configuration settings for the Weather-Driven Disease Outbreak Predictor.
"""

import os
from typing import Dict, List

# Application settings
APP_NAME = "Weather-Driven Plant Disease Outbreak Predictor"
APP_DESCRIPTION = "Predict daily plant disease outbreak risk over a 1–7 day window using weather forecasts and ML models"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

# Open-Meteo API settings
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Weather parameters - Expanded for better plant disease prediction
WEATHER_PARAMS = {
    "hourly": [
        # Temperature variables
        "temperature_2m",              # Air temperature at 2m
        "temperature_80m",             # Temperature at 80m (upper air)
        "temperature_120m",            # Temperature at 120m
        "soil_temperature_0cm",        # Surface soil temperature
        "soil_temperature_6cm",        # Soil temperature at 6cm depth
        "soil_temperature_18cm",       # Soil temperature at 18cm depth
        "soil_temperature_54cm",       # Deep soil temperature
        
        # Humidity and moisture
        "relative_humidity_2m",        # Relative humidity at 2m
        "dew_point_2m",                # Dew point temperature
        "soil_moisture_0_1cm",         # Surface soil moisture
        "soil_moisture_1_3cm",         # Shallow soil moisture
        "soil_moisture_3_9cm",         # Root zone moisture (shallow)
        "soil_moisture_9_27cm",        # Root zone moisture (medium)
        "soil_moisture_27_81cm",       # Deep root zone moisture
        
        # Precipitation
        "precipitation",               # Total precipitation
        "rain",                        # Liquid precipitation
        "snowfall",                    # Snowfall amount
        "precipitation_probability",   # Probability of precipitation
        "showers",                     # Shower precipitation
        
        # Wind
        "wind_speed_10m",              # Wind speed at 10m
        "wind_speed_80m",              # Wind speed at 80m
        "wind_speed_120m",             # Wind speed at 120m
        "wind_direction_10m",          # Wind direction at 10m
        "wind_direction_80m",          # Wind direction at 80m
        "wind_gusts_10m",              # Wind gusts
        
        # Atmospheric pressure
        "pressure_msl",                # Mean sea level pressure
        "surface_pressure",            # Surface pressure
        
        # Cloud cover and radiation
        "cloud_cover",                 # Total cloud cover
        "cloud_cover_low",             # Low level clouds
        "cloud_cover_mid",             # Mid level clouds
        "cloud_cover_high",            # High level clouds
        "shortwave_radiation",         # Solar radiation
        "direct_radiation",            # Direct solar radiation
        "diffuse_radiation",           # Diffuse solar radiation
        "direct_normal_irradiance",    # DNI
        
        # Additional atmospheric variables
        "vapour_pressure_deficit",     # VPD (critical for disease)
        "evapotranspiration",          # ET (water loss)
        "et0_fao_evapotranspiration",  # Reference ET
        "weather_code",                # Weather condition code
        "visibility",                  # Atmospheric visibility
        "is_day",                      # Day/night indicator
        
        # Boundary layer
        "cape",                        # Convective available potential energy
        "lifted_index",                # Atmospheric stability
        "freezing_level_height",       # Height of 0°C level
        "sunshine_duration",           # Duration of sunshine
    ],
    "temperature_unit": "celsius",
    "windspeed_unit": "kmh",
    "precipitation_unit": "mm",
    "timezone": "auto"
}

FORECAST_DAYS = 7
PAST_DAYS = 30

# Model settings
MODEL_DIR = "models"
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "preprocessor.pkl")
RF_MODEL_PATH = os.path.join(MODEL_DIR, "rf_model.pkl")
XGB_MODEL_PATH = os.path.join(MODEL_DIR, "xgb_model.json")
ENSEMBLE_CONFIG_PATH = os.path.join(MODEL_DIR, "ensemble_config.json")

# Lead time configuration
LEAD_DAYS = [1, 2, 3, 4, 5, 6, 7]

# Risk thresholds
RISK_THRESHOLDS = {
    "low": 0.33,
    "medium": 0.66,
    "high": 1.0
}

# Feature engineering settings - Expanded for better predictions
ROLLING_WINDOWS = [3, 6, 12, 24, 48, 72]  # hours (3h, 6h, 12h, 1d, 2d, 3d)
AGGREGATION_FUNCTIONS = ["mean", "min", "max", "std", "sum"]
LAG_PERIODS = [1, 3, 6, 12, 24, 48, 72]  # hours
DELTA_PERIODS = [1, 3, 6, 12, 24]  # hours for computing changes

# Cache settings
CACHE_DURATION_SECONDS = 3600  # 1 hour
CACHE_DIR = "cache"

# Data directories
DATA_DIR = "data"
OUTBREAKS_CSV = os.path.join(DATA_DIR, "outbreaks.csv")

# Logging settings
LOG_FORMAT = "json"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Model training settings
TRAIN_TEST_SPLIT_DATE = "2023-01-01"  # Example split date
VALIDATION_SPLIT = 0.2
RANDOM_STATE = 42

# Plant disease types
DISEASE_TYPES = [
    "powdery_mildew",
    "downy_mildew",
    "late_blight",
    "early_blight",
    "leaf_spot",
    "coffee_rust",
    "cedar_apple_rust",
    "wheat_stem_rust",
    "corn_smut",
    "bunt",
    "anthracnose",
    "botrytis_gray_mold",
    "damping_off",
    "clubroot",
    "fusarium_wilt_panama_disease",
    "verticillium_wilt",
    "oak_wilt"
]

# Top N features to display
TOP_N_FEATURES = 5
