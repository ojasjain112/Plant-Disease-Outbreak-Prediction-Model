"""
Flask application for Weather-Driven Disease Outbreak Predictor.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List

from flask import Flask, render_template, request, jsonify
import pandas as pd

import config
from weather_api import WeatherAPI
from features import FeatureEngine
from ml_model import initialize_model


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Initialize components
weather_api = WeatherAPI()
feature_engine = FeatureEngine()
ml_model = initialize_model()

logger.info("Application initialized successfully")


@app.route('/')
def index():
    """
    Home page with map interface and prediction inputs.
    
    Returns:
        Rendered HTML template
    """
    return render_template(
        'index.html',
        app_name=config.APP_NAME,
        app_description=config.APP_DESCRIPTION,
        lead_days=config.LEAD_DAYS,
        disease_types=config.DISEASE_TYPES
    )


@app.route('/test')
def test_page():
    """Test page for debugging API."""
    from flask import send_file
    return send_file('test_prediction.html')


@app.route('/predict', methods=['POST'])
def predict():
    """
    Prediction endpoint to compute outbreak risk.
    
    Expected JSON payload:
        {
            "latitude": float,
            "longitude": float,
            "lead_days": [1, 2, 3, ...],
            "disease": str (optional)
        }
    
    Returns:
        JSON response with predictions for each lead day
    """
    try:
        # Parse request data
        data = request.get_json()
        logger.info(f"Received prediction request: {data}")
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Validate required fields
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        lead_days = data.get('lead_days', config.LEAD_DAYS)
        disease = data.get('disease', 'unknown')
        
        if latitude is None or longitude is None:
            return jsonify({
                "status": "error",
                "message": "Latitude and longitude are required"
            }), 400
        
        # Validate coordinates
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        except ValueError as e:
            return jsonify({
                "status": "error",
                "message": f"Invalid coordinates: {e}"
            }), 400
        
        # Validate lead days
        if not isinstance(lead_days, list) or not lead_days:
            lead_days = config.LEAD_DAYS
        
        lead_days = [int(d) for d in lead_days if 1 <= int(d) <= 7]
        if not lead_days:
            return jsonify({
                "status": "error",
                "message": "At least one valid lead day (1-7) required"
            }), 400
        
        logger.info(f"Prediction request: lat={latitude}, lon={longitude}, days={lead_days}, disease={disease}")
        
        # Step 1: Fetch weather data
        try:
            weather_df, location_meta = weather_api.get_weather_for_prediction(latitude, longitude)
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return jsonify({
                "status": "error",
                "message": f"Failed to fetch weather data: {str(e)}"
            }), 500
        
        # Step 2: Engineer features
        try:
            # First engineer the full feature set for statistics
            features_df = feature_engine.engineer_features(weather_df, for_training=False)
            # Then prepare lead day specific features
            lead_day_features = feature_engine.prepare_features_for_prediction(weather_df, lead_days)
        except Exception as e:
            logger.error(f"Feature engineering error: {e}")
            return jsonify({
                "status": "error",
                "message": f"Failed to process features: {str(e)}"
            }), 500
        
        # Step 3: Run predictions
        try:
            predictions = ml_model.predict_for_lead_days(lead_day_features)
        except Exception as e:
            logger.error(f"Model prediction error: {e}")
            return jsonify({
                "status": "error",
                "message": f"Prediction failed: {str(e)}"
            }), 500
        
        # Step 4: Prepare response
        risk_by_day = [predictions[day] for day in sorted(lead_days) if day in predictions]
        
        # Extract top features by day
        top_features_by_day = {
            str(day): predictions[day]["top_features"]
            for day in lead_days if day in predictions
        }
        
        # Get weather summary
        weather_summary = _get_weather_summary(weather_df)
        
        # Get detailed weather parameters (all 53 parameters)
        weather_parameters = _get_weather_parameters_detail(weather_df)
        
        # Get feature engineering statistics
        feature_stats = _get_feature_statistics(features_df)
        
        response = {
            "status": "ok",
            "location": {
                "lat": latitude,
                "lon": longitude,
                "timezone": location_meta.get("timezone", "UTC")
            },
            "disease": disease,
            "risk_by_day": risk_by_day,
            "top_features_by_day": top_features_by_day,
            "weather_summary": weather_summary,
            "weather_parameters": weather_parameters,
            "feature_statistics": feature_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Prediction successful for {len(risk_by_day)} days")
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Unexpected error in prediction: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred"
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    
    Returns:
        JSON with service status
    """
    return jsonify({
        "status": "healthy",
        "service": config.APP_NAME,
    "timestamp": datetime.now(timezone.utc).isoformat()
    })


