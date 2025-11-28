"""
Weather API module for fetching data from Open-Meteo.
Includes caching logic to reduce API calls.
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import pandas as pd

import config


class WeatherCache:
    """Simple file-based cache for weather API responses."""
    
    def __init__(self, cache_dir: str = config.CACHE_DIR):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, lat: float, lon: float, data_type: str) -> str:
        """
        Generate a cache key from coordinates and data type.
        
        Args:
            lat: Latitude
            lon: Longitude
            data_type: Type of data (forecast/historical)
            
        Returns:
            Cache key string
        """
        key_str = f"{lat:.4f}_{lon:.4f}_{data_type}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, lat: float, lon: float, data_type: str) -> Optional[Dict]:
        """
        Retrieve cached data if available and not expired.
        
        Args:
            lat: Latitude
            lon: Longitude
            data_type: Type of data
            
        Returns:
            Cached data or None if not found/expired
        """
        cache_key = self._get_cache_key(lat, lon, data_type)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check if cache is expired
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > config.CACHE_DURATION_SECONDS:
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def set(self, lat: float, lon: float, data_type: str, data: Dict) -> None:
        """
        Store data in cache.
        
        Args:
            lat: Latitude
            lon: Longitude
            data_type: Type of data
            data: Data to cache
        """
        cache_key = self._get_cache_key(lat, lon, data_type)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except IOError as e:
            print(f"Warning: Failed to write cache: {e}")


class WeatherAPI:
    """Client for Open-Meteo weather API with caching."""
    
    def __init__(self):
        """Initialize the weather API client."""
        self.cache = WeatherCache()
        self.forecast_url = config.OPEN_METEO_FORECAST_URL
        self.archive_url = config.OPEN_METEO_ARCHIVE_URL
    
    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = config.FORECAST_DAYS,
        past_days: int = 0
    ) -> Dict:
        """
        Fetch weather forecast data from Open-Meteo.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            forecast_days: Number of days to forecast
            past_days: Number of past days to include
            
        Returns:
            Weather data dictionary
            
        Raises:
            requests.RequestException: If API request fails
        """
        # Check cache first
        cache_key = f"forecast_{past_days}"
        cached_data = self.cache.get(latitude, longitude, cache_key)
        if cached_data is not None:
            return cached_data
        
        # Construct API parameters
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(config.WEATHER_PARAMS["hourly"]),
            "temperature_unit": config.WEATHER_PARAMS["temperature_unit"],
            "windspeed_unit": config.WEATHER_PARAMS["windspeed_unit"],
            "precipitation_unit": config.WEATHER_PARAMS["precipitation_unit"],
            "timezone": config.WEATHER_PARAMS["timezone"],
            "forecast_days": forecast_days
        }
        
        if past_days > 0:
            params["past_days"] = past_days
        
        # Make API request
        try:
            response = requests.get(self.forecast_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            self.cache.set(latitude, longitude, cache_key, data)
            
            return data
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch weather forecast: {e}")
    
    def fetch_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Fetch historical weather data from Open-Meteo archive.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Historical weather data dictionary
            
        Raises:
            requests.RequestException: If API request fails
        """
        # Check cache
        cache_key = f"historical_{start_date}_{end_date}"
        cached_data = self.cache.get(latitude, longitude, cache_key)
        if cached_data is not None:
            return cached_data
        
        # Construct API parameters
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(config.WEATHER_PARAMS["hourly"]),
            "temperature_unit": config.WEATHER_PARAMS["temperature_unit"],
            "windspeed_unit": config.WEATHER_PARAMS["windspeed_unit"],
            "precipitation_unit": config.WEATHER_PARAMS["precipitation_unit"],
            "timezone": config.WEATHER_PARAMS["timezone"]
        }
        
        # Make API request
        try:
            response = requests.get(self.archive_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            self.cache.set(latitude, longitude, cache_key, data)
            
            return data
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch historical weather: {e}")
    
    def parse_to_dataframe(self, weather_data: Dict) -> pd.DataFrame:
        """
        Parse Open-Meteo JSON response to pandas DataFrame.
        
        Args:
            weather_data: Raw weather data from API
            
        Returns:
            DataFrame with datetime index and weather variables
        """
        if "hourly" not in weather_data:
            raise ValueError("Invalid weather data format")
        
        hourly = weather_data["hourly"]
        
        # Create DataFrame
        df = pd.DataFrame({
            "datetime": pd.to_datetime(hourly["time"]),
            "temperature": hourly.get("temperature_2m", [None] * len(hourly["time"])),
            "humidity": hourly.get("relative_humidity_2m", [None] * len(hourly["time"])),
            "precipitation": hourly.get("precipitation", [None] * len(hourly["time"])),
            "wind_speed": hourly.get("wind_speed_10m", [None] * len(hourly["time"])),
            "pressure": hourly.get("pressure_msl", [None] * len(hourly["time"])),
            "cloud_cover": hourly.get("cloud_cover", [None] * len(hourly["time"]))
        })
        
        df.set_index("datetime", inplace=True)
        
        return df
    
    def get_weather_for_prediction(
        self,
        latitude: float,
        longitude: float
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fetch and parse weather data needed for prediction.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Tuple of (weather DataFrame, location metadata)
        """
        # Fetch forecast with past days for feature engineering
        weather_data = self.fetch_forecast(
            latitude,
            longitude,
            forecast_days=config.FORECAST_DAYS,
            past_days=config.PAST_DAYS
        )
        
        # Parse to DataFrame
        weather_df = self.parse_to_dataframe(weather_data)
        
        # Extract location metadata
        location_meta = {
            "latitude": weather_data.get("latitude"),
            "longitude": weather_data.get("longitude"),
            "elevation": weather_data.get("elevation"),
            "timezone": weather_data.get("timezone")
        }
        
        return weather_df, location_meta
    
    def get_weather_for_training(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fetch historical weather data for model training.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Tuple of (weather DataFrame, location metadata)
        """
        # Build URL for historical data
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(config.WEATHER_PARAMS["hourly"]),
            "temperature_unit": config.WEATHER_PARAMS.get("temperature_unit", "celsius"),
            "windspeed_unit": config.WEATHER_PARAMS.get("windspeed_unit", "kmh"),
            "precipitation_unit": config.WEATHER_PARAMS.get("precipitation_unit", "mm"),
            "timezone": "UTC"
        }
        
        try:
            response = requests.get(config.OPEN_METEO_ARCHIVE_URL, params=params, timeout=30)
            response.raise_for_status()
            weather_data = response.json()
            
            # Parse to DataFrame with all 53 parameters
            hourly = weather_data["hourly"]
            df_dict = {"datetime": pd.to_datetime(hourly["time"])}
            
            # Add all available weather parameters
            for param in config.WEATHER_PARAMS["hourly"]:
                if param in hourly:
                    df_dict[param] = hourly[param]
            
            df = pd.DataFrame(df_dict)
            df.set_index("datetime", inplace=True)
            
            # Extract location metadata
            location_meta = {
                "latitude": weather_data.get("latitude"),
                "longitude": weather_data.get("longitude"),
                "elevation": weather_data.get("elevation"),
                "timezone": weather_data.get("timezone")
            }
            
            return df, location_meta
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical weather data: {e}")
            # Return empty DataFrame with proper structure
            df = pd.DataFrame()
            return df, {}
