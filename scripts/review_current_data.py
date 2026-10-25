#!/usr/bin/env python3
"""Read-only reproducible audit of the source league; never generates matches."""
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from realism.evaluate_system import sim_rows
from realism.calibrate import summary
from realism.policy import candidates
from generate import Match
ROOT=Path(__file__).resolve().parents[1]

def audit():
    root=ROOT/'data/league'; counts=Counter(duplicate_decisions=0,decision_snapshot_mismatches=0); rows=[]; mismatches=[]; unique_failures=[]
    for folder in sorted((root/'matches').iterdir()):
        if not folder.is_dir():continue
        meta=json.loads((folder/'metadata.json').read_text());roster={p['player_id'] for p in meta['players']}
        events=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines() if line.strip()]
        counts['matches']+=1;counts['events']+=len(events);counts['full_tracking_matches']+=int((folder/'tracking.jsonl').exists())
        ids=[e['event_id'] for e in events]
        if len(ids)!=len(set(ids)):unique_failures.append(folder.name)
        for e in events:
            if e['match_id']!=folder.name or e.get('player_id') and e['player_id'] not in roster:mismatches.append([folder.name,e['event_id']])
        rows.extend(sim_rows(events))
        with (folder/'decisions.jsonl').open() as stream:
            decision_ids=set()
            for line in stream:
                if not line.strip():continue
                d=json.loads(line);counts['decisions']+=1
                if d['decision_id'] in decision_ids:counts['duplicate_decisions']+=1
                decision_ids.add(d['decision_id'])
                f=d['snapshot']
                if d['player_id']!=f['ball_owner_id'] or d['t_ms']!=f['t_ms'] or d['score']!=f['score']:counts['decision_snapshot_mismatches']+=1
    squads=json.loads((root/'squads.json').read_text());players=[p for t in squads['teams'] for p in t['players']]
    statuses=Counter(p.get('sofascore',{}).get('status','missing') for p in players)
    feet=Counter(p.get('sofascore',{}).get('preferred_foot') or 'unknown' for p in players)
    # A counterexample to a score/time-aware policy: same spatial state, changed score and clock.
    sim=Match(714);sim.owner=9;sim.possession_team=0
    before=candidates(sim);sim.score=[0,1];sim.t=5900;after=candidates(sim)
    report=json.loads((ROOT/'artifacts/realism/system-validation.json').read_text())
    return dict(source_commit='96d13a377e98602c9998e3ebb82186843762febf',counts=dict(counts),
        duplicate_event_matches=unique_failures,event_identity_mismatches=mismatches,
        recomputed_synthetic_summary=summary(rows),
        front_quarter=summary([r for r in rows if r['x']>=78.75]),
        stored_reference_summary=report['real_held_out'],stored_front_quarter_reference=report['zone_fit'][3]['real'],
        players=len(players),profile_status=dict(statuses),preferred_foot=dict(feet),
        same_geometry_changed_score_and_clock_policy_unchanged=before==after,
        reference_scope='Stored 8-match World Cup held-out aggregate, not independently re-downloaded in this audit.',
        note='Event/snapshot integrity does not establish realistic decision-making or causal player effects.')
if __name__=='__main__': print(json.dumps(audit(),ensure_ascii=False,indent=2))
