#!/usr/bin/env python3
"""
Publishes the next due, approved item in queue.json to Instagram via the
Graph API, then commits the updated queue.json back to the repo.

Runs hourly from GitHub Actions (.github/workflows/publish.yml). Posts at
most ONE item per run (MAX_PER_RUN) so a backlog drips out on schedule
instead of flooding the account if a run is missed and several items go
overdue at once.

Required environment variables (set as GitHub Actions secrets, never
committed to the repo):
  IG_ACCESS_TOKEN  - long-lived / System User Page access token
  IG_BUSINESS_ID   - Instagram Business Account ID for @theconnectorclub_
  GITHUB_REPOSITORY - auto-provided by Actions ("owner/repo")
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = REPO_ROOT / "queue.json"
GRAPH_VERSION = "v21.0"
MAX_PER_RUN = 1
PUBLISH_POLL_ATTEMPTS = 10
PUBLISH_POLL_DELAY_SECONDS = 15

IG_ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_BUSINESS_ID = os.environ["IG_BUSINESS_ID"]
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "theconnectorclub/connector-club-content")
GITHUB_REF = os.environ.get("GITHUB_REF_NAME", "main")


def raw_media_url(media_file: str) -> str:
    return f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/{GITHUB_REF}/{media_file}"


def load_queue() -> list:
    return json.loads(QUEUE_PATH.read_text())


def save_queue(items: list) -> None:
    QUEUE_PATH.write_text(json.dumps(items, indent=2) + "\n")


def due_items(items: list) -> list:
    now = datetime.now(timezone.utc)
    due = []
    for item in items:
        if item.get("status") != "approved":
            continue
        scheduled = datetime.fromisoformat(item["scheduled_time"])
        if scheduled <= now:
            due.append(item)
    due.sort(key=lambda i: i["scheduled_time"])
    return due


def create_media_container(item: dict) -> str:
    video_url = raw_media_url(item["media_file"])
    data = {
        "media_type": item.get("media_type", "REELS"),
        "video_url": video_url,
        "caption": item["caption"],
        "access_token": IG_ACCESS_TOKEN,
    }
    if item.get("trial"):
        # Trial reels are shown to non-followers first; SS_PERFORMANCE lets
        # Instagram auto-graduate it to the main grid if it performs well,
        # with no manual in-app step required.
        data["trial_params"] = json.dumps({"graduation_strategy": "SS_PERFORMANCE"})
    if item.get("share_to_feed") is False:
        # Reels-tab only, not shown on the main profile grid.
        data["share_to_feed"] = "false"
    resp = requests.post(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_BUSINESS_ID}/media",
        data=data,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def wait_until_container_ready(creation_id: str) -> None:
    for _ in range(PUBLISH_POLL_ATTEMPTS):
        resp = requests.get(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{creation_id}",
            params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN},
            timeout=30,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Media container {creation_id} failed processing")
        time.sleep(PUBLISH_POLL_DELAY_SECONDS)
    raise TimeoutError(f"Media container {creation_id} did not finish processing in time")


def publish_container(creation_id: str) -> str:
    resp = requests.post(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_BUSINESS_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def main() -> None:
    items = load_queue()
    candidates = due_items(items)[:MAX_PER_RUN]

    if not candidates:
        print("Nothing due this run.")
        return

    changed = False
    for item in candidates:
        print(f"Publishing {item['id']} ({item['media_file']}) ...")
        try:
            creation_id = create_media_container(item)
            wait_until_container_ready(creation_id)
            media_id = publish_container(creation_id)
            item["status"] = "posted"
            item["ig_media_id"] = media_id
            item["posted_at"] = datetime.now(timezone.utc).isoformat()
            item["last_error"] = None
            print(f"  -> posted as {media_id}")
        except Exception as exc:  # noqa: BLE001 - log and continue, never crash the run
            item["status"] = "failed"
            item["last_error"] = str(exc)
            print(f"  -> FAILED: {exc}", file=sys.stderr)
        changed = True

    if changed:
        save_queue(items)


if __name__ == "__main__":
    main()
