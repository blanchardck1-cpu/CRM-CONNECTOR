#!/bin/bash
echo "Setting up Follow Up Boss B-Leads Auto-Texter..."

# Create .env with API key
echo "FUB_API_KEY=fka_0oLnKwXpmGYRziW3j8fZBEYCb13rimVcHQ" > .env
echo "FUB_SYSTEM_NAME=BLeadsAutoTexter" >> .env
echo "✓ API key configured"

# Install dependencies
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

echo ""
echo "Setup complete! Next steps:"
echo ""
echo "  1. Start the server:   python server.py"
echo "  2. In a second window: ngrok http 5000"
echo "  3. Copy the ngrok URL and run: python register_webhook.py https://xxxx.ngrok.io"
echo ""
echo "After that, every new b lead will get an auto-text 10 minutes after being tagged!"
