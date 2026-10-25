# NextPlay AI — 足球决策与视频证据分析

## 项目目标与本次更新（2026-10-25）

NextPlay AI 围绕一个具体的足球问题提供分析：**在这个时刻，持球者还有哪些选择，各有什么收益和风险？**
系统用 2D 球场展示候选动作，由算法计算比较结果，再由 Agent 引用证据解释。目标是让球迷看懂选择，也为教练复盘保留可核对的数据。

| 部分 | 原有基础 | 本次新增或接通 |
| --- | --- | --- |
| A：数据 | 合成比赛、球员资料、事件和轨迹 | 独立的视频标注契约、人工确认与不可变版本；不覆盖原比赛数据 |
| B：算法 | 候选动作比较、Q2 评分、短时反事实推演 | 将人工确认的 2D 快照适配到现有计算接口，保留模型与数据来源 |
| C：Agent 与服务 | 现有分析接口 | 四角色编排、工具调用、事实引用、审核规则、调用限额与降级处理 |
| D：交互 | 比赛回放、分析界面 | 视频上传与标注、2D 分析、先选后看答案、证据定位、人工反馈 |

### 1. 上传视频 → 人工确认 → 2D 数据

新增 `/video-review.html`，流程为：

1. 上传短视频，在动作发生前暂停并截取关键帧。
2. 标记至少四个分散的球场已知点，将画面坐标转换为 105×68 米球场坐标；镜头变化后需重新校准。
3. 人工标记球员落脚点与地面球位置，确认身份、门将、进攻方向、持球者、比分及比赛时间。
4. 保存标注并确认事实，生成可导出的 2D 快照。修改会生成新版本，旧证据保留。
5. 计算动作选择、查看短时假设推演，再运行 Agent 解读和审核。

支持 MP4/WebM，单文件上限 64 MiB；浏览器声明时长上限两分钟，服务端尚不独立解码验证时长。
局部画面可以保存，但当前评分适配要求完整 22 人、双方门将及明确持球者。遮挡、红牌或小场景不能补造位置后评分。
页面提供生成式合成视频演练，使用已知标注走通流程；**它不是自动识别演示**。

### 2. 评分与推演如何接入

人工确认的快照通过适配层调用 B 的现有 `compare_actions` 和 `simulate`，比较可用的传球、带球、射门、等待等动作。
评分思路为：

```text
动作价值增益 = 成功权重 × 成功后价值
             + (1 − 成功权重) × 失败后价值
             − 当前局面价值
```

当前权重与局面价值包含工程假设，不能直接理解为已校准的真实进球概率。模型向真实视频场景迁移的准确性仍待验证。
推演画面单独标为假设，不作为真实发生的比赛事实；未知速度保留为空，仅在计算适配中使用明确的中性假设。

### 3. 四个 Agent 的职责

| Agent | 职责 |
| --- | --- |
| 进攻 Agent | 引用候选动作和数值，解释机会、线路与收益 |
| 防守 Agent | 检查拦截、丢球及对方反击风险 |
| 协调 Agent | 结合用户问题整理可读的结论 |
| 审核 Agent | 检查结论是否夸大、引用是否支持；拒绝后允许一次改写再审核 |

四个角色使用独立模型上下文，共享同一份候选动作和证据，不能修改算法评分。
工具包括 `compare_actions`、`simulate_action`，视频流程另有 `get_evidence`。
事实准备由确定性程序执行，不额外算作一次大模型调用。

未配置模型、超时、预算耗尽或重复审核失败时，保留计算结果并明确降级，不生成伪造的成功记录。
已实现 Responses 工具调用编排；**尚未部署为 Foundry Agent Service**。

### 4. 事实层与审核

- 事实区分为人工观察、计算推导和模型假设，关联视频时间戳、媒体摘要、球员及标注版本。
- 解释必须引用同一快照的事实和候选动作；规则检查未知引用、未来时间、结构化数字及不支持的概率表述。
- 点击证据可定位原视频时间；用户可将结论标为“支持 / 缺乏支持 / 错误”，积累后续评测数据。
- 引用覆盖率不等于事实正确率。规则无法证明全部自然语言结论，目前没有教练标注基准或已验证的幻觉率。

### 5. 界面与调用管理

