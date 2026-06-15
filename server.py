"""
B-Leads Auto-Texter
-------------------
Listens for Follow Up Boss webhook events. When a contact is tagged "b leads",
waits 10 minutes then sends them a personalized intro text via FUB.

Run with:  python server.py
Expose publicly with ngrok:  ngrok http 5000
Then register the webhook:   python register_webhook.py
"""

import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from followupboss import FollowUpBossClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bleads.log"),
    ],
)
log = logging.getLogger(__name__)

app = Flask(__name__)
client = FollowUpBossClient()

MESSAGE_TEMPLATE = (
    "Hey {first_name}! I saw you inquired about {property}. "
    "I'd love to help you schedule a tour — when works best for you?"
)
DELAY_SECONDS = 10 * 60  # 10 minutes
B_LEAD_TAG = "b leads"


def get_property_name(person: Dict[str, Any]) -> str:
    """Pull property address from FUB person record."""
    # Check common FUB fields for property/address info
    for field in ("address", "propertyAddress", "property", "source"):
        val = person.get(field)
        if val and isinstance(val, str) and len(val) > 3:
            return val

    # Fall back to the intro note on the contact if present
    notes_data = client.get_notes(person_id=person["id"])
    for note in notes_data[:3]:
        body = note.get("body", "")
        # Look for "about <address>" pattern in the intro message
        lower = body.lower()
        for keyword in ("about ", "inquired about ", "interested in "):
            idx = lower.find(keyword)
            if idx != -1:
                snippet = body[idx + len(keyword):].split(".")[0].strip()
                if snippet:
                    return snippet

    return "the property"


def send_intro_text(person_id: int):
    """Called in a background thread after the 10-minute delay."""
    time.sleep(DELAY_SECONDS)
    try:
        person = client.get_person(person_id)

        # Confirm the tag is still there (agent may have removed it)
        tags = [t.get("name", "").lower() for t in person.get("tags", [])]
        if B_LEAD_TAG.lower() not in tags:
            log.info(f"Person {person_id} no longer tagged '{B_LEAD_TAG}', skipping.")
            return

        first_name = person.get("firstName") or "there"
        property_name = get_property_name(person)

        message = MESSAGE_TEMPLATE.format(
            first_name=first_name,
            property=property_name,
        )

        # Send text via FUB (uses the connected texting provider)
        client.create_event(
            person_id=person_id,
            type="Text",
            message=message,
            direction="outbound",
        )

        log.info(f"Sent intro text to {first_name} (id={person_id}) about '{property_name}'")

    except Exception as e:
        log.error(f"Failed to send text to person {person_id}: {e}")


def has_b_lead_tag(payload: Dict[str, Any]) -> bool:
    """Check if the webhook payload contains a b leads tag."""
    # FUB sends tag changes in various event structures
    tags = []

    # personTagged event
    if "tag" in payload:
        tags.append(payload["tag"].get("name", ""))

    # person updated — check tags array
    person = payload.get("person", {})
    for t in person.get("tags", []):
        tags.append(t.get("name", ""))

    return any(t.lower() == B_LEAD_TAG.lower() for t in tags if t)


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    event = payload.get("event", "")

    log.info(f"Webhook received: event={event}")

    # We care about tag events and person-created/updated events
    if event in ("personTagged", "personCreated", "personUpdated"):
        if has_b_lead_tag(payload):
            person_id = (
                payload.get("person", {}).get("id")
                or payload.get("personId")
            )
            if person_id:
                log.info(
                    f"B lead detected (id={person_id}), "
                    f"scheduling text in {DELAY_SECONDS // 60} minutes."
                )
                t = threading.Thread(
                    target=send_intro_text, args=(person_id,), daemon=True
                )
                t.start()

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "time": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    log.info(f"B-Leads Auto-Texter starting on port {port}")
    app.run(host="0.0.0.0", port=port)
