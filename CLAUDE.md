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

### Quantitative risk roles
"Quantitative risk" job titles (Risk Manager, Quantitative Financial Risk, Risk Analyst) require reading the actual responsibilities before scoring.

**KEEP** if the core work is ML/DS modeling: credit scoring models, default/LGD/PD prediction, risk forecasting, loss models, anomaly detection — these are data science roles with a risk domain.

**DISCARD (wrong role type)** if the core work is: stress testing, scenario analysis, portfolio margin analysis, risk tooling/reporting infrastructure, or the posting explicitly requires domain-specific quant finance experience (VaR, FRTB, Basel, financial risk frameworks). These are quantitative finance / risk management roles, not DS/ML.

Examples:
- "Build credit default prediction models using XGBoost" → KEEP
- "Execute portfolio margin stress tests and scenario analysis under tight timelines" → DISCARD
- "Develop and maintain quantitative analysis tools for credit, market, and liquidity risk" → DISCARD

### UK Remote rule
Treat "United Kingdom Remote" / "UK Remote" exactly like "US Remote": **DISCARD by default**. Exception: **KEEP** if the posting explicitly mentions visa sponsorship (e.g. "UK Skilled Worker Visa Sponsor"), contractor/freelance open to international, or remote-from-EU acceptable.

Always read the full content from `jobs_raw.json` for UK-listed roles before discarding — sponsorship info is often only in the full text, not the snippet.

### Interest score drivers (reminder)
High interest: technically excellent team, IC depth, novel ML methods, production impact at scale, small fast team.
Low interest: consulting/outsourcing firms, pure analytics without modeling, management-heavy roles.
