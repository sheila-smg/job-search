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

### Location & relocation — Portugal + EU remote (updated 2026-06-19)
Sheila is an EU resident (currently Spain) and is **open to relocating to Portugal**. This is purely additive — global remote is still the ideal. Acceptable locations, ranked by interest:

1. **Fully remote, global** — top preference. No interest penalty.
2. **EU remote / "Remote — Europe" / remote-from-EU** — now **KEEP** (previously flagged as ambiguous). Slight-to-no interest penalty.
3. **Portugal-based — onsite, hybrid, or remote-from-PT** (Lisbon/Porto/Lisboa/anywhere in Portugal) — now **KEEP**, but apply a small interest penalty (≈ −1) because it requires relocating. Treat Portugal onsite the same as Portugal hybrid.

Unchanged: **US Remote → DISCARD** (no visa, unless explicit sponsorship/contractor-international). **UK Remote → DISCARD** (non-EU; unless sponsorship/remote-from-EU). Onsite/hybrid **outside Portugal** → DISCARD as before. A role that just says "Remote" from a clearly EU/global company → KEEP and treat as EU/global remote; only US/UK "Remote" ambiguity follows the discard-by-default rule.

### Salary floors (updated 2026-06-19 — replaces the old 90K USD floor, applies to ALL roles)
Floors are now in **EUR** and depend on contract type:
- **Employee / permanent contract:** 75K EUR/year
- **Freelance / contractor contract:** 90K EUR/year

Apply with **~10% flexibility**: a posting within ~10% under the relevant floor is **KEEP-but-FLAG on salary**, not a discard. **DISCARD on salary** only when a posting states a number clearly below the floor (more than ~10% under). When salary is not stated, do not discard on salary — score on fit. If contract type is unstated, assume employee (75K EUR) unless the posting reads as a contractor/freelance gig.

### End-of-analysis push (MANDATORY)
After writing the daily analysis you MUST, in this order: (1) update seen.json with ALL URLs from today's compact_jobs.json, (2) commit both files, (3) `git push` and **verify the push succeeded** (re-run `git status`/`git log origin/main..main` — it must show no unpushed commits). An unpushed seen.json silently breaks the next day's dedup and causes every posting to be re-analyzed. If the push fails (e.g. OneDrive briefly locks .git files), retry until it goes through.

### Interest score drivers (reminder)
High interest: technically excellent team, IC depth, novel ML methods, production impact at scale, small fast team.
Low interest: consulting/outsourcing firms, pure analytics without modeling, management-heavy roles.
