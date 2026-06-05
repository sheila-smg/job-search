#!/usr/bin/env python3
"""
Job finder — Exa search only.
Saves raw results to jobs_raw.json for analysis by Claude Code.

Usage:
    python job_finder.py                                    # run search
    python job_finder.py --apply URL "Company" "Role"      # log a full application
    python job_finder.py --skip "Company A" "Company B"    # skip companies by name only

No external dependencies — uses stdlib only.
"""

import argparse
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

EXA_API_KEY = os.environ.get("EXA_API_KEY", "5d962423-d391-4609-9b39-ed8787503b5d")

DAYS_BACK = 30
RESULTS_PER_QUERY = 15
OUTPUT_FILE = "jobs_raw.json"
APPLIED_FILE = "applied.json"
APPLIED_EXPIRY_DAYS = 30

# Low-quality scrapers and aggregators that pollute results
EXCLUDE_DOMAINS = [
    # Known spam/fake aggregators
    "hireza.wuaze.com",
    "flexionis.wuaze.com",
    "hirebase.infinityfree.me",
    "hirro.kesug.com",
    "careerium.unaux.com",
    "remotica.totalh.net",
    "jaabz.com",
    "remoteyeah.com",
    "berlinstartupjobs.com",
    # liveblog365 aggregators — unverified postings, frequent mismatches
    "hirevector.liveblog365.com",
    "jobflarely.liveblog365.com",
    "wfhverse.liveblog365.com",
    "jobicyremote.liveblog365.com",
    # Other low-signal aggregators
    "wfh.hstn.me",
    "wfhforgeon.byethost7.com",
    "no-commute-jobs.com",
    "inclusivelyremote.com",
    "corptocorp.org",
    "upstaff.com",
    "tryjeremy.com",
    "aworker.io",
]

SEARCH_QUERIES = [
    # Crypto / web3 — preferred sector
    "Senior Data Scientist remote crypto web3 DeFi blockchain",
    "Machine Learning Engineer remote crypto DeFi risk quantitative",
    "quantitative researcher data scientist remote DeFi protocol",
    # Risk, pricing & quantitative ML — core expertise
    "Senior Data Scientist risk pricing models quantitative fully remote",
    "Senior Applied Scientist risk quantitative ML modeling fully remote",
    "Machine Learning Engineer credit risk fraud detection fully remote",
    "Data Scientist actuarial pricing insurance ML fully remote",
    # Prediction markets / fintech
    "Senior Data Scientist prediction markets probabilistic forecasting remote",
    "Machine Learning Engineer fintech quantitative trading risk remote",
    # General senior remote global — broad net
    "Senior Data Scientist fully remote global",
    "Senior Machine Learning Engineer fully remote global",
    "Senior Applied Scientist ML production systems fully remote",
    "Senior Data Scientist causal inference experimentation fully remote",
    "Machine Learning Engineer production ML systems fully remote global",
    # Europe-specific — catches postings that use EU/Europe instead of global
    "Senior Machine Learning Engineer remote Europe EU",
    "Senior ML Engineer production ML systems remote Europe",
    "Senior Data Scientist remote Europe startup",
    # Marketplace / startup / product — catches non-crypto roles that fit
    "senior data scientist marketplace startup remote",
    "senior data scientist pricing A/B testing remote",
    "senior ML engineer product analytics remote",
    "applied scientist experimentation causal inference remote",
    "senior data scientist fintech startup remote europe",
]

# Targeted searches restricted to specific job boards.
# Each entry: (query, domains)
DOMAIN_QUERIES: list[tuple[str, list[str]]] = [
    # Greenhouse & Lever — startups publish here, Exa's general index misses them
    (
        "senior data scientist machine learning remote",
        ["boards.greenhouse.io", "jobs.lever.co"],
    ),
    (
        "senior machine learning engineer remote",
        ["boards.greenhouse.io", "jobs.lever.co"],
    ),
    (
        "senior data scientist pricing risk experimentation remote",
        ["boards.greenhouse.io", "jobs.lever.co"],
    ),
    (
        "applied scientist data scientist crypto DeFi remote",
        ["boards.greenhouse.io", "jobs.lever.co"],
    ),
    # LinkedIn — large reach, EU roles often posted here only
    (
        "senior machine learning engineer remote Europe",
        ["linkedin.com"],
    ),
    (
        "senior data scientist remote Europe fully remote",
        ["linkedin.com"],
    ),
    # Wellfound (AngelList) — startup roles, often globally remote
    (
        "senior data scientist machine learning engineer remote",
        ["wellfound.com"],
    ),
    # Remote Rocketship — curated remote roles
    (
        "senior data scientist machine learning engineer remote",
        ["remoterocketship.com"],
    ),
    # Welcome to the Jungle — strong EU coverage
    (
        "senior data scientist machine learning engineer remote",
        ["welcometothejungle.com"],
    ),
]


# ── Applied list helpers ──────────────────────────────────────────────────────

def _norm(s: str) -> str:
    return s.lower().strip()