def _get_weather_summary(weather_df: pd.DataFrame) -> Dict:
    """
    Generate a summary of weather trends.
    
    Args:
        weather_df: Weather DataFrame
        
    Returns:
        Dictionary with weather statistics
    """
    try:
        # Get last 7 days for summary
        recent_df = weather_df.tail(24 * 7)  # Last 7 days of hourly data
        
        summary = {
            "temperature": {
                "mean": round(recent_df["temperature"].mean(), 1) if "temperature" in recent_df else None,
                "min": round(recent_df["temperature"].min(), 1) if "temperature" in recent_df else None,
                "max": round(recent_df["temperature"].max(), 1) if "temperature" in recent_df else None
            },
            "humidity": {
                "mean": round(recent_df["humidity"].mean(), 1) if "humidity" in recent_df else None
            },
            "precipitation": {
                "total": round(recent_df["precipitation"].sum(), 1) if "precipitation" in recent_df else None
            },
            "wind_speed": {
                "mean": round(recent_df["wind_speed"].mean(), 1) if "wind_speed" in recent_df else None,
                "max": round(recent_df["wind_speed"].max(), 1) if "wind_speed" in recent_df else None
            }
        }
        
        return summary
    
    except Exception as e:
        logger.warning(f"Failed to generate weather summary: {e}")
        return {}


