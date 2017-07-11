#!/bin/bash
echo "Installing required Python packages..."
sudo pip install -r requirements.txt
echo "Requirements met..."
python ./app.py
