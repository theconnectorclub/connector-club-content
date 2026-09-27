#!/usr/bin/env python3
"""One-off: fetch every field the Graph API will give us for a published
media item, so we can actually see whether trial/feed-sharing behaved as
requested instead of assuming it from a successful publish call.

Required env: IG_ACCESS_TOKEN, MEDIA_ID
"""
import os

import requests

GRAPH_VERSION = "v21.0"
IG_ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
MEDIA_ID = os.environ["MEDIA_ID"]

FIELDS = ",".join([
    "id", "media_type", "media_product_type", "permalink",
    "is_shared_to_feed", "timestamp", "caption",
])

resp = requests.get(
    f"https://graph.facebook.com/{GRAPH_VERSION}/{MEDIA_ID}",
    params={"fields": FIELDS, "access_token": IG_ACCESS_TOKEN},
    timeout=30,
)
print(resp.status_code)
print(resp.text)