分析页加入球迷/分析者模式、中英文助手控制、先选择再揭示排序的训练模式，以及可展开的模型/工具调用记录。
继承的部分算法诊断与主界面仍为英文，并非全站完成翻译。
服务端重新计算候选集合并拒绝过期结果；默认每日最多 100 次模型请求，失败请求也计入，同一轮分析可能多次请求。
密钥保留在服务端；调用次数限额不是金额预算上限。

## 本地运行

```sh
python3 server.py
# 比赛回放与决策分析：http://127.0.0.1:5173/
# 视频人工标注实验室：http://127.0.0.1:5173/video-review.html
```

无需模型 API 也可体验计算评分和标注流程。运行模型角色时，参考 `.env.example` 设置服务端环境变量：

- `NEXTPLAY_MODEL_BASE_URL`：支持 Responses 工具调用与结构化输出的服务地址。
- `NEXTPLAY_MODEL`：模型部署名称；Azure 使用部署名。
- `NEXTPLAY_MODEL_API_KEY`：服务密钥，仅在本机或云端秘密配置中填写。
- `NEXTPLAY_DAILY_MODEL_CALLS`：每日模型请求次数限制。

服务不会自动读取 `.env` 文件；完整配置见 [C/D 接线说明](docs/cd-integration.md)。
密钥、上传视频、本地标注和大型部署 ZIP 均不随仓库发布。

## 验证与当前边界

