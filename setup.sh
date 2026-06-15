#!/bin/bash
echo "Setting up Follow Up Boss CRM Connector..."

# Create .env with API key
echo "FUB_API_KEY=fka_0oLnKwXpmGYRziW3j8fZBEYCb13rimVcHQ" > .env
echo "FUB_SYSTEM_NAME=CRMConnector" >> .env
echo "✓ API key configured"

# Install dependencies
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Test connection
echo ""
echo "Testing connection to Follow Up Boss..."
python example.py
