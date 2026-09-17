#!/usr/bin/env python3
"""
scripts/retrigger_workflow.py

Safely triggers a new GitHub Actions workflow run before/after runner limit.
Features:
1. Multi-token fallback (GH_PAT -> GITHUB_TOKEN).
2. Checks for existing queued or in-progress runs to prevent duplicate parallel jobs.
3. Up to 3 retry attempts with exponential backoff on transient errors.
4. Clean exit without breaking workflow handoff.
"""

import os
import sys
import time
from datetime import datetime, timezone, timedelta
import requests

GITHUB_API_URL = "https://api.github.com"

def retrigger():
    pat = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY", "yasamarium/llmserver")
    workflow_id = os.getenv("WORKFLOW_ID", "server.yml")
    ref = os.getenv("GITHUB_REF_NAME", "main")
    
    if not pat:
        print(f"[WARN] No GH_PAT token provided for {repo}. Chaining skipped.")
        return

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {pat}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # 1. Check existing active runs for this workflow
    runs_url = f"{GITHUB_API_URL}/repos/{repo}/actions/workflows/{workflow_id}/runs"
    try:
        resp = requests.get(runs_url, headers=headers, params={"status": "in_progress", "per_page": 5}, timeout=15)
        curr_run_id = os.getenv("GITHUB_RUN_ID")
        if resp.status_code == 200:
            in_prog = resp.json().get("workflow_runs", [])
            other_active = [r for r in in_prog if str(r.get("id")) != str(curr_run_id)]
            if other_active:
                print(f"[GUARD] Active workflow run already exists (Run ID: {other_active[0]['id']}). Skipping redundant trigger.")
                return

        resp_queued = requests.get(runs_url, headers=headers, params={"status": "queued", "per_page": 5}, timeout=15)
        if resp_queued.status_code == 200:
            queued = resp_queued.json().get("workflow_runs", [])
            if queued:
                print(f"[GUARD] Queued workflow run already detected (Run ID: {queued[0]['id']}). Skipping trigger.")
                return

        # 2. Dispatch new workflow run with retry
        dispatch_url = f"{GITHUB_API_URL}/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        payload = {"ref": ref}
        print(f"Initiating workflow handoff dispatch for {repo} ({workflow_id} on {ref})...")

        for attempt in range(1, 4):
            dispatch_resp = requests.post(dispatch_url, headers=headers, json=payload, timeout=20)
            if dispatch_resp.status_code == 204:
                print(f"[SUCCESS] Successfully dispatched new runner handoff for {repo} (Attempt {attempt}).")
                return
            elif dispatch_resp.status_code == 422:
                print(f"[INFO] Workflow dispatch returned 422 (workflow may already be triggering or queued): {dispatch_resp.text}")
                return
            else:
                print(f"[RETRY {attempt}/3] Dispatch returned {dispatch_resp.status_code}: {dispatch_resp.text}")
                time.sleep(attempt * 3)

    except Exception as e:
        print(f"[ERROR] Exception during workflow retrigger for {repo}: {e}")

if __name__ == "__main__":
    retrigger()