本次本地验证通过 143 项 Python 测试、32 项 JavaScript 测试及视频契约验证。
覆盖标注转换、上传/视频流、评分接线、引用规则、Agent 编排和打包；模型测试使用模拟服务，浏览器演练使用合成视频。

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.js
node scripts/validate_video_review.mjs
```

测试需要 Node.js；契约验证还需安装 `package.json` 中的开发依赖。
尚待完成：真实授权视频的人工精度验证、真实 Foundry 工具调用、线上部署及教练标注评测。
当前没有自动球员追踪/CV，也没有经验证的比分策略或获胜概率模型。

## Azure 与队友联调

已添加 F1 试用部署模板、部署预览脚本、启动脚本、打包工具和 `/healthz`。
**目前尚未实际部署 Azure 或开通模型服务**。云端默认关闭视频上传和模型调用；F1 是否可用及免费额度以实际账号为准，Foundry 调用单独计费。
视频功能目前面向本地原型，公开部署前还需补多用户认证与数据保留机制。

| 文档 | 队友可以查看什么 |
| --- | --- |
| [视频整合与分工](docs/video-integration.md) | A/B/C/D 职责、数据边界、流程和接口 |
| [C/D 接线](docs/cd-integration.md) | 模型配置、四角色编排、训练模式与评测 |
| [原数据审查](docs/source-data-review.md) | 生成器问题、回传偏高等后续改进依据 |
| [Azure 部署](docs/azure-deployment.md) | 注册完成后的部署步骤与费用边界 |
| [视频输入契约](contracts/video-review.schema.json) | 人工标注字段和联调约束 |

下面保留原有模块文档；其中 2026-10-23 在线演示属于历史版本，不包含本次视频证据流程。当前入口和限制以上述说明为准。

---

# Touchline — NextPlay League 2026/27 replay and squad explorer

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

A football data demo with a dependency-free Python runtime for match replay, event consumption, live statistics and squad browsing. Club, player and venue names are fictional aliases. Squad sizes, shirt numbers and all other roster attributes are retained; every match result, event and tracking frame is procedurally generated.

## 数据契约 Schema

完整约定、字段入口与联调说明见 [contracts/README.md](contracts/README.md)。
`schema.json` 覆盖现有比赛、球员、来源属性、事件与轨迹；`contracts/schema.json`
定义带数据版本/种子的快照、模拟画像和分析请求/响应。三个固定案例位于
`tests/fixtures/contracts/`，契约测试已接入 `npm test`。

```sh
npm ci
npm run test:contract
npm run validate:schema
```

这些是供后续接口接线使用的契约和样本，现有 HTTP API 尚未切换到新响应格式。

## Sofascore player attributes

Each of the 566 players in `data/league/squads.json` now has a `sofascore`
profile collected from the official rendered player pages on 23 October 2026.
The snapshot contains 472 complete radars: 435 outfield and 37 goalkeeper radars.
Height is available for 561 players and preferred foot for 563. The other 94
players have no visible radar values. None of the inspected pages supplies weight;
`weight_kg` is reserved and remains `null`. No missing values are estimated.
See `artifacts/sofascore-coverage.json` for per-player gaps and source conflicts.

| Field | Meaning |
| --- | --- |
| `attributes` (outfield) | ATT attacking, DEF defending, CRE creativity, TEC technical, TAC tactical; observed scores from 0 to 100 |
| `attributes` (goalkeeper) | SAV saves, ANT anticipation, TAC tactical, BAL ball distribution, AER aerial; kept separate from outfield scores |
| `height_cm`, `weight_kg` | Observed measurements with explicit units, or `null` |
| `preferred_foot` | `left`, `right`, `both`, or `null` |
| `source_position`, `source_nationality`, `source_shirt_number`, `source_date_of_birth` | Source observations, without overwriting the original roster fields |
| `status`, `missing_fields` | `complete` requires five applicable radar values, height and preferred foot; weight is optional. `partial` preserves all available values. Failed identity checks use `needs_review`; no candidate uses `unmatched`. |
| `identity_match`, `source_conflicts` | How the player was matched and any differences from the original roster |
| `source`, `collected_at_utc`, `attribute_period`, `evidence_sha256` | Source label, observation time, default visible radar period and digest of the local capture |

The official [attribute overview explanation](https://www.sofascore.com/news/sofascores-attribute-overview-the-ultimate-tool-for-player-analysis)
describes the two radar types. These scores are descriptive indices, not action
success probabilities. The snapshot is current to collection time, so it must not
be treated as historical pre-match evidence when evaluating older matches.

Identity matching uses original names with dates of birth, or club and shirt
number, plus explicit reviews for aliases and conflicting records. The old
`api_player_id` is **not** a Sofascore ID. Six birth dates disagree with the original
roster; both dates are preserved and the conflicts are recorded. One local
defender is a goalkeeper on the source page; consumers must check `attribute_kind`
and `source_conflicts.position` before using that profile.

To keep fictional names in shared data, real names, Sofascore IDs, page URLs,
rendered page excerpts and identity-review evidence remain in the ignored
`.local/sofascore/` directory. A fresh clone includes the imported profiles and
coverage report, but not these local identity records. The evidence digest links
each profile to its capture without publishing the name-to-source mapping.
Existing retained IDs and demographic attributes still make this pseudonymized
data, not irreversible anonymization.

Reimport the captured pages locally with:

```sh
python3 import_sofascore.py
python3 -m unittest discover -s tests -p 'test_sofascore.py'
```

The importer accepts `--capture`, `--identities`, `--squads` and `--report` paths.
The capture is a JSON object with a `players` array; each entry provides
`local_player_id`, official `url`, `title`, UTC `fetched_at`, rendered `general`
and `radar` text, and the observed roster club/shirt or explicit review evidence.
It checks page IDs, identity, units and radar ranges before adding the profile.
An incomplete refresh never erases previously collected fields. The import is
idempotent and preserves every existing roster field.

`generate.py` carries the profile into starters, substitutes and new match
metadata, including after substitutions. Generator v2.3 uses the five applicable
radar attributes to adjust the probability of choosing a legal action.

### Player-dependent action probabilities

The policy first builds legal pass, carry and foot-shot candidates using pitch
position, pressure, passing lanes and offside restrictions. It then multiplies
their existing weights by a fitted action-class intercept and a bounded player
style factor, and normalizes to probabilities. Each decision record includes
these probabilities; metadata records the policy revision, multipliers and style
strength. The RNG seed still determines a reproducible sequence.

- Higher ATT favors shots; higher CRE and TAC favor passing; higher TEC favors
  carrying. DEF adds a conservative passing tendency. These are explicit style
  hypotheses with coefficients in `realism/player_actions.py`, not measured
  causal effects of Sofascore ratings.
- Every style multiplier stays between `exp(-0.6)` and `exp(0.6)`. Missing or
  incompatible radar values contribute a neutral factor. A goalkeeper uses only
  the relevant BAL/TAC/ANT tendencies and cannot acquire a shooting candidate.
- Preferred foot, height and weight remain available as data. This ground-pass,
  foot-shot policy has no calibrated weak-foot or aerial model, so it does not
  invent effects from those fields. Pass-completion and shot-conversion models
  remain separately calibrated and unchanged.
- Receiving a pass now leads to another action decision. The former unconditional
  carry after every pass biased the event mix toward carries. Mandatory restart
  carries are explicitly tagged and excluded from action-choice validation.

`realism/player-action-profile.json` stores global intercepts fitted to the 16
existing real training matches and 10 complete synthetic matches covering all 20
clubs. The reference is StatsBomb's pinned 2022 World Cup sample. Eight real test
matches and 20 different simulator seeds evaluate the frozen model; neither
selects its parameters. The report also runs the same seeds with the old policy
and with neutral player attributes. Runtime selection uses probabilities, without
event quotas or feedback from future events.

Reproduce fitting and validation (downloads only missing **pinned** files):

```sh
python3 -m realism.calibrate_player_actions --download --workers 4
python3 -m unittest discover -s tests -p 'test_player_actions.py'
```

See `artifacts/realism/player-action-validation.json` for the action shares,
training iterations, per-match results, source checksums and disjoint seed lists.
The 20 validation matches contain 45,506 eligible actions:

| Action | Former policy | Player-attribute policy | Real test matches |
| --- | ---: | ---: | ---: |
| Pass | 35.50% | 45.92% | 46.08% |
| Carry | 62.68% | 53.07% | 52.93% |
| Shot | 1.82% | 1.01% | 0.99% |

The largest absolute gap is 0.154 percentage points. Neutralizing player style
with the same fitted intercepts gives 48.54% passes, 50.67% carries and 0.78%
shots, confirming that the profiles affect selection. This ablation does not
validate the correctness of any individual player's style. A separate complete
match passes 30,001-frame motion and event-consistency checks; see
`artifacts/realism/player-action-stream-validation.json`.

Acceptance limits are absolute differences of 1.5 percentage points for passing
and carrying and 0.35 points for shooting, set before validation. The denominator
contains only modeled ground passes, carries and foot shots; this does not
establish realistic shares for crosses, tackles, fouls or other unsupported
actions, nor realistic action counts per minute. It is a World Cup reference,
not Premier League validation.

New matches use the fitted policy by default. On 24 October 2026 the local
40-match league, single-match sample and browser demonstration were regenerated
with this policy. Fixtures, seeds and the 566-player roster were retained;
results, standings, tracking, heatmaps and analysis were recomputed. The hosted
website is a separate deployment. For controlled
comparisons, `Match(..., attribute_actions=False)` selects the former policy;
`attribute_strength=0.0` keeps the new flow and fitted intercepts but neutralizes
player-style effects. Changing the radar coefficients or roster composition
requires refitting and rerunning validation.

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

`data/league/squads.json` contains 20 fictional clubs and 566 pseudonymous players, including shirt number, position, detailed position, nationality, date of birth and age at 2026-10-19.

Sources:

- [Premier League 2026/27 squad lists](https://www.premierleague.com/en/news/4706139/see-all-the-202627-premier-league-squad-lists) (3 September 2026)
- [Premier League 2026/27 squad numbers](https://www.premierleague.com/en/news/4725682/all-20-premier-league-clubs-squad-numbers-for-202627-season) (22 September 2026)

The links above document the original roster attributes, not the fictional names. Names use stable aliases such as Aster FC and Aster Player 01. Positions, nationalities, dates of birth, ages, shirt numbers, ratings and colours are preserved exactly, as are roster order and internal IDs (including legacy API IDs). This is display-identity pseudonymization, not irreversible anonymization. The checked-in roster and generator both use the fictional names; existing match reports and the compact public demo use the same aliases. Match results, events and tracking were not regenerated. No original-name mapping is shipped.

`tests/test_fictional_data.py` checks the pre-migration digest of every non-name roster attribute, generator/roster consistency, and names and report fingerprints across the archive and public demo. Attribute changes made intentionally in the future require reviewing that baseline.

## Repository layout

```text
data/league/
├── league.json              # clubs, fixtures, results, table, scorers, summary
├── fixtures.jsonl           # one JSON fixture per line
├── standings.json           # league table
├── squads.json              # 20 fictional 2026/27 squads
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
- `metadata.json` maps `HOME`/`AWAY` to fictional clubs and includes player names, shirt numbers, positions and squad status.
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

