# connector-club-content

Fully automated Instagram posting for **@theconnectorclub_**. Runs hourly on
GitHub Actions — cloud-only, works even if every laptop is off. Standalone
repo, standalone GitHub account (`theconnectorclub`), standalone Meta
credentials at the token level. Nothing here touches any other project's
repo, queue, or account.

## How to add a new post

1. Drop the finished video into `media/` (e.g. `media/2026-10-03-scale.mp4`).
   Keep each file under 100MB — GitHub serves it for free via
   `raw.githubusercontent.com`, which is what Instagram's API fetches from.
2. Add an entry to `queue.json`:

```json
{
  "id": "2026-10-03-scale",
  "media_file": "media/2026-10-03-scale.mp4",
  "media_type": "REELS",
  "caption": "Full caption text, including the DM CTA.",
  "scheduled_time": "2026-10-03T18:00:00+05:00",
  "status": "draft",
  "ig_media_id": null,
  "posted_at": null,
  "last_error": null
}
```

3. When it's ready to actually go out, change `"status": "draft"` to
   `"status": "approved"`. **Nothing posts until this flip happens** — that's
   the safety gate. `scheduled_time` uses Pakistan time (`+05:00`); the
   workflow compares real timestamps, not just the hour, so it's fine if a
   run lands a few minutes late.
4. Commit and push. The next hourly run (`.github/workflows/publish.yml`)
   will pick up anything `approved` and due, publish it, and commit the
   updated status back automatically.

Only **one** due item is published per run (`MAX_PER_RUN` in
`scripts/post.py`), even if several are overdue — this drips a backlog out
on schedule instead of flooding the account if a run gets missed.

## One-time setup (already done / to confirm)

- Repo is **public** — required so Instagram's servers can fetch
  `raw.githubusercontent.com/.../media/....mp4` without authentication.
  Nothing sensitive belongs here beyond upcoming captions/schedule.
- Two GitHub Actions secrets, set once via `gh secret set` (never committed,
  never pasted in chat):
  - `IG_ACCESS_TOKEN` — a Meta **System User** access token (Business
    Manager → System Users), scoped to the `autoposting` app with
    `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
    `pages_read_engagement`. System User tokens can be set to never expire,
    so this should be a true one-time setup, not a 60-day renewal chore.
  - `IG_BUSINESS_ID` — the Instagram Business Account ID for
    @theconnectorclub_.

## Checking on it

- `queue.json` is the single source of truth — `status` per item is
  `draft` → `approved` → `posted` (or `failed`, with `last_error` filled in;
  fix the issue, flip it back to `approved`, it'll retry next run).
- Actions tab → **Publish queued Instagram content** shows every run's log.
- Manual trigger any time: Actions tab → this workflow → **Run workflow**
  (no need to wait for the hourly cron).

## Explicitly NOT shared with other projects

- Not `city-reels` (mee.tpeople). Not `linkedin-autopilot` (Psycomaths).
- Separate GitHub account, separate repo, separate secrets.
- The Meta **app** (`autoposting`, ID 923546734112622) is reused across
  projects by prior explicit approval — but the **token** and **Instagram
  Business Account ID** here are unique to @theconnectorclub_.
# test
