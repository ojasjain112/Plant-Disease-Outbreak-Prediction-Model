"""
Data ingestion script to fetch historical outbreak and weather data.
"""

import os
import argparse
from datetime import datetime, timedelta
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from weather_api import WeatherAPI


def generate_sample_outbreak_data(output_path: str, num_samples: int = 1000):
    """
    Generate sample outbreak data for demonstration.
    In production, this would fetch real outbreak data from a database or API.
    
    Args:
        output_path: Path to save the CSV file
        num_samples: Number of sample records to generate
    """
    import numpy as np
    
    print(f"Generating {num_samples} sample outbreak records...")
    
    # Generate random dates over past 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    date_range = pd.date_range(start=start_date, end=end_date, periods=num_samples)
    
    # Generate random locations (example: India and surrounding regions)
    latitudes = np.random.uniform(8.0, 35.0, num_samples)
    longitudes = np.random.uniform(68.0, 97.0, num_samples)
    
    # Generate outbreak labels (with some correlation to season)
    # More outbreaks in monsoon season (June-September)
    months = date_range.month
    base_prob = 0.15
    outbreak_prob = np.where((months >= 6) & (months <= 9), base_prob + 0.15, base_prob)
    outbreaks = np.random.random(num_samples) < outbreak_prob
    
    # Disease types - uniform distribution across all disease types
    diseases = np.random.choice(config.DISEASE_TYPES, num_samples)
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': date_range.date,
        'lat': latitudes,
        'lon': longitudes,
        'location_id': [f"LOC_{i:04d}" for i in range(num_samples)],
        'outbreak': outbreaks.astype(int),
        'disease': diseases
    })
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Sample outbreak data saved to {output_path}")
    print(f"Total outbreaks: {df['outbreak'].sum()} ({df['outbreak'].mean()*100:.1f}%)")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    return df


def fetch_weather_for_outbreaks(outbreak_df: pd.DataFrame, output_dir: str):
    """
    Fetch historical weather data for outbreak locations.
    
    Args:
        outbreak_df: DataFrame with outbreak records
        output_dir: Directory to save weather data
    """
    weather_api = WeatherAPI()
    
    print("Fetching weather data for outbreak locations...")
    print("Note: This may take a while for large datasets")
    
    # Group by unique location and date range
    unique_locations = outbreak_df[['lat', 'lon']].drop_duplicates()
    
    print(f"Found {len(unique_locations)} unique locations")
    
    # For demonstration, limit to first 10 locations
    sample_locations = unique_locations.head(10)
    
    weather_data = []
    
    for idx, (_, row) in enumerate(sample_locations.iterrows(), 1):
        lat, lon = row['lat'], row['lon']
        
        print(f"Fetching weather for location {idx}/{len(sample_locations)}: "
              f"({lat:.4f}, {lon:.4f})")
        
        try:
            # Fetch historical weather (last 90 days as example)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            weather = weather_api.fetch_historical(
                lat, lon,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            weather_df = weather_api.parse_to_dataframe(weather)
            weather_df['lat'] = lat
            weather_df['lon'] = lon
            
            weather_data.append(weather_df)
            
        except Exception as e:
            print(f"  Warning: Failed to fetch weather for location ({lat}, {lon}): {e}")
            continue
    
    if weather_data:
        # Combine all weather data
        combined_weather = pd.concat(weather_data, ignore_index=False)
        
        # Save to CSV
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "historical_weather.csv")
        combined_weather.to_csv(output_path)
        
        print(f"Weather data saved to {output_path}")
        print(f"Total weather records: {len(combined_weather)}")
    else:
        print("No weather data fetched successfully")


def main():
    """Main data ingestion pipeline."""
    parser = argparse.ArgumentParser(description="Ingest outbreak and weather data")
    parser.add_argument('--samples', type=int, default=1000,
                       help='Number of sample outbreak records to generate')
    parser.add_argument('--fetch-weather', action='store_true',
                       help='Fetch weather data for outbreak locations')
    
    args = parser.parse_args()
    
    # Generate outbreak data
    outbreak_df = generate_sample_outbreak_data(config.OUTBREAKS_CSV, args.samples)
    
    # Optionally fetch weather data
    if args.fetch_weather:
        fetch_weather_for_outbreaks(outbreak_df, config.DATA_DIR)
    else:
        print("\nSkipping weather data fetch. Use --fetch-weather to enable.")
    
    print("\nData ingestion complete!")


if __name__ == '__main__':
    main()
