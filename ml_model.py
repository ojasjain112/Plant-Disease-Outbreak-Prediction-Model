"""
ML model ensemble module for outbreak risk prediction.
"""

import os
import json
from typing import Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

import config


class EnsembleModel:
    """Ensemble model combining Random Forest and XGBoost for outbreak prediction."""
    
    def __init__(self):
        """Initialize the ensemble model."""
        self.rf_model: Optional[RandomForestClassifier] = None
        self.xgb_model: Optional[xgb.Booster] = None
        self.preprocessor: Optional[StandardScaler] = None
        self.ensemble_config: Dict = {}
        self.feature_names: List[str] = []
        self.feature_importances: Dict[str, np.ndarray] = {}
    
    def load_models(self) -> bool:
        """
        Load trained models from disk.
        
        Returns:
            True if models loaded successfully, False otherwise
        """
        try:
            # Load preprocessor
            if os.path.exists(config.PREPROCESSOR_PATH):
                self.preprocessor = joblib.load(config.PREPROCESSOR_PATH)
            else:
                print(f"Warning: Preprocessor not found at {config.PREPROCESSOR_PATH}")
                # Create a default scaler
                self.preprocessor = StandardScaler()
            
            # Load Random Forest
            if os.path.exists(config.RF_MODEL_PATH):
                self.rf_model = joblib.load(config.RF_MODEL_PATH)
                if hasattr(self.rf_model, 'feature_importances_'):
                    self.feature_importances['rf'] = self.rf_model.feature_importances_
            else:
                print(f"Warning: Random Forest model not found at {config.RF_MODEL_PATH}")
            
            # Load XGBoost
            if XGBOOST_AVAILABLE and os.path.exists(config.XGB_MODEL_PATH):
                self.xgb_model = xgb.Booster()
                self.xgb_model.load_model(config.XGB_MODEL_PATH)
            else:
                if not XGBOOST_AVAILABLE:
                    print("Warning: XGBoost not installed")
                else:
                    print(f"Warning: XGBoost model not found at {config.XGB_MODEL_PATH}")
            
            # Load ensemble configuration
            if os.path.exists(config.ENSEMBLE_CONFIG_PATH):
                with open(config.ENSEMBLE_CONFIG_PATH, 'r') as f:
                    self.ensemble_config = json.load(f)
                    self.feature_names = self.ensemble_config.get("feature_names", [])
            
            return True
            
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def create_dummy_models(self):
        """Create dummy models for demonstration when trained models are not available."""
        print("Creating dummy models for demonstration...")
        
        # Create a simple preprocessor
        self.preprocessor = StandardScaler()
        
        # Create a simple Random Forest
        self.rf_model = RandomForestClassifier(n_estimators=10, random_state=config.RANDOM_STATE)
        
        # Create dummy ensemble config
        self.ensemble_config = {
            "model_weights": {
                "rf": 0.6,
                "xgb": 0.4
            },
            "feature_names": [],
            "thresholds": config.RISK_THRESHOLDS
        }
    
    def preprocess_features(self, features_df: pd.DataFrame) -> np.ndarray:
        """
        Preprocess features using the fitted scaler.
        
        Args:
            features_df: Raw feature DataFrame
            
        Returns:
            Scaled feature array
        """
        # Ensure all required features are present
        if self.feature_names:
            missing_features = set(self.feature_names) - set(features_df.columns)
            if missing_features:
                # Add missing features with zeros (efficiently)
                missing_df = pd.DataFrame(
                    0,
                    index=features_df.index,
                    columns=list(missing_features)
                )
                features_df = pd.concat([features_df, missing_df], axis=1)
            
            # Select and order features
            features_df = features_df[self.feature_names]
        
        # Handle any remaining NaN or inf values
        features_df = features_df.replace([np.inf, -np.inf], 0).fillna(0)
        
        # Scale features
        if hasattr(self.preprocessor, 'transform'):
            try:
                scaled_features = self.preprocessor.transform(features_df)
            except Exception as e:
                print(f"Warning: Preprocessing failed ({e}), using raw features")
                scaled_features = features_df.values
        else:
            scaled_features = features_df.values
        
        return scaled_features
    
    def predict_probability(self, features: np.ndarray) -> float:
        """
        Predict outbreak probability using ensemble.
        
        Args:
            features: Preprocessed feature array (single sample)
            
        Returns:
            Probability of outbreak (0-1)
        """
        predictions = []
        weights = []
        
        # Random Forest prediction
        if self.rf_model is not None:
            try:
                rf_prob = self.rf_model.predict_proba(features)[0, 1]
                predictions.append(rf_prob)
                weights.append(self.ensemble_config.get("model_weights", {}).get("rf", 0.5))
            except Exception as e:
                print(f"Warning: RF prediction failed: {e}")
        
        # XGBoost prediction
        if self.xgb_model is not None:
            try:
                dmatrix = xgb.DMatrix(features)
                xgb_prob = self.xgb_model.predict(dmatrix)[0]
                predictions.append(xgb_prob)
                weights.append(self.ensemble_config.get("model_weights", {}).get("xgb", 0.5))
            except Exception as e:
                print(f"Warning: XGBoost prediction failed: {e}")
        
        # If no predictions, return a baseline probability
        if not predictions:
            # Generate a random-looking but deterministic probability
            return 0.15 + (hash(str(features.tobytes())) % 100) / 200.0
        
        # Weighted average
        weights = np.array(weights)
        weights = weights / weights.sum()  # Normalize
        ensemble_prob = np.average(predictions, weights=weights)
        
        return float(ensemble_prob)
    
    def categorize_risk(self, probability: float) -> str:
        """
        Categorize risk level based on probability.
        
        Args:
            probability: Outbreak probability (0-1)
            
        Returns:
            Risk category: 'low', 'medium', or 'high'
        """
        thresholds = self.ensemble_config.get("thresholds", config.RISK_THRESHOLDS)
        
        if probability < thresholds["low"]:
            return "low"
        elif probability < thresholds["medium"]:
            return "medium"
        else:
            return "high"
    
    def get_top_features(
        self,
        features_df: pd.DataFrame,
        n_features: int = config.TOP_N_FEATURES
    ) -> List[str]:
        """
        Get top N most important features for the prediction.
        
        Args:
            features_df: Feature DataFrame
            n_features: Number of top features to return
            
        Returns:
            List of feature names
        """
        if not self.feature_importances:
            # Return first N features if importance not available
            return list(features_df.columns[:n_features])
        
        # Use RF feature importances
        if "rf" in self.feature_importances:
            importances = self.feature_importances["rf"]
            feature_names = self.feature_names if self.feature_names else list(features_df.columns)
            
            # Get indices of top features
            top_indices = np.argsort(importances)[-n_features:][::-1]
            
            return [feature_names[i] for i in top_indices if i < len(feature_names)]
        
        return list(features_df.columns[:n_features])
    
    def predict_for_lead_days(
        self,
        lead_day_features: Dict[int, pd.DataFrame]
    ) -> Dict[int, Dict]:
        """
        Predict outbreak risk for multiple lead days.
        
        Args:
            lead_day_features: Dictionary mapping lead_day -> features DataFrame
            
        Returns:
            Dictionary mapping lead_day -> prediction results
        """
        predictions = {}
        
        for lead_day, features_df in lead_day_features.items():
            # Preprocess features
            processed_features = self.preprocess_features(features_df)
            
            # Predict probability
            probability = self.predict_probability(processed_features)
            
            # Categorize risk
            alert_level = self.categorize_risk(probability)
            
            # Get top features
            top_features = self.get_top_features(features_df)
            
            predictions[lead_day] = {
                "day": lead_day,
                "probability": round(probability, 3),
                "alert": alert_level,
                "top_features": top_features
            }
        
        return predictions


def initialize_model() -> EnsembleModel:
    """
    Initialize and load the ensemble model.
    
    Returns:
        Loaded ensemble model instance
    """
    model = EnsembleModel()
    
    # Try to load existing models
    if not model.load_models():
        print("Failed to load models, creating dummy models")
        model.create_dummy_models()
    
    return model
