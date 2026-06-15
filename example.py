"""
Quick-start example — run this to verify your Follow Up Boss connection.

1. Copy .env.example to .env
2. Paste your API key into .env
3. Run:  python example.py
"""

from dotenv import load_dotenv
load_dotenv()

from followupboss import FollowUpBossClient

client = FollowUpBossClient()

# ── Who am I? ───────────────────────────────────────────────────────────────
identity = client.whoami()
print(f"Connected as: {identity.get('account', {}).get('name', 'unknown account')}\n")

# ── List first 5 contacts ────────────────────────────────────────────────────
people = client.get_people(limit=5)
print(f"First {len(people)} contacts:")
for p in people:
    name = f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
    print(f"  [{p['id']}] {name}")

# ── Create a contact ─────────────────────────────────────────────────────────
# new_person = client.create_person(
#     first_name="Jane",
#     last_name="Doe",
#     emails=["jane@example.com"],
#     phones=["555-123-4567"],
# )
# print(f"\nCreated contact: {new_person['id']}")

# ── Add a note ───────────────────────────────────────────────────────────────
# note = client.create_note(person_id=new_person["id"], body="Called and left voicemail.")
# print(f"Note added: {note['id']}")

# ── Create a follow-up task ──────────────────────────────────────────────────
# task = client.create_task(
#     name="Follow up call",
#     person_id=new_person["id"],
#     due_date="2026-06-20T10:00:00Z",
# )
# print(f"Task created: {task['id']}")

print("\nAll done!")
