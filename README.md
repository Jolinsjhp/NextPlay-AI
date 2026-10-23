# Touchline — Premier League 2026/27 replay and squad explorer

## 分享与快速体验（2026-10-23 升级）

在线交互演示：https://nextplay-replay-coach.kclxzl2022.chatgpt.site

浏览器演示包含 40 场合成比赛的 360 个精选动作。无需账户或 API 密钥，
可比较传球、带球、射门和等待，查看实际执行结果，并播放合法传球的假设推演。
评分在浏览器本地计算；浏览器版本与 Python 版本有数值一致性检查。
它不包含收费 LLM Agent 调用，不将敏感性范围当置信区间。

本地快速运行：

```sh
python3 server.py
# 打开 http://127.0.0.1:5173/public-demo/index.html
```

完整 40 场的新轨迹和逐条决策缓存不放入 Git；它们可用下文命令重新生成。
训练后的聚合模型、源码、测试、验证摘要及精简演示数据都包含在本仓库。
StatsBomb 原始缓存及本地 API 密钥不上传。

A dependency-free football data demo for match replay, event consumption, live statistics and squad browsing. Club names, 2026/27 squad numbers and player details are real; every match result, event and tracking frame is procedurally generated.

## Frontend

The Touchline dashboard reads `data/league/` directly. No build step, CDN or third-party package is required.

```sh
# From the project root (Python 3)
python3 server.py

# Or use the npm shortcut
npm run dev
```

Open <http://127.0.0.1:5173>. Serve the folder over HTTP rather than opening `index.html` directly: the browser needs to load JSONL files and a module Worker.

### Views

