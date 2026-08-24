"""Probe CourtListener's batch citation-lookup endpoint with a few citations.

Usage:
    python -m uslegalqa.probe_lookup
"""

from __future__ import annotations

import json
import os
import sys

import requests

API_ROOT = "https://www.courtlistener.com/api/rest/v4"

# Three well-known cases with unambiguous U.S. Reports citations.
SAMPLE = ["544 U.S. 431", "545 U.S. 469", "550 U.S. 618"]


def main() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    token = os.getenv("COURTLISTENER_TOKEN")
    if not token:
        sys.exit("COURTLISTENER_TOKEN is not set")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Token {token}",
        "User-Agent": "USLegalQA/3.0 (academic research)",
    })

    url = f"{API_ROOT}/citation-lookup/"
    print(f"POST {url}")
    print(f"citations: {SAMPLE}\n")

    try:
        r = session.post(url, data={"text": "  ".join(SAMPLE)}, timeout=60)
    except requests.RequestException as e:
        sys.exit(f"request failed: {e}")

    print(f"HTTP {r.status_code}")
    if r.status_code == 429:
        retry = r.headers.get("Retry-After")
        print(f"Still rate limited. Retry-After: {retry}s "
              f"({int(retry) // 60 if retry else '?'} min)")
        return

    if r.status_code == 404:
        print("Endpoint not present on this API version.")
        return

    if r.status_code >= 400:
        print(f"Error body: {r.text[:400]}")
        return

    try:
        payload = r.json()
    except ValueError:
        print(f"Non-JSON response: {r.text[:300]}")
        return

    print(json.dumps(payload, indent=2)[:2500])

    items = payload if isinstance(payload, list) else payload.get("results", [])
    resolved = 0
    for item in items if isinstance(items, list) else []:
        clusters = item.get("clusters") or []
        if clusters:
            resolved += 1
            c = clusters[0]
            print(f"\n  {item.get('citation')} -> cluster {c.get('id')} "
                  f"{str(c.get('case_name'))[:50]}")

    print(f"\nResolved {resolved}/{len(SAMPLE)} citations in one request.")
    if not resolved:
        print("No clusters returned; check the response shape above.")


if __name__ == "__main__":
    main()
