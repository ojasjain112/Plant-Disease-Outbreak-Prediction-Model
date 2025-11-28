"""
Model training script for the ensemble outbreak prediction model.
"""

import os
import sys
import argparse
import json
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc,
    classification_report, confusion_matrix
)
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from features import FeatureEngine

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    print("Warning: XGBoost not available. Using Random Forest only.")
    XGBOOST_AVAILABLE = False


def load_and_prepare_data(outbreak_path: str) -> pd.DataFrame:
    """
    Load outbreak data.
    
    Args:
        outbreak_path: Path to outbreak CSV file
        
    Returns:
        DataFrame with outbreak data
    """
    print(f"Loading data from {outbreak_path}...")
    
    if not os.path.exists(outbreak_path):
        raise FileNotFoundError(f"Outbreak data not found at {outbreak_path}")
    
    df = pd.read_csv(outbreak_path)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"Loaded {len(df)} records")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Outbreak rate: {df['outbreak'].mean()*100:.2f}%")
    
    return df


def create_training_data(outbreak_df: pd.DataFrame) -> tuple:
    """
    Create training features and labels using synthetic data matching real feature engineering.
    
    Note: In production, this would fetch real weather data and use the actual
    feature engineering pipeline. For now, we create synthetic features that
    match the structure and count (~400 features) of the real system.
    
    Args:
        outbreak_df: DataFrame with outbreak records
        
    Returns:
        Tuple of (features_df, labels, dates)
    """
    print("Creating synthetic training features matching the 400+ feature engineering pipeline...")
    
    return create_synthetic_training_data(outbreak_df)


