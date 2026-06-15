# Follow Up Boss CRM Connector

A Python client for the [Follow Up Boss API](https://docs.followupboss.com/reference).

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your API key
In Follow Up Boss: **Admin → API → API Key**

### 3. Configure
```bash
cp .env.example .env
# Edit .env and paste your API key
```

### 4. Test the connection
```bash
python example.py
```

---

## Usage

```python
from dotenv import load_dotenv
load_dotenv()

from followupboss import FollowUpBossClient

client = FollowUpBossClient()  # reads FUB_API_KEY from .env

# or pass the key directly:
# client = FollowUpBossClient(api_key="YOUR_KEY_HERE")
```

### Contacts (People)

```python
# List all contacts
people = client.get_people()

# Search contacts
results = client.search_people("John Smith")

# Get one contact
person = client.get_person(12345)

# Create a contact
person = client.create_person(
    first_name="Jane",
    last_name="Doe",
    emails=["jane@example.com"],
    phones=["555-123-4567"],
)

# Update a contact
client.update_person(person["id"], stage="Hot")

# Tag a contact
client.tag_person(person["id"], ["VIP", "Buyer"])

# Delete
client.delete_person(person["id"])
```

### Deals

```python
deals = client.get_deals()
deal = client.create_deal(name="123 Main St", person_id=person["id"], price=500000)
client.update_deal(deal["id"], stage="Under Contract")
```

### Tasks

```python
task = client.create_task(
    name="Follow-up call",
    person_id=person["id"],
    due_date="2026-06-20T10:00:00Z",
)
client.update_task(task["id"], isComplete=True)
```

### Notes

```python
note = client.create_note(person_id=person["id"], body="Left voicemail.")
notes = client.get_notes(person_id=person["id"])
```

### Webhooks

```python
# Register a webhook to receive real-time events
webhook = client.create_webhook(
    url="https://your-server.com/webhook",
    events=["personCreated", "personUpdated", "dealCreated"],
)

# List webhooks
client.get_webhooks()

# Remove webhook
client.delete_webhook(webhook["id"])
```

---

## Available Methods

| Resource | Methods |
|---|---|
| People | `get_people`, `get_person`, `create_person`, `update_person`, `delete_person`, `search_people`, `tag_person` |
| Deals | `get_deals`, `get_deal`, `create_deal`, `update_deal`, `delete_deal` |
| Tasks | `get_tasks`, `get_task`, `create_task`, `update_task`, `delete_task` |
| Notes | `get_notes`, `create_note` |
| Events | `get_events`, `create_event` |
| Appointments | `get_appointments`, `create_appointment` |
| Users | `get_users`, `get_user` |
| Pipelines | `get_pipelines`, `get_stages` |
| Tags | `get_tags` |
| Webhooks | `get_webhooks`, `create_webhook`, `delete_webhook` |
| Auth | `whoami` |
