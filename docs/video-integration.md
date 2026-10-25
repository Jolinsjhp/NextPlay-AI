# Manual video evidence integration

This extends the sprint document's A/B/C/D ownership without replacing its synthetic match main flow. The user explicitly added manual video intake to the scope. It is a separate research workspace at `/video-review.html`; it is not automatic CV, a calibrated real-player ability model, or proof of competition eligibility.

## Shared source baseline

- A source: `LiNTe912/NextPlay-AI` commit `96d13a377e98602c9998e3ebb82186843762febf`.
- B integration: `tigerguoyi/NextPlay-AI` commit `56b3704d71de7c43849824564fb8d3f8476e17f8`.
- These remain the generator and Q2 sources. The added `video_review` package adapts human observations into the existing comparator. No source league data, generator rule or Q2 formula is changed.

| Owner | Existing responsibility | Added video responsibility | Handoff |
|---|---|---|---|
| A | Generator, source data, fixtures, synthetic schemas | Roster/identity conventions, observed image points, human confirmations, future detection adapters | `contracts/video-review.schema.json`, immutable annotation revisions |
| B | Candidate actions, Q2/xT, rollouts, canonical contract | Review transfer assumptions, causal velocity fallback, complete-scene gate, model/claim provenance | Same `compare_actions` and `simulate` functions; new video envelope |
| C | Foundry transport, orchestration, caps and traces | Evidence preparer, typed facts, claim rule gate, human-label storage, private media endpoints | `video_review/project.py`, `audit.py`, `service.py` |
| D | Replay/coach/training UI | Upload, landmark/foot/ball annotation, confirmations, 2D view, source seeking, inline hypothesis playback, claim feedback | `video-review.html/js/css`, pure `video-review-model.js` |

A/B/C/D can work independently against the checked-in annotation fixture and HTTP contract. Changes to shared scoring semantics should still be reviewed by B. The source DOCX is an input to this implementation; it has not been silently rewritten.

## Workflow

1. Upload authorized MP4/WebM: 64 MiB maximum, browser-declared duration up to two minutes. Media is stored under the private state directory, never under static `data/` or a public upload directory. Server validation checks byte size/container signature; **it does not decode or independently verify duration**. The browser must be able to decode the video.
2. Pause before the decision and capture a frame. Match clock and video timestamp are separate values.
3. Mark at least four separated pitch landmarks using the listed known 105×68 m coordinates. The backend fits a planar homography and refuses singular layouts. Four exact points can fit perfectly even when annotated incorrectly: residual is not accuracy. At each new camera view recalibrate.
4. Mark all 22 players' ground contact positions and the ground ball. H/A IDs and jersey numbers are human mappings, not recognition. Confirm each team's goalkeeper, attacking direction, ball owner, period and observed score.
5. Check the six confirmations and save. Incomplete annotations can be saved and exported, but cannot enter Q2. The current scoring adapter supports fully observed 11v11 scenes; red-card/small-sided/occluded scenes remain annotation-only. Do not invent off-screen positions.
6. Compute candidates, optionally choose before revealing ranks, build a short hypothesis, and ask the model agents. The model key stays server-side. Without configuration the ranks/facts still work and the response says `model_unavailable`.
7. Click source links to seek to the original video timestamp; label approved claims as supported, unsupported or incorrect. These are user labels, not automatically verified coach credentials.

The synthetic walkthrough button generates a five-second video **in the browser**, uploads it through the same endpoint and loads known fixture marks. It is labelled synthetic and still requires review/confirmation. It is not a detection demo or independent evidence of real-video accuracy.

## Versioned data boundaries

`contracts/video-review.schema.json` validates the manual annotation input. Human observations retain normalized image points; derived pitch positions are separate. Each saved revision hashes the source media SHA and normalized annotation. Edits create a new immutable revision; they never overwrite old evidence. Candidates additionally bind snapshot/model/annotation provenance.

