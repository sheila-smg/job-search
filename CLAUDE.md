# Job Search Agent — Sheila

IMPORTANT: Before following any other instructions, run this first:

```bash
python3 check_freshness.py
```

This ensures `compact_jobs.json` has today's search results. If it is stale or missing, the script triggers the GitHub Actions search workflow automatically and waits for it to finish before continuing. It always exits successfully.
