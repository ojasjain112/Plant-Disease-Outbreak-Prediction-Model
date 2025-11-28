"""
Feature engineering module for creating ML features from weather data.
"""

from typing import Dict, List
import numpy as np
import pandas as pd

import config


class FeatureEngine:
    """Engineer features from raw weather data for ML models."""
    
    def __init__(self):
        """Initialize the feature engineering engine."""
        self.feature_names = []
    
    def create_rolling_features(
        self,
        df: pd.DataFrame,
        column: str,
        windows: List[int] = config.ROLLING_WINDOWS
    ) -> pd.DataFrame:
        """
        Create rolling window statistics for a column.
        
        Args:
            df: Input DataFrame with datetime index
            column: Column name to compute rolling stats
            windows: List of window sizes in hours
            
        Returns:
            DataFrame with rolling features
        """
        features = pd.DataFrame(index=df.index)
        
        for window in windows:
            for func in config.AGGREGATION_FUNCTIONS:
                feature_name = f"{column}_rolling_{window}h_{func}"
                
                if func == "mean":
                    features[feature_name] = df[column].rolling(window=window, min_periods=1).mean()
                elif func == "min":
                    features[feature_name] = df[column].rolling(window=window, min_periods=1).min()
                elif func == "max":
                    features[feature_name] = df[column].rolling(window=window, min_periods=1).max()
                elif func == "std":
                    features[feature_name] = df[column].rolling(window=window, min_periods=1).std()
        
        return features
    
    def create_lag_features(
        self,
        df: pd.DataFrame,
        column: str,
        lags: List[int] = None
    ) -> pd.DataFrame:
        """
        Create lagged features.
        
        Args:
            df: Input DataFrame
            column: Column to lag
            lags: List of lag periods in hours (uses config if None)
            
        Returns:
            DataFrame with lagged features
        """
        if lags is None:
            lags = config.LAG_PERIODS
            
        features = pd.DataFrame(index=df.index)
        
        for lag in lags:
            feature_name = f"{column}_lag_{lag}h"
            features[feature_name] = df[column].shift(lag)
        
        return features
    
    def create_delta_features(
        self,
        df: pd.DataFrame,
        column: str,
        periods: List[int] = None
    ) -> pd.DataFrame:
        """
        Create change/delta features.
        
        Args:
            df: Input DataFrame
            column: Column to compute deltas
            periods: List of periods for computing change (uses config if None)
            
        Returns:
            DataFrame with delta features
        """
        if periods is None:
            periods = config.DELTA_PERIODS
            
        features = pd.DataFrame(index=df.index)
        
        for period in periods:
            feature_name = f"{column}_delta_{period}h"
            features[feature_name] = df[column].diff(period)
        
        return features
    
    def create_disease_specific_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create disease-specific calculated features.
        These are critical environmental indicators for plant disease development.
        
        Args:
            df: Input DataFrame with weather variables
            
        Returns:
            DataFrame with disease-specific features
        """
        features = pd.DataFrame(index=df.index)
        
        # 1. Leaf Wetness Duration (LWD) - Critical for fungal diseases
        # Estimate based on humidity, dew point, and precipitation
        if "relative_humidity_2m" in df.columns:
            # High humidity (>85%) indicates likely leaf wetness
            features["leaf_wetness_indicator"] = (df["relative_humidity_2m"] > 85).astype(int)
            
            if "precipitation" in df.columns:
                # Precipitation directly causes leaf wetness
                features["leaf_wetness_from_rain"] = (df["precipitation"] > 0).astype(int)
                # Combined leaf wetness
                features["leaf_wetness_combined"] = (
                    (df["relative_humidity_2m"] > 85) | (df["precipitation"] > 0)
                ).astype(int)
        
        # 2. Vapor Pressure Deficit (VPD) - Critical for disease development
        if "temperature_2m" in df.columns and "relative_humidity_2m" in df.columns:
            # Calculate saturation vapor pressure using Magnus formula
            temp = df["temperature_2m"]
            svp = 0.6108 * np.exp((17.27 * temp) / (temp + 237.3))
            # Calculate actual vapor pressure
            avp = (df["relative_humidity_2m"] / 100) * svp
            # VPD = SVP - AVP
            features["vpd_calculated"] = svp - avp
            
            # VPD categories (important for different diseases)
            features["vpd_low"] = (features["vpd_calculated"] < 0.5).astype(int)
            features["vpd_optimal"] = ((features["vpd_calculated"] >= 0.5) & 
                                       (features["vpd_calculated"] <= 1.5)).astype(int)
            features["vpd_high"] = (features["vpd_calculated"] > 1.5).astype(int)
        
        # 3. Temperature ranges for different disease groups
        if "temperature_2m" in df.columns:
            temp = df["temperature_2m"]
            
            # Cold-loving pathogens (5-15°C) - Late blight, downy mildew
            features["temp_range_cold"] = ((temp >= 5) & (temp <= 15)).astype(int)
            
            # Cool-moderate pathogens (15-20°C) - Early blight, leaf spots
            features["temp_range_cool"] = ((temp > 15) & (temp <= 20)).astype(int)
            
            # Warm pathogens (20-25°C) - Powdery mildew, rusts
            features["temp_range_warm"] = ((temp > 20) & (temp <= 25)).astype(int)
            
            # Hot pathogens (25-30°C) - Some bacterial diseases
            features["temp_range_hot"] = ((temp > 25) & (temp <= 30)).astype(int)
            
            # Extreme temperatures (unfavorable for most diseases)
            features["temp_extreme_cold"] = (temp < 5).astype(int)
            features["temp_extreme_hot"] = (temp > 30).astype(int)
            
            # Diurnal temperature range (important for some diseases)
            if "temperature_80m" in df.columns:
                features["temp_gradient_vertical"] = df["temperature_2m"] - df["temperature_80m"]
        
        # 4. Humidity-based features
        if "relative_humidity_2m" in df.columns:
            humidity = df["relative_humidity_2m"]
            
            # Critical humidity thresholds
            features["humidity_very_high"] = (humidity > 90).astype(int)
            features["humidity_high"] = ((humidity > 80) & (humidity <= 90)).astype(int)
            features["humidity_moderate"] = ((humidity >= 60) & (humidity <= 80)).astype(int)
            features["humidity_low"] = (humidity < 60).astype(int)
            
            # Hours of high humidity (fungal spore germination)
            features["high_humidity_hours"] = (humidity > 85).astype(int)
        
        # 5. Precipitation patterns
        if "precipitation" in df.columns:
            precip = df["precipitation"]
            
            # Precipitation categories
            features["has_precipitation"] = (precip > 0).astype(int)
            features["light_rain"] = ((precip > 0) & (precip <= 2)).astype(int)
            features["moderate_rain"] = ((precip > 2) & (precip <= 10)).astype(int)
            features["heavy_rain"] = (precip > 10).astype(int)
            
            # Cumulative precipitation (rolling sum)
            features["precip_sum_24h"] = precip.rolling(window=24, min_periods=1).sum()
            features["precip_sum_48h"] = precip.rolling(window=48, min_periods=1).sum()
            features["precip_sum_72h"] = precip.rolling(window=72, min_periods=1).sum()
            
            # Consecutive wet hours
            features["wet_hour"] = (precip > 0).astype(int)
            
            # Dry spell after rain (important for spore dispersal)
            if "relative_humidity_2m" in df.columns:
                features["drying_conditions"] = ((precip == 0) & 
                                                 (df["relative_humidity_2m"] < 70)).astype(int)
        
        # 6. Wind-based features (spore dispersal)
        if "wind_speed_10m" in df.columns:
            wind = df["wind_speed_10m"]
            
            # Wind categories
            features["wind_calm"] = (wind < 5).astype(int)
            features["wind_light"] = ((wind >= 5) & (wind < 15)).astype(int)
            features["wind_moderate"] = ((wind >= 15) & (wind < 25)).astype(int)
            features["wind_strong"] = (wind >= 25).astype(int)
            
            # Wind with rain (spore splash dispersal)
            if "precipitation" in df.columns:
                features["wind_driven_rain"] = ((wind > 10) & (precip > 0)).astype(int)
        
        # 7. Cloud cover and solar radiation (affects leaf drying)
        if "cloud_cover" in df.columns:
            cloud = df["cloud_cover"]
            
            features["overcast"] = (cloud > 80).astype(int)
            features["partly_cloudy"] = ((cloud >= 40) & (cloud <= 80)).astype(int)
            features["clear_sky"] = (cloud < 40).astype(int)
            
            # Overcast with high humidity (ideal for many diseases)
            if "relative_humidity_2m" in df.columns:
                features["overcast_humid"] = ((cloud > 80) & 
                                              (df["relative_humidity_2m"] > 80)).astype(int)
        
        # 8. Soil conditions (for soil-borne diseases)
        if "soil_moisture_0_1cm" in df.columns:
            soil_moist = df["soil_moisture_0_1cm"]
            
            features["soil_very_wet"] = (soil_moist > 0.4).astype(int)
            features["soil_moist"] = ((soil_moist >= 0.2) & (soil_moist <= 0.4)).astype(int)
            features["soil_dry"] = (soil_moist < 0.2).astype(int)
            
            # Soil temperature + moisture combinations
            if "soil_temperature_0cm" in df.columns:
                soil_temp = df["soil_temperature_0cm"]
                
                # Warm + wet soil (damping-off, root rots)
                features["soil_warm_wet"] = ((soil_temp > 20) & (soil_moist > 0.3)).astype(int)
                
                # Cool + wet soil (clubroot)
                features["soil_cool_wet"] = ((soil_temp < 20) & (soil_moist > 0.3)).astype(int)
        
        # 9. Pressure trends (weather pattern changes)
        if "pressure_msl" in df.columns:
            pressure = df["pressure_msl"]
            
            # Pressure change (falling pressure = incoming weather system)
            features["pressure_falling"] = (pressure.diff() < -1).astype(int)
            features["pressure_rising"] = (pressure.diff() > 1).astype(int)
            features["pressure_stable"] = (np.abs(pressure.diff()) <= 1).astype(int)
        
        # 10. Dew point depression (dew point vs temperature)
        if "dew_point_2m" in df.columns and "temperature_2m" in df.columns:
            features["dew_point_depression"] = df["temperature_2m"] - df["dew_point_2m"]
            
            # Low depression = near saturation (high disease risk)
            features["near_saturation"] = (features["dew_point_depression"] < 2).astype(int)
        
        # 11. Combined risk indices
        if "temperature_2m" in df.columns and "relative_humidity_2m" in df.columns:
            # Late blight risk (cool + wet)
            if "precipitation" in df.columns:
                features["late_blight_conditions"] = (
                    (df["temperature_2m"] >= 10) & 
                    (df["temperature_2m"] <= 25) &
                    (df["relative_humidity_2m"] > 85)
                ).astype(int)
            
            # Powdery mildew risk (warm + moderate humidity)
            features["powdery_mildew_conditions"] = (
                (df["temperature_2m"] >= 18) & 
                (df["temperature_2m"] <= 28) &
                (df["relative_humidity_2m"] >= 40) &
                (df["relative_humidity_2m"] <= 85)
            ).astype(int)
            
            # Rust disease conditions (moderate temp + high humidity)
            features["rust_conditions"] = (
                (df["temperature_2m"] >= 15) & 
                (df["temperature_2m"] <= 25) &
                (df["relative_humidity_2m"] > 80)
            ).astype(int)
            
            # Botrytis/gray mold (cool + very humid)
            features["botrytis_conditions"] = (
                (df["temperature_2m"] >= 15) & 
                (df["temperature_2m"] <= 23) &
                (df["relative_humidity_2m"] > 90)
            ).astype(int)
        
        # 12. Evapotranspiration-based features
        if "evapotranspiration" in df.columns:
            et = df["evapotranspiration"]
            
            features["et_low"] = (et < 1).astype(int)
            features["et_moderate"] = ((et >= 1) & (et < 3)).astype(int)
            features["et_high"] = (et >= 3).astype(int)
            
            # Low ET with high humidity = disease favorable
            if "relative_humidity_2m" in df.columns:
                features["low_et_high_humidity"] = (
                    (et < 1) & (df["relative_humidity_2m"] > 80)
                ).astype(int)
        
        # 13. Day/Night patterns
        if "is_day" in df.columns:
            # Night-time high humidity (dew formation)
            if "relative_humidity_2m" in df.columns:
                features["night_high_humidity"] = (
                    (df["is_day"] == 0) & (df["relative_humidity_2m"] > 85)
                ).astype(int)
        
        # 14. Freezing conditions
        if "temperature_2m" in df.columns:
            features["freezing"] = (df["temperature_2m"] <= 0).astype(int)
            features["near_freezing"] = ((df["temperature_2m"] > 0) & 
                                         (df["temperature_2m"] < 5)).astype(int)
        
        return features
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between weather variables.
        Enhanced with more sophisticated interactions.
        
        Args:
            df: Input DataFrame with weather variables
            
        Returns:
            DataFrame with interaction features
        """
        features = pd.DataFrame(index=df.index)
        
        # Temperature × Humidity (heat stress index)
        if "temperature_2m" in df.columns and "relative_humidity_2m" in df.columns:
            features["temp_humidity_product"] = df["temperature_2m"] * df["relative_humidity_2m"]
            features["temp_humidity_ratio"] = df["temperature_2m"] / (df["relative_humidity_2m"] + 1)
        
        # Precipitation × Wind Speed (splash dispersal potential)
        if "precipitation" in df.columns and "wind_speed_10m" in df.columns:
            features["precip_wind_product"] = df["precipitation"] * df["wind_speed_10m"]
        
        # Temperature × Cloud Cover (radiation effect)
        if "temperature_2m" in df.columns and "cloud_cover" in df.columns:
            features["temp_cloud_product"] = df["temperature_2m"] * df["cloud_cover"]
        
        # Humidity × Cloud Cover (condensation potential)
        if "relative_humidity_2m" in df.columns and "cloud_cover" in df.columns:
            features["humidity_cloud_product"] = df["relative_humidity_2m"] * df["cloud_cover"]
        
        # Soil moisture × Soil temperature (root disease risk)
        if "soil_moisture_0_1cm" in df.columns and "soil_temperature_0cm" in df.columns:
            features["soil_moist_temp_product"] = df["soil_moisture_0_1cm"] * df["soil_temperature_0cm"]
        
        # Wind × Humidity (drying potential)
        if "wind_speed_10m" in df.columns and "relative_humidity_2m" in df.columns:
            features["wind_humidity_ratio"] = df["wind_speed_10m"] / (df["relative_humidity_2m"] + 1)
        
        # Precipitation × Humidity (wetness duration proxy)
        if "precipitation" in df.columns and "relative_humidity_2m" in df.columns:
            features["precip_humidity_product"] = df["precipitation"] * df["relative_humidity_2m"]
        
        # Temperature range (if multiple temperature levels available)
        if "temperature_2m" in df.columns and "temperature_80m" in df.columns:
            features["temp_range_vertical"] = np.abs(df["temperature_2m"] - df["temperature_80m"])
        
        # Soil temperature gradient
        if "soil_temperature_0cm" in df.columns and "soil_temperature_6cm" in df.columns:
            features["soil_temp_gradient"] = df["soil_temperature_0cm"] - df["soil_temperature_6cm"]
        
        # Pressure × Wind (storm intensity)
        if "pressure_msl" in df.columns and "wind_speed_10m" in df.columns:
            features["pressure_wind_interaction"] = df["pressure_msl"] * df["wind_speed_10m"]
        
        return features
    
    def create_daily_aggregates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate hourly data to daily statistics.
        
        Args:
            df: Hourly weather DataFrame
            
        Returns:
            Daily aggregated DataFrame
        """
        daily_features = []
        
        # Group by date
        df_copy = df.copy()
        df_copy["date"] = df_copy.index.date
        
        for column in df.columns:
            if column == "date":
                continue
            
            daily = df_copy.groupby("date")[column].agg([
                ("mean", "mean"),
                ("min", "min"),
                ("max", "max"),
                ("std", "std"),
                ("sum", "sum")
            ])
            
            # Rename columns
            daily.columns = [f"{column}_daily_{stat}" for stat in daily.columns]
            daily_features.append(daily)
        
        # Combine all features
        result = pd.concat(daily_features, axis=1)
        
        return result
    
    def engineer_features(
        self,
        weather_df: pd.DataFrame,
        for_training: bool = False
    ) -> pd.DataFrame:
        """
        Complete feature engineering pipeline.
        
        Args:
            weather_df: Raw weather DataFrame with hourly data
            for_training: Whether this is for training (includes labels) or prediction
            
        Returns:
            Engineered feature DataFrame
        """
        all_features = []
        
        # 1. Daily aggregates of raw features
        daily_agg = self.create_daily_aggregates(weather_df)
        all_features.append(daily_agg)
        
        # 2. Rolling statistics
        for column in ["temperature", "humidity", "precipitation", "wind_speed", "pressure", "cloud_cover"]:
            if column in weather_df.columns:
                rolling_feats = self.create_rolling_features(weather_df, column)
                # Aggregate rolling features to daily
                rolling_feats["date"] = rolling_feats.index.date
                rolling_daily = rolling_feats.groupby("date").mean()
                all_features.append(rolling_daily)
        
        # 3. Delta features (day-over-day changes)
        # Compute on daily aggregates
        for column in daily_agg.columns:
            if "_mean" in column:
                delta_feat = daily_agg[[column]].diff()
                delta_feat.columns = [f"{column}_delta"]
                all_features.append(delta_feat)
        
        # 4. Interaction features on hourly data, then aggregate
        interaction_feats = self.create_interaction_features(weather_df)
        if not interaction_feats.empty:
            interaction_feats["date"] = interaction_feats.index.date
            interaction_daily = interaction_feats.groupby("date").mean()
            all_features.append(interaction_daily)
        
        # 5. Disease-specific calculated features
        disease_features = self.create_disease_specific_features(weather_df)
        if not disease_features.empty:
            disease_features["date"] = disease_features.index.date
            disease_daily = disease_features.groupby("date").mean()
            all_features.append(disease_daily)
        
        # Combine all features
        feature_df = pd.concat(all_features, axis=1)
        
        # Fill NaN values (from rolling/lagging) - using updated pandas methods
        feature_df = feature_df.bfill().ffill().fillna(0)
        
        # Store feature names
        self.feature_names = list(feature_df.columns)
        
        return feature_df
    
    def prepare_features_for_prediction(
        self,
        weather_df: pd.DataFrame,
        lead_days: List[int]
    ) -> Dict[int, pd.DataFrame]:
        """
        Prepare features for each lead day prediction.
        
        Args:
            weather_df: Raw weather DataFrame
            lead_days: List of lead days to predict
            
        Returns:
            Dictionary mapping lead_day -> feature vector (single row DataFrame)
        """
        # Engineer all features
        feature_df = self.engineer_features(weather_df, for_training=False)
        
        # Get today's date (last date with complete data)
        today = pd.Timestamp.now().normalize()
        
        # Prepare features for each lead day
        lead_day_features = {}
        
        for lead_day in lead_days:
            target_date = (today + pd.Timedelta(days=lead_day)).date()
            
            # Get features for target date
            if target_date in feature_df.index:
                lead_day_features[lead_day] = feature_df.loc[[target_date]]
            else:
                # Use the last available date if target not in forecast
                last_date = feature_df.index[-1]
                lead_day_features[lead_day] = feature_df.loc[[last_date]]
        
        return lead_day_features
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of all feature names.
        
        Returns:
            List of feature names
        """
        return self.feature_names
