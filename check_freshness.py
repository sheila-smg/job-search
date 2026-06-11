#!/usr/bin/env python3
"""
Run at the start of each CCR agent session.
If compact_jobs.json is stale or missing, triggers the GitHub Actions search
workflow and waits for it to complete, then pulls the fresh data.
Exits 0 in all cases so the agent always continues.
"""
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
REPO = "sheila-smg/job-search"


def get_token():
    """GitHub token: env var first, then PAT embedded in the git remote URL."""
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True
    )
    url = result.stdout.strip()
    # Format: https://TOKEN@github.com/...
    try:
        return url.split("@")[0].split("//")[1]
    except IndexError:
        return ""


def gh(path, method="GET", body=None, token=""):
    hdrs = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "User-Agent": "job-finder-bot",
        "Accept": "application/vnd.github.v3+json",
    }
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers=hdrs,
        method=method,
        data=json.dumps(body).encode() if body else None,
    )
    last_err = None
    for attempt in range(3):
        if attempt:
            time.sleep(10 * attempt)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = r.read()
                return json.loads(resp) if resp else None
        except Exception as e:
            last_err = e
            print(f"  (attempt {attempt + 1}/3 failed: {e})")
    raise RuntimeError(f"GitHub API call failed ({method} {path}): {last_err}")


def is_fresh():
    try:
        with open("compact_jobs.json", encoding="utf-8") as f:
            return json.load(f).get("date") == TODAY
    except FileNotFoundError:
        return False


def trigger_and_wait(token):
    workflows = gh(f"/repos/{REPO}/actions/workflows", token=token)
    wf_id = next(
        (w["id"] for w in workflows["workflows"] if "daily-search" in w["path"]), None
    )
    if wf_id is None:
        print("WARNING: daily-search workflow not found. Continuing with existing data.")
        return

    before = gh(f"/repos/{REPO}/actions/workflows/{wf_id}/runs?per_page=1", token=token)
    before_id = before["workflow_runs"][0]["id"] if before["total_count"] > 0 else None

    gh(f"/repos/{REPO}/actions/workflows/{wf_id}/dispatches", method="POST",
       body={"ref": "main"}, token=token)
    print("GH Actions dispatched. Waiting for run to start...")

    new_run_id = None
    for _ in range(18):  # up to 3 minutes
        time.sleep(10)
        runs = gh(f"/repos/{REPO}/actions/workflows/{wf_id}/runs?per_page=1", token=token)
        if runs["total_count"] > 0 and runs["workflow_runs"][0]["id"] != before_id:
            new_run_id = runs["workflow_runs"][0]["id"]
            print(f"Run {new_run_id} started.")
            break

    if not new_run_id:
        print("WARNING: new run did not appear within 3 min. Continuing with existing data.")
        return

    for _ in range(36):  # up to 6 more minutes
        time.sleep(10)
        run = gh(f"/repos/{REPO}/actions/runs/{new_run_id}", token=token)
        print(f"  status: {run['status']}")
        if run["status"] == "completed":
            print(f"Workflow finished: {run['conclusion']}")
            break

    # Retry the pull: on Windows, OneDrive sync can briefly lock .git files
    # (e.g. "could not open .git/FETCH_HEAD: Permission denied").
    for attempt in range(3):
        if attempt:
            time.sleep(15)
        try:
            result = subprocess.run(
                ["git", "pull", "--no-rebase", "origin", "main"],
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            print(result.stdout.strip() or result.stderr.strip())
            if result.returncode == 0:
                return
        except subprocess.TimeoutExpired:
            print("WARNING: git pull timed out after 60s (likely waiting on a "
                  "credential prompt).")
    print("WARNING: git pull did not succeed after 3 attempts. "
          "Continuing with existing data.")


try:
    if is_fresh():
        print(f"compact_jobs.json is already fresh ({TODAY}). No action needed.")
    else:
        print("compact_jobs.json is missing or stale. Triggering GH Actions search...")
        trigger_and_wait(get_token())
except Exception as e:
    print(f"WARNING: freshness check failed ({e}). Continuing with existing data.")

print("check_freshness.py done — continuing regardless of outcome above.")
