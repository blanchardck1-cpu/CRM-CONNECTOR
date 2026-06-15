"""
Run this ONCE to register your webhook URL with Follow Up Boss.
Usage:  python register_webhook.py https://your-ngrok-url.ngrok.io
"""

import sys
from dotenv import load_dotenv
load_dotenv()

from followupboss import FollowUpBossClient

if len(sys.argv) < 2:
    print("Usage: python register_webhook.py https://your-ngrok-url.ngrok.io")
    sys.exit(1)

base_url = sys.argv[1].rstrip("/")
webhook_url = f"{base_url}/webhook"

client = FollowUpBossClient()

# Remove any old webhooks pointing to the same path to avoid duplicates
existing = client.get_webhooks()
for wh in existing:
    if "/webhook" in wh.get("url", ""):
        client.delete_webhook(wh["id"])
        print(f"Removed old webhook: {wh['url']}")

webhook = client.create_webhook(
    url=webhook_url,
    events=["personTagged", "personCreated", "personUpdated"],
)

print(f"\nWebhook registered!")
print(f"  URL:    {webhook_url}")
print(f"  ID:     {webhook['id']}")
print(f"  Events: personTagged, personCreated, personUpdated")
print(f"\nFollow Up Boss will now notify you in real time when a b lead is tagged.")
