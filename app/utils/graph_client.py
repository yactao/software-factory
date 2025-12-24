import requests
from typing import Dict, Any, List

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

# TEST_USER_EMAIL = "aziz@itsynchronic.com"

def fetch_all_emails(
    graph_token: str,
    max_emails: int = 500,
) -> List[Dict[str, Any]]:

    headers = {
        "Authorization": f"Bearer {graph_token}"
    }

    url = f"{GRAPH_BASE_URL}/me/messages?$top=50"
    emails: List[Dict[str, Any]] = []

    while url and len(emails) < max_emails:
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            raise RuntimeError(f"Graph error {r.status_code}: {r.text}")

        data = r.json()
        emails.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return emails[:max_emails]


def get_message_attachments(
    graph_token: str,
    message_id: str,
) -> Dict[str, Any]:

    headers = {
        "Authorization": f"Bearer {graph_token}"
    }

    url = f"{GRAPH_BASE_URL}/me/messages/{message_id}/attachments"
    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")

    return r.json()


def download_message_attachment(
    graph_token: str,
    message_id: str,
    attachment_id: str,
) -> tuple[bytes, str]:

    headers = {
        "Authorization": f"Bearer {graph_token}"
    }

    url = (
        f"{GRAPH_BASE_URL}/me/messages/"
        f"{message_id}/attachments/{attachment_id}/$value"
    )

    r = requests.get(url, headers=headers, stream=True, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")

    content_type = r.headers.get(
        "Content-Type", "application/octet-stream"
    )

    return r.content, content_type
