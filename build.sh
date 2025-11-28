#!/bin/bash

echo "Starting build process..."

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p models data cache

# Generate sample training data
echo "Generating training data..."
python scripts/data_ingest.py --samples 1000

# Train ML models
echo "Training models..."
python scripts/train_models.py

echo "Build complete!"
