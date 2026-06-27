# CONNECT — Owner channel-connect runbook (~20 min)

Until you complete this, the Growth Agent stays in **prepare-mode** (it sharpens
creative and keeps `awaiting_connect: true`) and never publishes, emails, or spends.
Completing it flips the agent to **execute-mode** (queue content, advance email, run
falsifiable experiments, measure lift).

The factory **builds** all of this with provider abstractions in **dry-run**; you
**connect + authorize + fund**. Secrets live in the deployed app's env, never in the
agent and never committed.

## 1. Email provider (~7 min)
- Pick a provider (e.g. Resend, Postmark, SendGrid, Mailchimp).
- Create an API key. Add it to the deployed backend env (e.g. `EMAIL_API_KEY`,
  `EMAIL_FROM`). Verify your sending domain (SPF/DKIM) for deliverability.
- Confirm double-opt-in is on (the engine assumes it).

## 2. Analytics (~5 min)
- Pick a privacy-safe analytics tool (e.g. Plausible, PostHog self-host, GA4 with
  consent). Add the site/app key to env.
- Expose only **aggregates** to the read-API the Growth Agent uses — no raw PII/events.

## 3. Publishing channels (~5 min)
- Connect only channels you own and authorize (your own X/LinkedIn/blog). The Growth
  Agent will queue drafts; **you** approve publishing. No fake accounts, no automation
  that logs into communities, no astroturf, no paid reviews.

## 4. Paid acquisition (optional, only when funded)
- The agent never spends without a funded, authorized budget with a hard cap. Set the
  cap with the provider, then record the budget in the deploy env.

## 5. Flip the switch
- Once a channel is connected + authorized, update `channels_connected` /
  `awaiting_connect` via the Growth Agent's next run (it detects the env), or note it in
  PENDING_OPS as done. The agent moves to execute-mode automatically when it sees a
  connected channel.

> Boundary: the agent **recommends and prepares**; **you** authorize the first live
> send/post/spend. FTC disclosure required on anything promotional.