def create_synthetic_training_data(outbreak_df: pd.DataFrame) -> tuple:
    """
    Fallback: Create synthetic training data matching the feature engineering pipeline.
    
    Args:
        outbreak_df: DataFrame with outbreak records
        
    Returns:
        Tuple of (features_df, labels, dates)
    """
    print("Creating synthetic training features matching real feature engineering...")
    
    n_samples = len(outbreak_df)
    np.random.seed(config.RANDOM_STATE)
    
    # Simulate the 53 base weather parameters
    base_features = {}
    
    # Temperature variables (7)
    for var in ['temperature_2m', 'temperature_80m', 'temperature_120m', 
                'soil_temperature_0cm', 'soil_temperature_6cm', 
                'soil_temperature_18cm', 'soil_temperature_54cm']:
        base_features[var] = np.random.uniform(10, 35, n_samples)
    
    # Humidity and moisture (8)
    for var in ['relative_humidity_2m', 'dew_point_2m', 'vapour_pressure_deficit']:
        base_features[var] = np.random.uniform(30, 95, n_samples)
    for var in ['soil_moisture_0_1cm', 'soil_moisture_1_3cm', 'soil_moisture_3_9cm',
                'soil_moisture_9_27cm', 'soil_moisture_27_81cm']:
        base_features[var] = np.random.uniform(0.1, 0.5, n_samples)
    
    # Precipitation (5)
    for var in ['precipitation', 'rain', 'snowfall', 'showers']:
        base_features[var] = np.random.exponential(2, n_samples)
    base_features['precipitation_probability'] = np.random.uniform(0, 100, n_samples)
    
    # Wind (6)
    for var in ['wind_speed_10m', 'wind_speed_80m', 'wind_speed_120m', 'wind_gusts_10m']:
        base_features[var] = np.random.uniform(0, 30, n_samples)
    for var in ['wind_direction_10m', 'wind_direction_80m']:
        base_features[var] = np.random.uniform(0, 360, n_samples)
    
    # Pressure (2)
    for var in ['pressure_msl', 'surface_pressure']:
        base_features[var] = np.random.uniform(990, 1020, n_samples)
    
    # Cloud and radiation (8)
    for var in ['cloud_cover', 'cloud_cover_low', 'cloud_cover_mid', 'cloud_cover_high']:
        base_features[var] = np.random.uniform(0, 100, n_samples)
    for var in ['shortwave_radiation', 'direct_radiation', 'diffuse_radiation', 'direct_normal_irradiance']:
        base_features[var] = np.random.uniform(0, 1000, n_samples)
    
    # Evapotranspiration (2)
    for var in ['evapotranspiration', 'et0_fao_evapotranspiration']:
        base_features[var] = np.random.uniform(0, 10, n_samples)
    
    # Atmospheric (5)
    base_features['visibility'] = np.random.uniform(1000, 50000, n_samples)
    base_features['cape'] = np.random.uniform(0, 3000, n_samples)
    base_features['lifted_index'] = np.random.uniform(-5, 10, n_samples)
    base_features['freezing_level_height'] = np.random.uniform(0, 5000, n_samples)
    base_features['sunshine_duration'] = np.random.uniform(0, 3600, n_samples)
    
    # Add engineered features (rolling, lag, delta, interaction, disease-specific)
    # Simulate ~400 total features to match real system
    engineered = {}
    
    # Rolling features (~180 features: 6 windows * 5 functions * 6 key vars)
    key_vars = ['temperature_2m', 'relative_humidity_2m', 'precipitation', 
                'wind_speed_10m', 'soil_temperature_0cm', 'soil_moisture_0_1cm']
    for window in [3, 6, 12, 24, 48, 72]:
        for func in ['mean', 'min', 'max', 'std', 'sum']:
            for var in key_vars:
                if var in base_features:
                    feat_name = f'{var}_rolling_{window}h_{func}'
                    noise = np.random.normal(0, 1, n_samples)
                    engineered[feat_name] = base_features[var] + noise
    
    # Lag features (~84 features: 7 lags * 12 key vars)
    lag_vars = ['temperature_2m', 'relative_humidity_2m', 'precipitation', 
                'wind_speed_10m', 'pressure_msl', 'cloud_cover',
                'soil_temperature_0cm', 'soil_moisture_0_1cm', 'vapour_pressure_deficit',
                'evapotranspiration', 'wind_direction_10m', 'dew_point_2m']
    for lag in [1, 3, 6, 12, 24, 48, 72]:
        for var in lag_vars:
            if var in base_features:
                feat_name = f'{var}_lag_{lag}h'
                engineered[feat_name] = base_features[var] + np.random.normal(0, 2, n_samples)
    
    # Delta features (~60 features: 5 deltas * 12 key vars)
    for delta in [1, 3, 6, 12, 24]:
        for var in lag_vars:
            if var in base_features:
                feat_name = f'{var}_delta_{delta}h'
                engineered[feat_name] = np.random.normal(0, 3, n_samples)
    
    # Interaction features (~25 features)
    engineered['temp_x_humidity'] = base_features['temperature_2m'] * base_features['relative_humidity_2m'] / 100
    engineered['precip_x_wind'] = base_features['precipitation'] * base_features['wind_speed_10m']
    engineered['temp_per_humidity'] = base_features['temperature_2m'] / (base_features['relative_humidity_2m'] + 1)
    engineered['soil_moisture_x_soil_temp'] = base_features['soil_moisture_0_1cm'] * base_features['soil_temperature_0cm']
    engineered['wind_x_humidity'] = base_features['wind_speed_10m'] * base_features['relative_humidity_2m']
    engineered['pressure_x_wind'] = base_features['pressure_msl'] * base_features['wind_speed_10m']
    engineered['temp_humidity_ratio'] = base_features['temperature_2m'] / (base_features['relative_humidity_2m'] + 1)
    engineered['precip_x_humidity'] = base_features['precipitation'] * base_features['relative_humidity_2m']
    engineered['cloud_x_humidity'] = base_features['cloud_cover'] * base_features['relative_humidity_2m']
    engineered['temp_x_cloud'] = base_features['temperature_2m'] * base_features['cloud_cover']
    engineered['vertical_temp_gradient'] = base_features['temperature_2m'] - base_features['temperature_80m']
    engineered['soil_temp_gradient'] = base_features['soil_temperature_0cm'] - base_features['soil_temperature_18cm']
    engineered['wind_gradient'] = base_features['wind_speed_10m'] - base_features['wind_speed_80m']
    
    # Disease-specific features (~100 features)
    # Leaf wetness indicators
    engineered['leaf_wetness_hours'] = np.where(
        base_features['relative_humidity_2m'] > 85, 
        np.random.uniform(4, 24, n_samples), 
        np.random.uniform(0, 4, n_samples)
    )
    engineered['leaf_wetness_precip'] = np.where(
        base_features['precipitation'] > 0.1,
        1, 0
    )
    engineered['leaf_wetness_combined'] = engineered['leaf_wetness_hours'] * (engineered['leaf_wetness_precip'] + 0.5)
    
    # VPD calculations (4 features)
    temp_kelvin = base_features['temperature_2m'] + 273.15
    svp = 0.6108 * np.exp((17.27 * base_features['temperature_2m']) / (base_features['temperature_2m'] + 237.3))
    avp = svp * (base_features['relative_humidity_2m'] / 100.0)
    engineered['vpd_calculated'] = svp - avp
    engineered['vpd_kpa'] = engineered['vpd_calculated']
    engineered['vpd_category_low'] = np.where(engineered['vpd_calculated'] < 0.4, 1, 0)
    engineered['vpd_category_high'] = np.where(engineered['vpd_calculated'] > 1.2, 1, 0)
    
    # Temperature ranges (8 features)
    engineered['temp_cold'] = np.where((base_features['temperature_2m'] >= 5) & (base_features['temperature_2m'] < 15), 1, 0)
    engineered['temp_cool'] = np.where((base_features['temperature_2m'] >= 15) & (base_features['temperature_2m'] < 20), 1, 0)
    engineered['temp_warm'] = np.where((base_features['temperature_2m'] >= 20) & (base_features['temperature_2m'] < 25), 1, 0)
    engineered['temp_hot'] = np.where((base_features['temperature_2m'] >= 25) & (base_features['temperature_2m'] < 30), 1, 0)
    engineered['temp_very_hot'] = np.where(base_features['temperature_2m'] >= 30, 1, 0)
    engineered['temp_range'] = base_features['temperature_2m'].max() - base_features['temperature_2m'].min()
    engineered['temp_freezing'] = np.where(base_features['temperature_2m'] <= 0, 1, 0)
    engineered['temp_near_freezing'] = np.where((base_features['temperature_2m'] > 0) & (base_features['temperature_2m'] <= 5), 1, 0)
    
    # Humidity categories (4 features)
    engineered['humidity_very_high'] = np.where(base_features['relative_humidity_2m'] > 90, 1, 0)
    engineered['humidity_high'] = np.where((base_features['relative_humidity_2m'] >= 80) & (base_features['relative_humidity_2m'] <= 90), 1, 0)
    engineered['humidity_moderate'] = np.where((base_features['relative_humidity_2m'] >= 60) & (base_features['relative_humidity_2m'] < 80), 1, 0)
    engineered['humidity_low'] = np.where(base_features['relative_humidity_2m'] < 60, 1, 0)
    
    # Precipitation patterns (8 features)
    engineered['precip_light'] = np.where((base_features['precipitation'] > 0) & (base_features['precipitation'] <= 2), 1, 0)
    engineered['precip_moderate'] = np.where((base_features['precipitation'] > 2) & (base_features['precipitation'] <= 10), 1, 0)
    engineered['precip_heavy'] = np.where(base_features['precipitation'] > 10, 1, 0)
    engineered['precip_cumulative_24h'] = base_features['precipitation'] * np.random.uniform(1, 3, n_samples)
    engineered['precip_cumulative_48h'] = base_features['precipitation'] * np.random.uniform(2, 5, n_samples)
    engineered['precip_cumulative_72h'] = base_features['precipitation'] * np.random.uniform(3, 7, n_samples)
    engineered['wet_hours_24h'] = np.random.uniform(0, 24, n_samples)
    engineered['drying_conditions'] = np.where((base_features['wind_speed_10m'] > 15) & (base_features['relative_humidity_2m'] < 60), 1, 0)
    
    # Wind categories (5 features)
    engineered['wind_calm'] = np.where(base_features['wind_speed_10m'] < 5, 1, 0)
    engineered['wind_light'] = np.where((base_features['wind_speed_10m'] >= 5) & (base_features['wind_speed_10m'] < 15), 1, 0)
    engineered['wind_moderate'] = np.where((base_features['wind_speed_10m'] >= 15) & (base_features['wind_speed_10m'] < 25), 1, 0)
    engineered['wind_strong'] = np.where(base_features['wind_speed_10m'] >= 25, 1, 0)
    engineered['wind_driven_rain'] = engineered['wind_moderate'] * (base_features['precipitation'] > 0.5)
    
    # Cloud and radiation categories (4 features)
    engineered['overcast'] = np.where(base_features['cloud_cover'] > 80, 1, 0)
    engineered['partly_cloudy'] = np.where((base_features['cloud_cover'] >= 40) & (base_features['cloud_cover'] <= 80), 1, 0)
    engineered['clear'] = np.where(base_features['cloud_cover'] < 40, 1, 0)
    engineered['overcast_humid'] = engineered['overcast'] * engineered['humidity_very_high']
    
    # Soil conditions (5 features)
    engineered['soil_very_wet'] = np.where(base_features['soil_moisture_0_1cm'] > 0.4, 1, 0)
    engineered['soil_moist'] = np.where((base_features['soil_moisture_0_1cm'] > 0.25) & (base_features['soil_moisture_0_1cm'] <= 0.4), 1, 0)
    engineered['soil_dry'] = np.where(base_features['soil_moisture_0_1cm'] <= 0.25, 1, 0)
    engineered['soil_warm_wet'] = (base_features['soil_temperature_0cm'] > 20) * (base_features['soil_moisture_0_1cm'] > 0.3)
    engineered['soil_cool_wet'] = (base_features['soil_temperature_0cm'] < 15) * (base_features['soil_moisture_0_1cm'] > 0.3)
    
    # Pressure trends (3 features)
    engineered['pressure_falling'] = np.where(base_features['pressure_msl'] < 1000, 1, 0)
    engineered['pressure_rising'] = np.where(base_features['pressure_msl'] > 1015, 1, 0)
    engineered['pressure_stable'] = np.where((base_features['pressure_msl'] >= 1000) & (base_features['pressure_msl'] <= 1015), 1, 0)
    
    # Dew point depression (2 features)
    engineered['dew_point_depression'] = base_features['temperature_2m'] - base_features['dew_point_2m']
    engineered['near_saturation'] = np.where(engineered['dew_point_depression'] < 2, 1, 0)
    
    # Disease-specific risk indices (4 features)
    # Late blight conditions (cool + wet + humid)
    engineered['late_blight_risk'] = (
        (base_features['temperature_2m'] > 10) & (base_features['temperature_2m'] < 25) &
        (base_features['relative_humidity_2m'] > 85) &
        (base_features['precipitation'] > 0.1)
    ).astype(float) * np.random.uniform(0.5, 1.0, n_samples)
    
    # Powdery mildew conditions (warm + dry + moderate humidity)
    engineered['powdery_mildew_risk'] = (
        (base_features['temperature_2m'] > 15) & (base_features['temperature_2m'] < 30) &
        (base_features['relative_humidity_2m'] > 40) & (base_features['relative_humidity_2m'] < 70) &
        (base_features['precipitation'] < 0.1)
    ).astype(float) * np.random.uniform(0.5, 1.0, n_samples)
    
    # Rust conditions (moderate temp + high humidity)
    engineered['rust_risk'] = (
        (base_features['temperature_2m'] > 15) & (base_features['temperature_2m'] < 25) &
        (base_features['relative_humidity_2m'] > 80)
    ).astype(float) * np.random.uniform(0.5, 1.0, n_samples)
    
    # Botrytis conditions (cool + wet + poor air circulation)
    engineered['botrytis_risk'] = (
        (base_features['temperature_2m'] > 10) & (base_features['temperature_2m'] < 20) &
        (base_features['relative_humidity_2m'] > 85) &
        (base_features['wind_speed_10m'] < 5)
    ).astype(float) * np.random.uniform(0.5, 1.0, n_samples)
    
    # ET categories (3 features)
    engineered['et_low'] = np.where(base_features['evapotranspiration'] < 2, 1, 0)
    engineered['et_moderate'] = np.where((base_features['evapotranspiration'] >= 2) & (base_features['evapotranspiration'] < 5), 1, 0)
    engineered['et_high'] = np.where(base_features['evapotranspiration'] >= 5, 1, 0)
    
    # Additional atmospheric features (5 features)
    engineered['high_cape'] = np.where(base_features['cape'] > 1000, 1, 0)
    engineered['unstable_atmosphere'] = np.where(base_features['lifted_index'] < 0, 1, 0)
    engineered['low_visibility'] = np.where(base_features['visibility'] < 5000, 1, 0)
    engineered['low_sunshine'] = np.where(base_features['sunshine_duration'] < 1800, 1, 0)
    engineered['freezing_level_low'] = np.where(base_features['freezing_level_height'] < 1000, 1, 0)
    
    # Combine all features
    all_features = {**base_features, **engineered}
    features_df = pd.DataFrame(all_features)
    labels = outbreak_df['outbreak'].values
    dates = outbreak_df['date'].values
    
    print(f"Created {features_df.shape[1]} synthetic features")
    
    return features_df, labels, dates


