"""
Notion API helper — thin wrapper around the Notion REST API using requests.
Used by the transcript agent for standalone execution without MCP.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers():
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN not set in environment")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


# ── Pages ──────────────────────────────────────────────────────────────

def get_page(page_id: str) -> dict:
    """Retrieve a page by ID."""
    r = requests.get(f"{NOTION_BASE}/pages/{page_id}", headers=_headers())
    r.raise_for_status()
    return r.json()


def update_page(page_id: str, properties: dict) -> dict:
    """Update page properties."""
    r = requests.patch(
        f"{NOTION_BASE}/pages/{page_id}",
        headers=_headers(),
        json={"properties": properties},
    )
    r.raise_for_status()
    return r.json()


def create_page(parent: dict, properties: dict, children: list = None) -> dict:
    """Create a new page."""
    body = {"parent": parent, "properties": properties}
    if children:
        body["children"] = children
    r = requests.post(f"{NOTION_BASE}/pages", headers=_headers(), json=body)
    r.raise_for_status()
    return r.json()


# ── Databases ──────────────────────────────────────────────────────────

def query_database(database_id: str, filter: dict = None, sorts: list = None) -> list:
    """Query a database and return all pages (handles pagination)."""
    body = {}
    if filter:
        body["filter"] = filter
    if sorts:
        body["sorts"] = sorts

    all_results = []
    has_more = True
    start_cursor = None

    while has_more:
        if start_cursor:
            body["start_cursor"] = start_cursor
        r = requests.post(
            f"{NOTION_BASE}/databases/{database_id}/query",
            headers=_headers(),
            json=body,
        )
        r.raise_for_status()
        data = r.json()
        all_results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return all_results


# ── Blocks ─────────────────────────────────────────────────────────────

def get_block_children(block_id: str) -> list:
    """Get all children blocks (handles pagination)."""
    all_blocks = []
    has_more = True
    start_cursor = None

    while has_more:
        url = f"{NOTION_BASE}/blocks/{block_id}/children?page_size=100"
        if start_cursor:
            url += f"&start_cursor={start_cursor}"
        r = requests.get(url, headers=_headers())
        r.raise_for_status()
        data = r.json()
        all_blocks.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return all_blocks


def append_blocks(block_id: str, children: list) -> dict:
    """Append children blocks to a page or block. Batches in groups of 100."""
    results = []
    for i in range(0, len(children), 100):
        batch = children[i:i + 100]
        r = requests.patch(
            f"{NOTION_BASE}/blocks/{block_id}/children",
            headers=_headers(),
            json={"children": batch},
        )
        r.raise_for_status()
        results.append(r.json())
    return results[-1] if results else {}


def delete_block(block_id: str) -> dict:
    """Delete (archive) a block."""
    r = requests.delete(f"{NOTION_BASE}/blocks/{block_id}", headers=_headers())
    r.raise_for_status()
    return r.json()


def get_page_text(block_id: str) -> str:
    """Extract all text content from a page recursively."""
    blocks = get_block_children(block_id)
    return _parse_blocks(blocks)


def _parse_blocks(blocks: list, indent: int = 0) -> str:
    """Parse Notion blocks into plain text, recursively."""
    lines = []
    prefix = "  " * indent

    for block in blocks:
        btype = block.get("type", "")
        bdata = block.get(btype, {})

        # Extract rich_text content
        rich_text = bdata.get("rich_text", [])
        text = "".join(rt.get("plain_text", "") for rt in rich_text)

        if btype.startswith("heading_"):
            level = btype[-1]
            lines.append(f"{'#' * int(level)} {text}")
        elif btype == "paragraph":
            lines.append(f"{prefix}{text}")
        elif btype == "bulleted_list_item":
            lines.append(f"{prefix}• {text}")
        elif btype == "numbered_list_item":
            lines.append(f"{prefix}1. {text}")
        elif btype == "to_do":
            checked = "x" if bdata.get("checked") else " "
            lines.append(f"{prefix}[{checked}] {text}")
        elif btype == "quote":
            lines.append(f"{prefix}> {text}")
        elif btype == "callout":
            icon = bdata.get("icon", {}).get("emoji", "")
            lines.append(f"{prefix}{icon} {text}")
        elif btype == "code":
            lang = bdata.get("language", "")
            lines.append(f"{prefix}```{lang}\n{text}\n```")
        elif btype == "divider":
            lines.append("---")
        elif btype == "table_row":
            cells = bdata.get("cells", [])
            cell_texts = ["".join(rt.get("plain_text", "") for rt in cell) for cell in cells]
            lines.append(f"{prefix}| {' | '.join(cell_texts)} |")
        elif text:
            lines.append(f"{prefix}{text}")

        # Recurse into children
        if block.get("has_children"):
            child_blocks = get_block_children(block["id"])
            child_text = _parse_blocks(child_blocks, indent + 1)
            if child_text:
                lines.append(child_text)

    return "\n".join(lines)