def _get_weather_parameters_detail(weather_df: pd.DataFrame) -> Dict:
    """
    Extract detailed statistics for all 53 weather parameters.
    
    Args:
        weather_df: Weather DataFrame
        
    Returns:
        Dictionary with all weather parameter statistics organized by category
    """
    try:
        recent_df = weather_df.tail(24 * 7)  # Last 7 days
        
        def safe_stats(col_name):
            """Safely compute statistics for a column."""
            if col_name in recent_df.columns:
                col = recent_df[col_name]
                return {
                    "mean": float(round(col.mean(), 2)),
                    "min": float(round(col.min(), 2)),
                    "max": float(round(col.max(), 2)),
                    "current": float(round(col.iloc[-1], 2)) if len(col) > 0 else None
                }
            return None
        
        parameters = {
            "temperature": {
                "temperature_2m": safe_stats("temperature_2m"),
                "temperature_80m": safe_stats("temperature_80m"),
                "temperature_120m": safe_stats("temperature_120m"),
                "soil_temperature_0cm": safe_stats("soil_temperature_0cm"),
                "soil_temperature_6cm": safe_stats("soil_temperature_6cm"),
                "soil_temperature_18cm": safe_stats("soil_temperature_18cm"),
                "soil_temperature_54cm": safe_stats("soil_temperature_54cm"),
            },
            "humidity_moisture": {
                "relative_humidity_2m": safe_stats("relative_humidity_2m"),
                "dew_point_2m": safe_stats("dew_point_2m"),
                "vapour_pressure_deficit": safe_stats("vapour_pressure_deficit"),
                "soil_moisture_0_1cm": safe_stats("soil_moisture_0_1cm"),
                "soil_moisture_1_3cm": safe_stats("soil_moisture_1_3cm"),
                "soil_moisture_3_9cm": safe_stats("soil_moisture_3_9cm"),
                "soil_moisture_9_27cm": safe_stats("soil_moisture_9_27cm"),
                "soil_moisture_27_81cm": safe_stats("soil_moisture_27_81cm"),
            },
            "precipitation": {
                "precipitation": safe_stats("precipitation"),
                "rain": safe_stats("rain"),
                "snowfall": safe_stats("snowfall"),
                "showers": safe_stats("showers"),
                "precipitation_probability": safe_stats("precipitation_probability"),
            },
            "wind": {
                "wind_speed_10m": safe_stats("wind_speed_10m"),
                "wind_speed_80m": safe_stats("wind_speed_80m"),
                "wind_speed_120m": safe_stats("wind_speed_120m"),
                "wind_direction_10m": safe_stats("wind_direction_10m"),
                "wind_direction_80m": safe_stats("wind_direction_80m"),
                "wind_gusts_10m": safe_stats("wind_gusts_10m"),
            },
            "pressure": {
                "pressure_msl": safe_stats("pressure_msl"),
                "surface_pressure": safe_stats("surface_pressure"),
            },
            "cloud_radiation": {
                "cloud_cover": safe_stats("cloud_cover"),
                "cloud_cover_low": safe_stats("cloud_cover_low"),
                "cloud_cover_mid": safe_stats("cloud_cover_mid"),
                "cloud_cover_high": safe_stats("cloud_cover_high"),
                "shortwave_radiation": safe_stats("shortwave_radiation"),
                "direct_radiation": safe_stats("direct_radiation"),
                "diffuse_radiation": safe_stats("diffuse_radiation"),
                "direct_normal_irradiance": safe_stats("direct_normal_irradiance"),
            },
            "evapotranspiration": {
                "evapotranspiration": safe_stats("evapotranspiration"),
                "et0_fao_evapotranspiration": safe_stats("et0_fao_evapotranspiration"),
            },
            "atmospheric": {
                "visibility": safe_stats("visibility"),
                "cape": safe_stats("cape"),
                "lifted_index": safe_stats("lifted_index"),
                "freezing_level_height": safe_stats("freezing_level_height"),
                "sunshine_duration": safe_stats("sunshine_duration"),
            }
        }
        
        # Remove None values
        parameters = {
            category: {k: v for k, v in params.items() if v is not None}
            for category, params in parameters.items()
        }
        
        return parameters
    
    except Exception as e:
        logger.warning(f"Failed to extract weather parameters: {e}")
        return {}


def _get_feature_statistics(features_df: pd.DataFrame) -> Dict:
    """
    Generate statistics about engineered features.
    
    Args:
        features_df: Features DataFrame
        
    Returns:
        Dictionary with feature statistics by type
    """
    try:
        stats = {
            "total_features": int(len(features_df.columns)),
            "feature_types": {},
            "sample_features": {}
        }
        
        # Categorize features
        rolling_features = [col for col in features_df.columns if 'rolling' in col.lower()]
        lag_features = [col for col in features_df.columns if 'lag' in col.lower()]
        delta_features = [col for col in features_df.columns if 'delta' in col.lower()]
        interaction_features = [col for col in features_df.columns if any(x in col for x in ['_x_', '_per_', '_gradient'])]
        disease_features = [col for col in features_df.columns if any(x in col for x in ['leaf_wetness', 'vpd', 'risk_', 'disease_'])]
        
        stats["feature_types"] = {
            "rolling_window": int(len(rolling_features)),
            "lag": int(len(lag_features)),
            "delta": int(len(delta_features)),
            "interaction": int(len(interaction_features)),
            "disease_specific": int(len(disease_features)),
            "base_weather": int(len(features_df.columns) - len(rolling_features) - len(lag_features) - len(delta_features) - len(interaction_features) - len(disease_features))
        }
        
        # Sample features from each category (top 5)
        stats["sample_features"] = {
            "rolling": rolling_features[:5],
            "lag": lag_features[:5],
            "delta": delta_features[:5],
            "interaction": interaction_features[:5],
            "disease_specific": disease_features[:5]
        }
        
        return stats
    
    except Exception as e:
        logger.warning(f"Failed to generate feature statistics: {e}")
        return {"total_features": 0, "feature_types": {}, "sample_features": {}}


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    
    # Run the app
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