def train_random_forest(X_train, y_train, X_test, y_test):
    """
    Train Random Forest classifier.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Trained model
    """
    print("\nTraining Random Forest...")
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred_proba = model.predict_proba(X_train)[:, 1]
    test_pred_proba = model.predict_proba(X_test)[:, 1]
    
    train_auc = roc_auc_score(y_train, train_pred_proba)
    test_auc = roc_auc_score(y_test, test_pred_proba)
    
    print(f"  Train ROC-AUC: {train_auc:.4f}")
    print(f"  Test ROC-AUC: {test_auc:.4f}")
    
    return model


def train_xgboost(X_train, y_train, X_test, y_test):
    """
    Train XGBoost classifier.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Trained model
    """
    if not XGBOOST_AVAILABLE:
        print("XGBoost not available, skipping...")
        return None
    
    print("\nTraining XGBoost...")
    
    # Calculate scale_pos_weight for imbalanced classes
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': scale_pos_weight,
        'random_state': config.RANDOM_STATE
    }
    
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=100,
        evals=[(dtrain, 'train'), (dtest, 'test')],
        early_stopping_rounds=10,
        verbose_eval=False
    )
    
    # Evaluate
    train_pred_proba = model.predict(dtrain)
    test_pred_proba = model.predict(dtest)
    
    train_auc = roc_auc_score(y_train, train_pred_proba)
    test_auc = roc_auc_score(y_test, test_pred_proba)
    
    print(f"  Train ROC-AUC: {train_auc:.4f}")
    print(f"  Test ROC-AUC: {test_auc:.4f}")
    
    return model