`validate.py` checks a single match: 5 Hz continuity, identities, pitch bounds, velocity/acceleration limits, ball attachment, event causality, goals, statistics and state snapshots. `validate_league.py` checks the 20-club schedule, every match's summary/events/states/preview, the table, scorer totals and that match lineups come from the fictional squad file.

## Limitations

This is a demo, not a professional football model. It does not model offsides, a complete foul/referee system, physical collisions, fatigue or full ball physics. Cards and substitutions follow a deterministic demo script; substitutes inherit the outgoing formation slot; pressure is a proximity heuristic. Match outcomes are heuristic and are not calibrated to real football distributions. Use the label **simulated match data** whenever presenting scores, distances or tactical explanations.

The original 2026/27 roster attributes are sourced from the Premier League; club, player and venue names are fictional. Match events, tracking and results are generated and are not official competition data.

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
The local league archive now uses generator v2.3 and the player-attribute policy.
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

The `data/league-validated/` dataset mirrors the refreshed 40-match main league.
Open `/coach.html?dataset=validated` to analyze the same matches with the full
decision records. `public-demo/data.json` contains curated moments from this run.

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

## Integrated current-generator Decision analysis

Open the main dashboard, select a match, then **Analysis → Decision analysis**.
The report/player-performance view remains available in **Match report**.
A direct link is `/?match=PL26-W01-MCI-CHE&view=stats&analysis=decisions`.