The video envelope uses `video-review-1`, not the synthetic `contract-1` match schema. In the **private B compatibility bridge**, uploaded-video metadata has `synthetic:false` (the declared synthetic walkthrough has `true`), `seed:null`, and `schema_version:video-bridge-1`. The inherited `gen-` data-version prefix is only a legacy content hash, not a claim that the video is generated. Internal one-hour period offsets prevent overlapping clocks; they are not observed half durations. `tracking_hz=1000` is a millisecond ID grid, not a measured video frame rate. Do not export this bridge as an ordinary generated match or validate it against the synthetic metadata schema.

Unknown velocities remain `null` in exported observations. B receives explicit neutral zeros where motion is unknown. With a preceding confirmed keyframe within two seconds, velocity is derived causally from past/current positions; future keyframes are never used for pre-action scoring. Implausible speed blocks scoring. Counterfactual frames are always separate hypotheses.

## Evidence preparation and review

The evidence preparer is a deterministic tool agent, not an extra paid language-model call. Its trace explicitly says `execution:deterministic_tool`. It creates typed `observed / derived / assumed` facts with media SHA, revision, player ID and video timestamp. B's unchanged model generates candidates and diagnostics.

Attack, defense, coordinator and reviewer receive the same facts/candidate set and can call `get_evidence`, `compare_actions` and `simulate_action`. For video reviews they must return structured claims, their evidence/fact/player/action IDs, certainty and any numeric quantities. A server rule gate rejects unknown references, out-of-set actions, future timestamps, unsupported structured numbers, percentage claims, derived facts mislabeled observed, and free prose that bypasses the claims array. Reviewer rejection still triggers one rewrite, then computed-only fallback.

Important limits: identity checks apply to declared IDs; numerical checks cover structured quantities and parsed numeric literals. Rules cannot prove every natural-language assertion or detect every paraphrased hallucination. The model reviewer and human labels still assess semantic support. Citation coverage is **not** factual accuracy. The exported human error rate is `null` until labelled claims exist; no coach benchmark or hallucination rate is fabricated.

## HTTP API

All routes require same-origin requests. The source directory is not accepted from the client.

| Route | Request | Response |
|---|---|---|
| `POST /api/video-review/upload` | Raw `video/mp4` or `video/webm`; optional declared `X-NextPlay-Source:synthetic_demo` | Random media ID, SHA, private same-origin media URL |
| `GET /api/video-review/media/{id}` | Optional single byte Range | Private media stream; 206/416 supported |
| `POST /api/video-review/confirm` | `{annotation}` | Immutable revision, reconstructed moments and blocking reasons |
| `GET /api/video-review/revision` | `video_id`, `revision_id` query | Saved observations, never a client-selected filesystem path |
| `POST /api/video-review/analyze` | Selection below, CID initially null | Facts, rule report, optional B diagnostics envelope |
| `POST /api/video-review/agents` | Same selection, current CID required | Canonical response inside video envelope, claims and audit |
| `POST /api/video-review/counterfactual` | `{selection,action_id}` | Existing short hypothetical scenarios |
| `POST /api/video-review/feedback` | Video/revision/explanation IDs, claim index, verdict and notes | Saved labels and human-only error metric |

Selection fields are exactly `video_id, revision_id, frame_index, question, mode, language, candidate_set_id`. Changing annotation, moment, question, selected action, audience or language invalidates stale answers in the UI. Model answers are accepted only for matching video/revision/frame/CID.

The new source data is private; `.local`, uploads, labels and keys are excluded from Git, Docker build context and Azure packaging. `NEXTPLAY_STATE_DIR` moves private storage outside the application tree. The default local upload budget is 512 MiB of media. There is no general production multi-user authentication, retention policy or malware-decoding sandbox in this prototype. Public judging mode disables video routes/uploads unless explicitly enabled by an operator; keep them disabled on an unauthenticated deployment.

## Verification

Run `python3 -m unittest discover -s tests -p 'test_video*.py'`, `node --test tests/video-review.test.js` and `node scripts/validate_video_review.mjs`. The HTTP test covers actual upload/storage/range requests and deterministic scoring; model orchestration tests use fake transport. The browser walkthrough exercises a generated video, not arbitrary real footage. A real authorized clip and human-checked positions are still needed to assess reconstruction accuracy.
