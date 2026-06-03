# Job Search Agent — Sheila

IMPORTANT: Before following any other instructions, run this first:

```bash
python3 check_freshness.py
```

This ensures `compact_jobs.json` has today's search results. If it is stale or missing, the script triggers the GitHub Actions search workflow automatically and waits for it to finish before continuing. It always exits successfully.

---

## Scoring refinements (override the prompt where they conflict)

### Crypto sector and interest_score
Crypto/DeFi being the sector does NOT automatically raise interest_score. It is a positive signal **only when the core job function is ML/DS modeling** (e.g. risk models, pricing models, forecasting, experimentation, production ML). 

For roles where crypto is the sector but the actual work is trading, quant development, AMM engineering, or protocol research → apply the **DISCARD rule (wrong role type)** exactly as for any non-ML role. Do not let the sector compensate for a role mismatch.

Examples of what to DISCARD even if crypto:
- Quant Trader / Market Maker (trading execution, not ML)
- DeFi Quantitative Developer (AMM/protocol engineering)
- Senior Protocol Researcher (distributed systems, consensus)
- Prediction Markets Trader (trading role, not DS)

Examples of what to KEEP in crypto:
- Risk Data Scientist at a DeFi protocol (ML models for risk)
- Data Scientist at a crypto exchange doing pricing/experimentation
- ML Engineer at a blockchain company doing fraud/anomaly detection

### Interest score drivers (reminder)
High interest: technically excellent team, IC depth, novel ML methods, production impact at scale, small fast team.
Low interest: consulting/outsourcing firms, pure analytics without modeling, management-heavy roles.