The default landing page is **Home**. Choose any of the 20 clubs and click
**Set home club**; the browser remembers this choice. The simulation clock defaults
to **the start of matchweek 3 (7 November 2026)**, independently of the computer's
clock. Home shows form, results, goals, points and league position using only weeks
1–2; week 3 is the next fixture and week 4 is on the horizon. Future scores never
enter these homepage calculations. Click a past result to open its match report.
The match explorer defaults to week 3 (your club's match when selected); explicit
`?match=` links still open the requested replay. The explorer remains an archive
of all generated matches. `CURRENT_MATCHWEEK` in `club-home.js` sets the clock.

- **Select match** — filter 40 fixtures by matchweek, or use previous/next. `?match=<match_id>` deep-links a match.
- **Overview** — score, possession, shots, passing, interceptions, pressure events, event feed and player focus.
- **Replay** — smooth 5 Hz tracking for players and the ball, 1× / 4× / 10× speed, timeline scrubbing and ±10 second controls. Red cards remove players; substitutions switch to the incoming player's identity. Space toggles playback; arrow keys jump 10 seconds.
- **Analysis** — an English post-match report, first- and second-half review, match progression, Player of the Match with evidence and leading performers, plus final match statistics.
- **Lineups** — matchday XI plus substitutes, appearance status, cards and simulated distance.
- **Squads** — a new league-wide tab with all 20 clubs' 2026/27 rosters. Pick a club, search by player, position or nationality, and browse players grouped by goalkeepers, defenders, midfielders and forwards.

The replay starts at the selected match's `preview-60s.json` clip. Matches marked `tracking: "full"` continue loading the complete `tracking.jsonl` in a Web Worker; all other matches remain a 60-second preview. If full tracking fails, the preview stays usable. Selecting a match reloads its `metadata`, `summary`, `events`, `states` and `preview` files.

### Independent match-summary model service

Run `npm run dev` (or `python3 server.py`) and open **Settings**. Enter an HTTPS
Responses API base URL, model ID and API key, then save. The service must support
structured JSON output. In **Analysis**, click **Generate model summary** to write
and save a new full-match and half-by-half review for the selected completed match.
The request sends the computed match report to your configured provider and may
incur provider usage charges. Scores, statistics, evidence and Player of the Match
remain computed locally. Failed requests leave the existing report intact.

`model_service.py` owns model narration independently of `analysis_agent.py`.
`server.py` provides same-origin settings and generation APIs on loopback only.
The key is saved in `.local/model-service.json` with owner-only file permissions;
this directory is ignored by Git and blocked from static serving. Settings responses
only expose whether a key exists. Leave the key blank to retain it, or choose
**Remove saved API key**. Changing the service URL requires entering a key again.
Do not serve this directory with a generic static server after saving credentials.
Pure static hosting can still show pre-generated reports but cannot use settings
or generate new model summaries. This server is intended for local personal use.

### Post-match analysis agent

The project interface, generated reports, documentation and agent prompts are in English.
`analysis_agent.py` runs automatically from `write_match()` after each simulated match ends.
It checks the final whistle, event count, match identity and goal sequence before analysing
the entire event stream. Each match receives an `analysis.json` file, including matches
with only a 60-second tracking preview. Existing finished matches have reports too.

Open **Analysis** to read and export the final report at any replay position. A full-time
banner links to the report when the full replay finishes. A preview ending does not count
as a final whistle. Reports do not change the replay's time-filtered event feed.

The default **local evidence agent** uses deterministic English reporting and transparent
impact scoring; it is rule-based, not an LLM. It considers every player who appeared,
including substitutes and goalkeepers. Goals, non-goal shots on target, saves, interceptions,
passing and cards contribute to the award. The exact formula and tie-break order appear in
each report. Pressure tags, distance, unrecorded assists and xG are not used to infer quality
or tactical intent. These are simulated matches and the award is a demo assessment.

```sh
# Generate or refresh reports without rerunning the simulation
npm run analyze

# Analyse a single completed match
python3 analysis_agent.py data/league/matches/PL26-W01-MCI-CHE

# Explicitly regenerate cached reports
python3 analysis_agent.py --force
```

For model-written English summaries and half-by-half analysis, set `OPENAI_API_KEY` and
`OPENAI_MODEL` in the generating process's environment, then use:

```sh
python3 analysis_agent.py --mode openai

# Also use model narration automatically for newly generated matches
TOUCHLINE_ANALYSIS_MODE=openai python3 generate.py
```

Choose a model supporting the [Responses API structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).
Model mode sends the derived match evidence (including player names, statistics and event
references) to OpenAI. Credentials remain in the Python process and are never included in
browser code or reports. The model writes the narrative; the evidence, ranking and award
remain computed and auditable. Generated prose can still contain mistakes.

Reports are cached by source fingerprint, agent version, mode and model. Missing
configuration, timeout, refusal or malformed responses retain the local report with a
visible explanation. Run the same analysis command to retry. Local mode requires no
credentials, network, packages or background service.

### Squad data

`data/league/squads.json` contains 20 clubs and 566 registered players, including shirt number, position, detailed position, nationality, date of birth and age at 2026-10-19.

Sources:

- [Premier League 2026/27 squad lists](https://www.premierleague.com/en/news/4706139/see-all-the-202627-premier-league-squad-lists) (3 September 2026)
- [Premier League 2026/27 squad numbers](https://www.premierleague.com/en/news/4725682/all-20-premier-league-clubs-squad-numbers-for-202627-season) (22 September 2026)

Positions, nationalities and dates of birth were cross-checked against the Premier League player directory. Match lineups are selected from each club's real squad by position, then supplemented with substitutes. The match simulation still determines results, events, cards and tracking.

## Repository layout

```text
data/league/
├── league.json              # clubs, fixtures, results, table, scorers, summary
├── fixtures.jsonl           # one JSON fixture per line
├── standings.json           # league table
├── squads.json              # 20 real 2026/27 squads
├── validation_report.json   # league consistency report
└── matches/
    └── PL26-W01-MCI-CHE/
        ├── metadata.json
        ├── summary.json
        ├── analysis.json    # English report, award, ranking and source evidence
        ├── events.jsonl
        ├── states.jsonl
        ├── preview-60s.json
        └── tracking.jsonl   # only for featured/full matches

data/                      # legacy single-match example used by validate.py/package.py
index.html
styles.css
app.js
core.js
tracking-worker.js
generate.py
analysis_agent.py
validate.py
validate_league.py
package.py
schema.json
```

## Generate the league

The default league is 20 clubs × 4 matchweeks × 10 matches = 40 fixtures. Every club plays once per matchweek and ends with 2 home / 2 away matches.

```sh
# Default: 4 matchweeks, full tracking for the marquee match of each week
python3 generate.py

# Change the number of matchweeks (1-19) or the tracking scope
python3 generate.py --weeks 4 --tracking featured
python3 generate.py --weeks 4 --tracking all
python3 generate.py --weeks 4 --tracking none

# Add a full replay for a specific fixture
python3 generate.py --full-match PL26-W01-TOT-ARS

# Generate an alternate league with a different seed
python3 generate.py --seed 12345 --output data/league-alt
```

`--tracking` controls full 5 Hz tracking:

| Value | Meaning | Approx. size (4 weeks) |
| --- | --- | --- |
| `featured` (default) | Full tracking for the highest-rated fixture each week; 60s previews elsewhere | ~300 MB |
| `all` | Full tracking for all 40 matches | ~1.3 GB |
| `none` | No full tracking; previews, events, states and summaries only | ~190 MB |

Fixtures run from Saturday 24 October 2026 across four weekends, with local kick-off times in `Europe/London`. The schedule uses the first four rounds of a single round-robin rotation, so no pairing repeats.

## Data model

Each match keeps the existing `HOME / AWAY` stream format:

- 28 registered players per team: starters `H01–H11` / `A01–A11`, substitutes `H12–H14` / `A12–A14`.
- 22 players + 1 ball in tracking frames while nobody is sent off.
- 5 Hz sampling: 30,001 frames from `0` to `6,000,000` ms (100 simulated minutes).
- 6,001 one-second state snapshots.
- `metadata.json` maps `HOME`/`AWAY` to real clubs and includes player names, shirt numbers, positions and squad status.
- `summary.json` includes final score, statistics, goals and per-player distance.
- `events.jsonl` includes passes, carries, pressure, interceptions, shots, saves, restarts, cards, substitutions and match phases.
- `tracking.jsonl` is written only when full replay is requested.

The root `data/` folder remains the original two-team Harbor FC vs Mountain FC example. The frontend uses `data/league/`; the root data is retained for the legacy single-match validator and packaging script.

## Event generation

- `Match.emit()` — builds every event with `event_id`, `sequence`, `match_id`, `period`, `start_ms`, `end_ms`, `available_at_ms` and `possession_id`.
- `Match.finish_action()` — emits `carry`, `pass`, `interception`, `shot`, `save`, `stoppage` and `restart` events.
- `Match.step()` — emits `pressure`, `period_start`, `period_end`, `match_end` and `action_cancelled`.
- `Match.set_possession()` — emits `possession_change`.
- `Match.apply_administrative_events()` — emits yellow cards, red cards and substitutions.
- `build_summary()` — extracts goals from `shot` events with `outcome="goal"`.
- `write_match()` — writes each match's `events.jsonl`.
- `generate_league()` — creates each match and calls `write_match()`.

Events are only released when `available_at_ms <= replay time`. The replay never reveals future passes, cards, substitutions or goals.

## Validation

```sh
npm test

python3 validate.py
python3 validate_league.py
python3 validate.py data/league/matches/PL26-W01-MCI-CHE
```

`validate.py` checks a single match: 5 Hz continuity, identities, pitch bounds, velocity/acceleration limits, ball attachment, event causality, goals, statistics and state snapshots. `validate_league.py` checks the 20-club schedule, every match's summary/events/states/preview, the table, scorer totals and that match lineups come from the real squad file.

## Limitations

This is a demo, not a professional football model. It does not model offsides, a complete foul/referee system, physical collisions, fatigue or full ball physics. Cards and substitutions follow a deterministic demo script; substitutes inherit the outgoing formation slot; pressure is a proximity heuristic. Match outcomes are heuristic and are not calibrated to real football distributions. Use the label **simulated match data** whenever presenting scores, distances or tactical explanations.

Real 2026/27 squad data is sourced from the Premier League and is included for identification and demonstration. Match events, tracking and results are generated and are not official Premier League data.

### Daily calendar

The homepage includes a seven-day schedule and an expandable January calendar,
with an All clubs / My club filter. The calendar uses January 2027 within the
2026/27 season and the existing simulation clock (`CURRENT_MATCHWEEK = 3`), so
“This week” is January 11–17 rather than the computer's current week. The four
rounds occupy January 2–3, 9–10, 16–17 and 23–24, with five matches each Saturday
and Sunday. Unscheduled dates remain empty, including the final weekend.

`calendar.js` maps the source fixtures to these simulation dates at load time;
the original generated replay files remain source data. The homepage, match
picker and match header share the mapped dates. Only prior rounds show scores
and report links in the calendar. Calendar coverage and score visibility are
checked by `tests/calendar.test.js` as part of `npm test`.

### Player reports and running heatmaps

Click a player in Analysis or Lineups to open their full-time report; after the
replay reaches full time, pitch clicks open the same report. The report includes
distance, attempted/completed passes, pass accuracy, shots, shots on target,
goals, interceptions and saves. Statistics come from resolved match events and
the existing simulated distance totals.

Each match now has `heatmaps.json`: 35 × 23 occupancy bins per registered player,
aggregated from all 5 Hz on-pitch tracking intervals. Substituted and dismissed
players contribute only while present; unused players have empty maps. Colours
are normalized per player. Coordinates stay fixed across both halves, so the
map includes the half-time change of ends. These are simulated time-occupancy
maps, not estimates from event locations or the 60-second preview.

`generate.py` writes heatmaps during match generation, even when full tracking
is not saved. `python3 player_heatmaps.py` backfills existing league matches:
reads full tracking where available, otherwise reproduces the seeded simulation
and verifies preview frames, final score, distance, event count and team stats
before writing the compact artifact. No source replay or result files are changed.

## Decision Coach prototype

Open `/coach.html` using `python3 server.py` to compare candidate ground passes and play four short hypothetical defensive responses. The numerical analysis is an uncalibrated deterministic baseline, not a trained probability model. An optional four-agent Responses-compatible tool workflow is available after configuring a model in Settings; no live model execution is claimed when configuration is missing. See [decision/README.md](decision/README.md) for assumptions, endpoints, research references and remaining work.

## Real-event-calibrated generator v2.2

The generator now filters offside pass candidates, uses distance/pressure completion
priors fitted on StatsBomb footed ground passes, and scores selection using pass
geometry, lane risk, shot angle/distance and current pressure. Team ratings no
longer determine these outcome probabilities. New passes use ground trajectories only, matching the calibration population.
Shot goal frequencies are fitted by distance; other motion and ball-outcome behavior remains heuristic.

Open `/coach.html?realism=1` for the newly generated sample and
`/realism-validation.html` for before/after measurements, regressions and sources.
The existing league archive is retained; it predates this generator change.
Every newly written match also gets `decisions.jsonl`: pre-decision snapshot,
candidates, selection weights and selected action linked to the next action ID.
These are simulator records, **not expert optimal-action training labels**.

```sh
# Reproduce from cached source data (no network)
python3 -m realism.calibrate
python3 -m realism.benchmark
python3 -m realism.render_validation
# Fetch sources if needed; source revision and SHA256 saved in provenance
python3 -m realism.calibrate --download
# Write a fresh full sample without replacing the league archive
python3 generate.py --mode single --output data/realism-sample
python3 validate.py data/realism-sample
```

Source: [StatsBomb Open Data](https://github.com/statsbomb/open-data), 2022 World Cup.
32 matches: 16 fitting, 8 development, 8 final held out. Footed ground passes and
footed shots in Regular Play, periods 1–2; source 120×80 rescaled to 105×68.
Raw source data stays in ignored `.local/statsbomb`; derived profile/provenance is
in `realism/profile.json`. Follow source attribution/logo terms when publishing.
This is not Premier League calibration, tracking validation or counterfactual ground
truth. Overall backward-pass share remains too high; see the diagnostics page.
The coach's existing feasibility/utility scores remain separate uncalibrated models.

### Full new-data system audit

The separate `data/league-validated/` dataset contains a newly generated 40-match
league. Open `/coach.html?dataset=validated` to analyze those matches. It does not
replace the older archive or change the meaning of its results.

```sh
python3 generate.py --weeks 4 --tracking featured --output data/league-validated
python3 validate_league.py data/league-validated
python3 -m realism.evaluate_system
python3 -m realism.render_validation
```

The system audit runs deterministic coach analysis at every recorded decision,
checks decision/event linkage, and runs two recommended-pass rollouts per match
(four scenarios per rollout). It checks all generated post-match reports and
measures aggregate/zone-level distance, completion and backward-pass statistics.
`artifacts/realism/system-validation.json` includes source checksum verification,
real held-out Brier scores, match-level bootstrap intervals, errors and individual
match results. `system-analysis.jsonl` stores compact per-decision audit results.
LLM agents are not invoked during the batch. Previously viewed test matches are
reused for a reproducibility audit; this is not a fresh blind evaluation.

### Outcome-oriented action comparison

Open `/action-review.html` for the new decision / execution / alternatives view.
Run `python3 -m decision.train_value` to reproduce real-event outcome training.
See `decision/README.md` for which components are learned and which are assumptions.
The original pass-only coach and generator are retained. Restart the local server
after Python API edits. `TOUCHLINE_PORT=5174 python3 server.py` runs a separate
upgrade preview when the original 5173 server is already running.
