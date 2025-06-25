#!/bin/bash
echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt
echo "Dependencies installation completed!"
