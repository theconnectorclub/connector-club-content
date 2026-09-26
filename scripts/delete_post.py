#!/usr/bin/env python3
"""
Deletes a single published Instagram post/reel by its media ID, via the
Graph API. Triggered manually (workflow_dispatch with a media_id input),
never automatically.

Required environment variables:
  IG_ACCESS_TOKEN - same System User token used for publishing
  MEDIA_ID        - the ig_media_id to delete
"""
import os
import sys

import requests

GRAPH_VERSION = "v21.0"

IG_ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
MEDIA_ID = os.environ["MEDIA_ID"]


def main() -> None:
    resp = requests.delete(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{MEDIA_ID}",
        params={"access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    print(resp.status_code, resp.text)
    resp.raise_for_status()
    if not resp.json().get("success", False):
        print("Delete call succeeded but did not report success=true", file=sys.stderr)
        sys.exit(1)
    print(f"Deleted {MEDIA_ID}")


if __name__ == "__main__":
    main()
