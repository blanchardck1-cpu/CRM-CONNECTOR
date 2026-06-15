"""
B-Leads Auto-Texter (Polling Mode)
-----------------------------------
Every 5 minutes, checks Follow Up Boss for new contacts tagged "b leads"
that were added in the last 10 minutes. Sends each one a personalized
intro text and logs them so they never get double-texted.

Run with:  python poller.py
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

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

POLL_INTERVAL = 5 * 60        # check every 5 minutes
LOOKBACK_MINUTES = 10         # catch leads added in last 10 min
B_LEAD_TAG = "b leads"
CONTACTED_FILE = Path("contacted.json")  # tracks who already got a text

MESSAGE_TEMPLATE = (
    "Hey {first_name}! I saw you inquired about {property}. "
    "My name is Charles Blanchard with the Rarity Real Estate Team — "
    "I'd love to help you schedule a tour! When works best for you?"
)


def load_contacted() -> set:
    if CONTACTED_FILE.exists():
        return set(json.loads(CONTACTED_FILE.read_text()))
    return set()


def save_contacted(contacted: set):
    CONTACTED_FILE.write_text(json.dumps(list(contacted)))


def get_property_name(client: FollowUpBossClient, person: dict) -> str:
    """Try to find the property the lead inquired about."""
    for field in ("address", "propertyAddress", "property"):
        val = person.get(field)
        if val and isinstance(val, str) and len(val) > 3:
            return val

    # Check recent notes for property mention
    try:
        notes = client.get_notes(person_id=person["id"])
        for note in notes[:5]:
            body = note.get("body", "")
            lower = body.lower()
            for keyword in ("about ", "inquired about ", "interested in "):
                idx = lower.find(keyword)
                if idx != -1:
                    snippet = body[idx + len(keyword):].split(".")[0].strip()
                    if snippet:
                        return snippet
    except Exception:
        pass

    return "the property"


def send_intro_text(client: FollowUpBossClient, person: dict):
    first_name = person.get("firstName") or "there"
    property_name = get_property_name(client, person)

    message = MESSAGE_TEMPLATE.format(
        first_name=first_name,
        property=property_name,
    )

    client.create_event(
        person_id=person["id"],
        type="Text",
        message=message,
        direction="outbound",
    )

    log.info(f"Sent intro text to {first_name} (id={person['id']}) about '{property_name}'")


def has_b_lead_tag(person: dict) -> bool:
    tags = [t.get("name", "").lower() for t in person.get("tags", [])]
    return B_LEAD_TAG.lower() in tags


def check_for_new_bleads(client: FollowUpBossClient, contacted: set) -> set:
    since = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        people = client.get_people(sort="created", direction="desc", limit=50)
    except Exception as e:
        log.error(f"Failed to fetch people: {e}")
        return contacted

    new_contacts = 0
    for person in people:
        created_str = person.get("created", "")
        try:
            created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except Exception:
            continue

        # Only look at recently created contacts
        if created < since:
            break

        person_id = str(person["id"])

        if person_id in contacted:
            continue

        if not has_b_lead_tag(person):
            continue

        try:
            send_intro_text(client, person)
            contacted.add(person_id)
            save_contacted(contacted)
            new_contacts += 1
        except Exception as e:
            log.error(f"Failed to text person {person['id']}: {e}")

    if new_contacts == 0:
        log.info("No new b leads found.")

    return contacted


def main():
    client = FollowUpBossClient()
    contacted = load_contacted()
    log.info("B-Leads Auto-Texter started. Checking every 5 minutes...")
    log.info(f"Already contacted {len(contacted)} people (won't double-text them).")

    while True:
        log.info("Checking for new b leads...")
        contacted = check_for_new_bleads(client, contacted)
        log.info(f"Next check in {POLL_INTERVAL // 60} minutes.")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