def save_models(rf_model, xgb_model, preprocessor, feature_names):
    """
    Save trained models to disk.
    
    Args:
        rf_model: Trained Random Forest model
        xgb_model: Trained XGBoost model
        preprocessor: Fitted preprocessor
        feature_names: List of feature names
    """
    print("\nSaving models...")
    
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    
    # Save Random Forest
    if rf_model is not None:
        joblib.dump(rf_model, config.RF_MODEL_PATH)
        print(f"  Random Forest saved to {config.RF_MODEL_PATH}")
    
    # Save XGBoost
    if xgb_model is not None:
        xgb_model.save_model(config.XGB_MODEL_PATH)
        print(f"  XGBoost saved to {config.XGB_MODEL_PATH}")
    
    # Save preprocessor
    joblib.dump(preprocessor, config.PREPROCESSOR_PATH)
    print(f"  Preprocessor saved to {config.PREPROCESSOR_PATH}")
    
    # Save ensemble config
    ensemble_config = {
        'model_weights': {
            'rf': 0.6,
            'xgb': 0.4
        },
        'feature_names': feature_names,
        'thresholds': config.RISK_THRESHOLDS,
        'training_date': datetime.now().isoformat()
    }
    
    with open(config.ENSEMBLE_CONFIG_PATH, 'w') as f:
        json.dump(ensemble_config, f, indent=2)
    
    print(f"  Ensemble config saved to {config.ENSEMBLE_CONFIG_PATH}")


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description="Train outbreak prediction models")
    parser.add_argument('--data', type=str, default=config.OUTBREAKS_CSV,
                       help='Path to outbreak data CSV')
    
    args = parser.parse_args()
    
    # Load data
    outbreak_df = load_and_prepare_data(args.data)
    
    # Create features
    features_df, labels, dates = create_training_data(outbreak_df)
    
    # Split data (time-based split)
    split_idx = int(len(features_df) * (1 - config.VALIDATION_SPLIT))
    
    X_train = features_df.iloc[:split_idx]
    X_test = features_df.iloc[split_idx:]
    y_train = labels[:split_idx]
    y_test = labels[split_idx:]
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Preprocess features
    print("\nPreprocessing features...")
    preprocessor = StandardScaler()
    X_train_scaled = preprocessor.fit_transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)
    
    # Train models
    rf_model = train_random_forest(X_train_scaled, y_train, X_test_scaled, y_test)
    xgb_model = train_xgboost(X_train_scaled, y_train, X_test_scaled, y_test)
    
    # Save models
    feature_names = list(features_df.columns)
    save_models(rf_model, xgb_model, preprocessor, feature_names)
    
    print("\nTraining complete!")


if __name__ == '__main__':
    main()