This module ports Hackthon `84251bb` onto this repository's `96d13a` generator
source. All match/replay/report data comes from the current `data/league`;
there is no legacy B match dataset switch. Source hashes are checked before
reusing the same-source fitted xT/baselines, and all decisions were re-scored
with the new version binding. No match simulator was re-run.

The model is B's two-step Q2 with tactical probability assumptions and a fitted
12×8 xT tail, not FQI or a learned individual-skill policy. The main table shows
rank, reason and risk. The explicit diagnostics contract exposes all 30 features,
branch probabilities, Q1/Q2 decomposition and Softmax preference shares for future
Agent integration; these are research estimates, not real-football probabilities.
Observed radar attributes and simulated foot settings stay separate and do not
become unvalidated personal execution multipliers.

Representative decisions rotate players, teams, pitch zones and possession
sequences. All decisions and largest losses are separate scopes. Unsupported
states have no fabricated score. Missing historical carry intent stays unknown.

A separate **Counterfactual lab** supports every ranked pass, carry and shot.
Passes reuse A's existing four-scenario loop; carries/shots add explicitly
simplified bounded movement/contact hypotheses. Scenario frequencies are not
probabilities, playback is not observed future, and playback never changes ranking
or source files. It stops at the current period boundary. Replay and both new views
share one pitch renderer and the original team palette.

Existing `/api/decision`, `/api/rollout`, report and Agent APIs retain their
meaning. New endpoints use `/api/decision-analysis/`; the original canonical
rank/text-only schema remains unchanged. The new versioned metrics/counterfactual
extension, tool catalog and real JSON examples are documented in
[the dedicated integration contract](contracts/decision-analysis/README.md).
No live language-model agent is configured by this integration.

See [implementation notes](docs/decision-analysis-integration.md) and
[validation results](docs/decision-analysis-validation.md). Runtime only needs
Python 3.9+. Restart the Python server after upgrading code.

## C / D: evidence-bound replay coach

Open **Analysis → Decision analysis** for the integrated question, four-role explanation, training selection and B counterfactual flow. See [C/D integration and Foundry setup](docs/cd-integration.md) for architecture, private server configuration, test commands and deployment handoff. Without model credentials, computed comparisons still work and the service reports `model_unavailable`.

## Human-confirmed video evidence

Open **Video evidence lab** at `/video-review.html` to upload an authorized MP4/WebM clip, annotate pitch landmarks and all visible players, confirm a moment, and reuse Q2 comparison, hypothetical rollout and evidence-audited model explanations. The included walkthrough generates synthetic video; no automatic video recognition is claimed. See [video workflow and A/B/C/D handoffs](docs/video-integration.md), [the video annotation contract](contracts/video-review.schema.json), and [Azure trial deployment](docs/azure-deployment.md). Missing observations block scoring; uploaded videos and human labels stay outside public assets and deployment packages.
