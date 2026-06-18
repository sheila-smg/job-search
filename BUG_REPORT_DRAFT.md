# Bug report: CCR routine sessions stuck indefinitely at container provisioning

## Summary
Scheduled CCR routines never start executing — every run gets permanently stuck
at "Configurando un contenedor en la nube" (setting up a cloud container) and
never progresses to running the agent prompt. No logs, no output, no error —
the session just spins forever.

## Affected
- Account: Sheila (sheilasmgg92@gmail.com / display name "Sheila")
- Environment: `env_01DBftVk2RpxptBaPQNM8GRE` (the "Default" environment, kind: anthropic_cloud)
- Routine 1 (original): `trig_01Hyb7UqsT7HSngWuwh2Jhas` — "Daily Job Search — Sheila"
  - Created: 2026-05-29
  - Schedule: `30 6 * * *` UTC (daily)
  - **Every single scheduled/manual run since creation has been stuck "loading"** —
    confirmed via the routine's run-history page, where all entries show "loading"
    and never resolve to completed/failed.
- Routine 2 (freshly recreated to rule out corrupted state): `trig_01JW4BPkt6fuwd8QMNL3cxso`
  - Created: 2026-06-08T09:44 UTC, same environment, same repo source, simplified config
  - Manually triggered immediately after creation — **also stuck at container
    provisioning ("Configurando un contenedor en la nube") for 45+ minutes**

## Why this rules out a config/prompt issue
We spent significant effort eliminating other explanations before concluding
this is an infrastructure problem:
1. Verified the GitHub PAT used by the routine has valid `repo`+`workflow` scopes
   and push access (tested via `git ls-remote` / dry-run push).
2. Found and fixed a latent bug in the repo's `check_freshness.py` (an unguarded
   `subprocess.run(["git","pull",...])` with no timeout) — did not change the outcome.
3. Enabled `allow_unrestricted_git_push` on the git_repository source — did not
   change the outcome.
4. Created an entirely new routine from scratch (new ID, fresh config, push
   permission baked in at creation) — **exhibits the identical hang**, confirming
   this isn't routine-specific corrupted state but an environment/platform issue.

The container for the new routine never finishes provisioning — the agent never
even begins reading its prompt. This is squarely a platform infra bug, not
something fixable from the user side.

## Impact
A daily automated job-search analysis pipeline has produced **zero successful
runs since the routine's creation on 2026-05-29** (i.e., it has never worked even
once), forcing the user to manually backfill analysis documents for over a week.

## Requested action
Please investigate why CCR sessions in environment `env_01DBftVk2RpxptBaPQNM8GRE`
(or generally for this account) get stuck indefinitely at container provisioning,
and why no timeout/error is ever surfaced to the user when this happens.

---
---

# FOLLOW-UP — ready to send to support (2026-06-11)

> Reply with this on the existing (auto-closed) ticket — replying reopens it.

Hi — following up on my report about cloud routines never running ("Configurando
un contenedor en la nube" forever). The issue is still occurring, and I have new,
concrete evidence since my first message. Please reopen the ticket.

Account: sheilasmg92@gmail.com (account_uuid 3be58448-297e-4123-920b-8eb72d4ba7cc)
Environment: env_01DBftVk2RpxptBaPQNM8GRE (kind: anthropic_cloud)

Correction to my first message: the routine was created May 29, **2026** (I wrote 2025).

New findings:

1. **Routine `trig_01JW4BPkt6fuwd8QMNL3cxso`** (the fresh replacement) fired on
   2026-06-09 at 06:32 UTC, and on 2026-06-10 at ~06:31 UTC it was
   **auto-disabled by the platform with `ended_reason: "auto_disabled_config_rejected"`**
   (visible via GET /v1/code/triggers). No notification of this was ever surfaced
   to me — my daily automation silently stopped even attempting to run.
   Note: this routine's config had a GitHub PAT embedded in the git source URL
   (https://TOKEN@github.com/...). If that is what the validation rejects, the
   rejection reason should say so, and ideally it should be rejected at creation
   time, not silently days later.

2. **A third routine with a clean config still hangs at provisioning.** On
   2026-06-11 at 06:29 UTC I created `trig_01NHoiKHt2x1y6jmFMHGGYZW` — plain
   `https://github.com/sheila-smg/job-search` source URL (public repo, no
   credentials embedded), default environment, trivial diagnostic prompt (push
   an empty commit to a test branch). The create and run API calls both returned
   HTTP 200, but 20+ minutes later: `last_fired_at` was never set, the session
   never started, and the test branch never appeared on GitHub. Same indefinite
   provisioning hang as the original routine.

So there appear to be **two distinct problems**:
- (a) sessions for this account/environment never finish container provisioning
  (routines `trig_01Hyb7UqsT7HSngWuwh2Jhas` and `trig_01NHoiKHt2x1y6jmFMHGGYZW`);
- (b) a config-validation path that silently auto-disables routines
  (`trig_01JW4BPkt6fuwd8QMNL3cxso`, `auto_disabled_config_rejected`) with no
  user-facing error.

Routine IDs and timestamps again, for your logs:
- trig_01Hyb7UqsT7HSngWuwh2Jhas — created 2026-05-29, every run stuck provisioning
- trig_01JW4BPkt6fuwd8QMNL3cxso — created 2026-06-08, auto-disabled 2026-06-10 ~06:31 UTC
- trig_01NHoiKHt2x1y6jmFMHGGYZW — created 2026-06-11 06:29 UTC, manual run never started

I have since moved my automation to GitHub Actions, so this is no longer urgent
for me day-to-day, but the provisioning hang and the silent auto-disable both
seem like platform bugs worth fixing.

Thank you
