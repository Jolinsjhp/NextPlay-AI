# C / D integration on teammate A / B

This branch extends the registered `decision_analysis` Q2 comparator. It does not replace A's generator, retrain B, or use the legacy `decision.engine.analyze()` for the new coach.

## C: agent service

`decision_analysis/agents.py` implements four separate model contexts: attack → defense → coordinator → reviewer. Attack and defense read the same pre-action candidates; the coordinator answers the question; the reviewer audits the proposed answer. A rejected draft is rewritten once and re-reviewed. Two rejections produce only the computed comparison. Missing configuration, timeouts, invalid citations and exhausted budgets never produce a fake explanation or fake successful trace.

`POST /api/decision-analysis/agents` accepts exactly `{request, candidate_set_id}` using the existing canonical request. The server resolves a registered snapshot and recomputes B's candidate set before invoking any model. It rejects a stale ID. Candidates, evidence and ranks stay unchanged. Neither historical action nor observed future is sent to models. Public response remains the original canonical `analysis_response` schema.

Model tools:

- `compare_actions({})`: returns that immutable candidate set and evidence.
- `simulate_action({action_id})`: executes B's short hypothetical scenario; returns summaries without animation frames. Model arguments cannot change snapshot, profile or candidate set.

Each role uses the Responses tool loop and structured JSON. Actual model and tool calls, local citation checks and durations appear in `agent_trace`. This is a small Python orchestrator, **not** a deployed Foundry Agent Service or Microsoft Agent Framework integration. Semantic review is performed by a model, not a mathematical proof. Valid evidence IDs alone do not guarantee supported prose.

Limits: one review in flight per server process; 150-second workflow deadline; at most 18 Responses calls per review; 1,100 output tokens per call; at most three turns per role. Default daily cap is 100 outbound calls, not 100 user reviews. Failed provider requests also consume reservations. Quota persists in `.local/agent-usage.sqlite3`, counts UTC days, and must be shared/persisted for a single-instance deployment. It is not a currency spending cap; also configure Azure billing controls.

### Foundry connection

Deploy an Azure OpenAI model that supports Responses function calling and structured outputs. Use the **deployment name**, not an assumed model name. Configure server environment from `.env.example` (the server does not automatically read `.env`):

```sh
export NEXTPLAY_MODEL_BASE_URL='https://YOUR-RESOURCE.openai.azure.com/openai/v1'
export NEXTPLAY_MODEL='YOUR-DEPLOYMENT-NAME'
# Set NEXTPLAY_MODEL_API_KEY privately in the shell or cloud secret configuration.
export NEXTPLAY_MODEL_AUTH='auto'
export NEXTPLAY_DAILY_MODEL_CALLS='100'
python3 server.py
```

Azure resource hosts use `api-key`; generic Responses services use Bearer authentication. HTTPS only, no URL credentials, query parameters or redirects. Local Settings credentials are a fallback; environment settings override them for the new service. Judges never enter a key. No API key is returned by the service or stored by the new coach in browser storage. This code does not create an Azure account, claim free credits, deploy a model, or guarantee zero-cost usage.

References: [Microsoft Responses API](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/responses), [Responses function tools](https://developers.openai.com/api/docs/guides/function-calling).

## D: integrated coach

Start the server, open `/`, select **Analysis → Decision analysis**. The existing current-match timeline, shared 2D pitch, B action comparison and counterfactual lab remain the main flow. The new coach panel adds a question, fan/analyst audience, English/Chinese controls, training selection, approved answer and collapsible real trace. The assistant controls and requested answer are bilingual; the inherited B diagnostic prose and surrounding dashboard remain English.

Training mode hides ranks/reasons, the recommended route, historical action and the counterfactual/export buttons until the user locks a candidate. This is a learning aid, not an anti-cheating exam. Retrospective type/recipient is revealed separately and is never sent to agents. Dashed gold means hypothesis; solid cream means matched historical type/recipient, not a reconstructed observed flight path. Candidate routes do not encode right/wrong colours.

Changing question, audience, language or training mode invalidates the answer. Switching snapshots discards delayed model responses. The client checks snapshot/data/candidate IDs on every returned explanation. Changing only the viewed candidate does not change the scored candidate set or the question, so it does not trigger another paid call.

## Validation and remaining work

```sh
python3 -m unittest discover -s tests -p 'test_bound_agents.py'
node --test tests/*.test.js
NODE_BINARY=node python3 -m unittest discover -s tests -p 'test_*decision*.py'
python3 scripts/evaluate_agents.py
# Optional, explicitly invokes the configured paid service:
python3 scripts/evaluate_agents.py --live > agent-evaluation.json
```

The evaluation script pairs one coordinator-only baseline with the four-role workflow on three registered matches. Dry runs mark all model results `not_run`; they do not demonstrate multi-agent superiority. Live output records explanation, elapsed time and trace; teammates must review factual support, usefulness, risks identified and latency before claiming an improvement.

Still requires account access: actual Foundry authentication/tool-call smoke test, live three-case evaluation, and cloud deployment. Unit tests use a fake transport to exercise orchestration; they are not provider acceptance tests.

## Optional cloud handoff

A Dockerfile is provided but has not been deployed. Run **one instance** behind an HTTPS reverse proxy that preserves Host, set `NEXTPLAY_PUBLIC_ORIGIN` to the exact external origin, inject model credentials as server secrets, and persist `/app/.local` for quota. Do not publish port 5173 directly to the Internet. Public-origin mode disables local Settings and legacy paid model endpoints; the canonical agent route uses the capped transport. Unsupported or cross-origin requests are rejected. Prefer authenticated/private judging access. The standard-library server is a demo server; production deployment needs a production HTTP layer, shared distributed quotas if scaled, and operator access controls.

## Match situation

The coach receives the observed score, actor-team goal margin, period and nominal regulation time remaining (excluding added time). The UI displays that background. Competition/extra-time rules, aggregate score and qualification objectives stay unknown. This enables contextual discussion of protecting a lead or chasing a deficit, but **does not turn Q2 into a win-probability or match-objective model**. Metadata is shared in full; historical action and future observations remain excluded.