def load_applied() -> list[dict]:
    if not os.path.exists(APPLIED_FILE):
        return []
    with open(APPLIED_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_applied(entries: list[dict]) -> None:
    with open(APPLIED_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def active_applied(entries: list[dict]) -> list[dict]:
    cutoff = datetime.now() - timedelta(days=APPLIED_EXPIRY_DAYS)
    return [e for e in entries if datetime.fromisoformat(e["date"]) >= cutoff]


def is_already_applied(job: dict, active: list[dict]) -> tuple[bool, str]:
    """Returns (should_skip, reason)."""
    url_norm = _norm(job["url"])
    title_norm = _norm(job["title"])

    for e in active:
        # Exact URL match
        if e.get("url") and _norm(e["url"]) == url_norm:
            return True, f"URL match — {e['company']}"
        # Company name anywhere in the job title (catches reposts on other platforms)
        company = _norm(e.get("company", ""))
        if company and company in title_norm:
            return True, f"Company match — {e['company']}"

    return False, ""


def add_entries(new_entries: list[dict]) -> None:
    entries = load_applied()
    today = datetime.now().date().isoformat()
    added = []
    for new in new_entries:
        # Avoid duplicates: same company + role (or company-only)
        exists = any(
            _norm(e.get("company", "")) == _norm(new["company"])
            and _norm(e.get("role", "")) == _norm(new.get("role", ""))
            for e in entries
        )
        if not exists:
            new["date"] = today
            entries.append(new)
            added.append(new)

    save_applied(entries)
    for e in added:
        role_str = f" — {e['role']}" if e.get("role") else ""
        url_str = f" ({e['url']})" if e.get("url") else ""
        print(f"  Added: {e['company']}{role_str}{url_str}")
    if not added:
        print("  Nothing new to add (all entries already exist).")


# ── Exa search ────────────────────────────────────────────────────────────────

def _exa_search(query: str, start_date: str, extra: dict) -> list[dict]:
    payload = {
        "query": query,
        "type": "neural",
        "numResults": RESULTS_PER_QUERY,
        "startPublishedDate": start_date,
        "excludeDomains": EXCLUDE_DOMAINS,
        "contents": {"text": {"maxCharacters": 3500}},
        **extra,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.exa.ai/search",
        data=data,
        headers={"x-api-key": EXA_API_KEY, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["results"]


def search_jobs() -> list[dict]:
    seen_urls: set[str] = set()
    results: list[dict] = []
    start_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime(
        "%Y-%m-%dT00:00:00.000Z"
    )

    def _fetch(query: str, extra: dict) -> None:
        print(f"  Searching: {query[:68]}...")
        try:
            for r in _exa_search(query, start_date, extra):
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append({
                        "title": r.get("title") or "",
                        "url": url,
                        "published": r.get("publishedDate") or "",
                        "content": (r.get("text") or "")[:3500],
                        "matched_query": query,
                    })
            time.sleep(0.4)
        except Exception as exc:
            print(f"    Warning: query failed — {exc}")

    for query in SEARCH_QUERIES:
        _fetch(query, {})

    print(f"\n  Searching Greenhouse & Lever ({len(DOMAIN_QUERIES)} queries)...")
    for query, domains in DOMAIN_QUERIES:
        _fetch(query, {"includeDomains": domains})

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Job finder — Exa search")
    parser.add_argument(
        "--apply", nargs=3, metavar=("URL", "COMPANY", "ROLE"),
        help="Log a full application: --apply URL 'Company' 'Role'",
    )
    parser.add_argument(
        "--skip", nargs="+", metavar="COMPANY",
        help="Skip companies by name (no URL needed): --skip 'Company A' 'Company B'",
    )
    args = parser.parse_args()

    if args.apply:
        url, company, role = args.apply
        add_entries([{"url": url, "company": company, "role": role}])
        return

    if args.skip:
        add_entries([{"company": c, "role": "", "url": ""} for c in args.skip])
        return

    # ── Search ──
    all_applied = load_applied()
    active = active_applied(all_applied)
    expired = len(all_applied) - len(active)
    if active:
        print(f"\nLoaded {len(active)} active entries ({expired} expired/ignored)")

    print(f"\nSearching Exa ({len(SEARCH_QUERIES)} queries, last {DAYS_BACK} days)...")
    jobs = search_jobs()

    skipped, kept = [], []
    for j in jobs:
        skip, reason = is_already_applied(j, active)
        if skip:
            skipped.append((j["title"], reason))
        else:
            kept.append(j)

    if skipped:
        print(f"\nSkipped {len(skipped)} already-applied posting(s):")
        for title, reason in skipped:
            print(f"    {title[:55]}  [{reason}]")

    print(f"{len(kept)} new postings found")

    output = {
        "fetched_at": datetime.now().isoformat(),
        "days_back": DAYS_BACK,
        "total": len(kept),
        "results": kept,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved to {OUTPUT_FILE}")
    print("\nNext step: ask Claude Code to analyze jobs_raw.json")
    print("To log an application: python job_finder.py --apply URL 'Company' 'Role'")
    print("To skip companies:     python job_finder.py --skip 'Company A' 'Company B'\n")


if __name__ == "__main__":
    main()
