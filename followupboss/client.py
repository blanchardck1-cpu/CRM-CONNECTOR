import base64
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests


class FollowUpBossError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class FollowUpBossClient:
    """Client for the Follow Up Boss REST API.

    Docs: https://docs.followupboss.com/reference
    Authentication: HTTP Basic Auth — API key as username, empty password.
    """

    BASE_URL = "https://api.followupboss.com/v1"

    def __init__(self, api_key: Optional[str] = None, system_name: Optional[str] = None):
        api_key = api_key or os.environ.get("FUB_API_KEY")
        if not api_key:
            raise ValueError(
                "API key required. Pass api_key= or set FUB_API_KEY environment variable."
            )
        token = base64.b64encode(f"{api_key}:".encode()).decode()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-System": system_name or os.environ.get("FUB_SYSTEM_NAME", "CRMConnector"),
                "X-System-Key": api_key,
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.BASE_URL}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        resp = self._session.request(method, self._url(path), **kwargs)
        if not resp.ok:
            try:
                detail = resp.json().get("errorMessage", resp.text)
            except Exception:
                detail = resp.text
            raise FollowUpBossError(resp.status_code, detail)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, data: Dict) -> Any:
        return self._request("POST", path, json=data)

    def _put(self, path: str, data: Dict) -> Any:
        return self._request("PUT", path, json=data)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def _paginate(self, path: str, key: str, params: Optional[Dict] = None) -> List[Dict]:
        params = dict(params or {})
        params.setdefault("limit", 100)
        params.setdefault("offset", 0)
        results = []
        while True:
            data = self._get(path, params=params)
            page = data.get(key, [])
            results.extend(page)
            if len(page) < params["limit"]:
                break
            params["offset"] += params["limit"]
        return results

    # ------------------------------------------------------------------
    # People (Contacts)
    # ------------------------------------------------------------------

    def get_people(self, **filters) -> List[Dict]:
        """Return all people/contacts, with optional filters.

        Common filters: search, stage, assignedTo, tag, limit, sort
        """
        return self._paginate("people", "people", params=filters)

    def get_person(self, person_id: int) -> Dict:
        return self._get(f"people/{person_id}")

    def create_person(
        self,
        first_name: str,
        last_name: str = "",
        emails: Optional[List[str]] = None,
        phones: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict:
        """Create a contact. Extra keyword args are passed directly to the API."""
        payload: Dict[str, Any] = {"firstName": first_name, "lastName": last_name, **kwargs}
        if emails:
            payload["emails"] = [{"value": e} for e in emails]
        if phones:
            payload["phones"] = [{"value": p} for p in phones]
        return self._post("people", payload)

    def update_person(self, person_id: int, **fields) -> Dict:
        return self._put(f"people/{person_id}", fields)

    def delete_person(self, person_id: int) -> None:
        self._delete(f"people/{person_id}")

    def search_people(self, query: str) -> List[Dict]:
        return self._paginate("people", "people", params={"search": query})

    # ------------------------------------------------------------------
    # Deals
    # ------------------------------------------------------------------

    def get_deals(self, **filters) -> List[Dict]:
        return self._paginate("deals", "deals", params=filters)

    def get_deal(self, deal_id: int) -> Dict:
        return self._get(f"deals/{deal_id}")

    def create_deal(self, name: str, person_id: int, **kwargs) -> Dict:
        return self._post("deals", {"name": name, "personId": person_id, **kwargs})

    def update_deal(self, deal_id: int, **fields) -> Dict:
        return self._put(f"deals/{deal_id}", fields)

    def delete_deal(self, deal_id: int) -> None:
        self._delete(f"deals/{deal_id}")

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def get_tasks(self, **filters) -> List[Dict]:
        return self._paginate("tasks", "tasks", params=filters)

    def get_task(self, task_id: int) -> Dict:
        return self._get(f"tasks/{task_id}")

    def create_task(self, name: str, person_id: int, due_date: Optional[str] = None, **kwargs) -> Dict:
        """due_date: ISO 8601 string, e.g. '2026-06-20T10:00:00Z'"""
        payload: Dict[str, Any] = {"name": name, "personId": person_id, **kwargs}
        if due_date:
            payload["dueDate"] = due_date
        return self._post("tasks", payload)

    def update_task(self, task_id: int, **fields) -> Dict:
        return self._put(f"tasks/{task_id}", fields)

    def delete_task(self, task_id: int) -> None:
        self._delete(f"tasks/{task_id}")

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    def get_notes(self, person_id: Optional[int] = None, **filters) -> List[Dict]:
        if person_id:
            filters["personId"] = person_id
        return self._paginate("notes", "notes", params=filters)

    def create_note(self, person_id: int, body: str, **kwargs) -> Dict:
        return self._post("notes", {"personId": person_id, "body": body, **kwargs})

    # ------------------------------------------------------------------
    # Events (Activity / Timeline)
    # ------------------------------------------------------------------

    def get_events(self, **filters) -> List[Dict]:
        return self._paginate("events", "events", params=filters)

    def create_event(self, person_id: int, type: str, **kwargs) -> Dict:
        """Log an event for a contact. type examples: 'Note', 'Call', 'Email'"""
        return self._post("events", {"personId": person_id, "type": type, **kwargs})

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------

    def get_appointments(self, **filters) -> List[Dict]:
        return self._paginate("appointments", "appointments", params=filters)

    def create_appointment(self, person_id: int, start: str, end: str, title: str, **kwargs) -> Dict:
        """start/end: ISO 8601 strings"""
        return self._post(
            "appointments",
            {"personId": person_id, "start": start, "end": end, "title": title, **kwargs},
        )

    # ------------------------------------------------------------------
    # Teams / Users
    # ------------------------------------------------------------------

    def get_users(self) -> List[Dict]:
        return self._paginate("users", "users")

    def get_user(self, user_id: int) -> Dict:
        return self._get(f"users/{user_id}")

    # ------------------------------------------------------------------
    # Pipelines / Stages
    # ------------------------------------------------------------------

    def get_pipelines(self) -> List[Dict]:
        return self._get("pipelines").get("pipelines", [])

    def get_stages(self, pipeline_id: Optional[int] = None) -> List[Dict]:
        params = {"pipelineId": pipeline_id} if pipeline_id else None
        return self._get("stages", params=params).get("stages", [])

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def get_tags(self) -> List[Dict]:
        return self._get("tags").get("tags", [])

    def tag_person(self, person_id: int, tags: List[str]) -> Dict:
        """Add tags to a contact."""
        person = self.get_person(person_id)
        existing = [t["name"] for t in person.get("tags", [])]
        merged = list(set(existing + tags))
        return self.update_person(person_id, tags=[{"name": t} for t in merged])

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def get_webhooks(self) -> List[Dict]:
        return self._get("webhooks").get("webhooks", [])

    def create_webhook(self, url: str, events: List[str]) -> Dict:
        """events examples: ['personCreated', 'personUpdated', 'dealCreated']"""
        return self._post("webhooks", {"url": url, "events": events})

    def delete_webhook(self, webhook_id: int) -> None:
        self._delete(f"webhooks/{webhook_id}")

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def whoami(self) -> Dict:
        """Return info about the authenticated account."""
        return self._get("identity")
