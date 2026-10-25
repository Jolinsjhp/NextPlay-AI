"""Hard provenance checks plus explicit, human-labelled evaluation. Not a truth oracle."""
import math
import re
from contracts.model import digest

CLAIM_SCHEMA = dict(type='object',properties={
    'text':dict(type='string'), 'cited_evidence_ids':dict(type='array',items=dict(type='string')), 'approved':dict(type='boolean'),
    'claims':dict(type='array',items=dict(type='object',properties={
        'text':dict(type='string'), 'evidence_ids':dict(type='array',items=dict(type='string')),
        'fact_ids':dict(type='array',items=dict(type='string')), 'player_ids':dict(type='array',items=dict(type='string')),
        'action_id':dict(anyOf=[dict(type='string'),dict(type='null')]),
        'certainty':dict(type='string',enum=['observation','estimate','hypothesis']),
        'quantities':dict(type='array',items=dict(type='object',properties={
            'fact_id':dict(type='string'),'value':dict(type='number'),'unit':dict(type='string')},
            required=['fact_id','value','unit'],additionalProperties=False))},
        required=['text','evidence_ids','fact_ids','player_ids','action_id','certainty','quantities'],additionalProperties=False))},
    required=['text','cited_evidence_ids','approved','claims'],additionalProperties=False)

POLICY = '''This input is manually annotated video (or an explicitly synthetic walkthrough), not automatic tracking.
The evidence preparer has built claim_context. Use only these facts and B's comparison. Never infer unseen players or body orientation.
Return the required claims array; text MUST equal the claim texts joined with one space.
Every claim needs evidence_ids. Every numeric value in prose needs a quantities entry with an exact fact_id/value/unit.
Never emit percentages or success probabilities. Q2 ranks and xT are transferred, unvalidated model estimates.
Only use listed player IDs, action IDs, and observed time/score. Unknown remains unknown.
certainty=observation is permitted only for observed facts; calibrated coordinates are estimates and future scenarios are hypotheses.
Do not infer a pass's actual result. A reviewer approves only if draft claims are supported and do not exaggerate.'''


def audit_note(note, public, claim_context, active_ids, video_ms):
    if not isinstance(note,dict) or set(note)!={'text','cited_evidence_ids','approved','claims'}:raise ValueError('Structured claims required')
    if type(note['approved']) is not bool:raise ValueError('Invalid approval flag')
    claims=note['claims']
    if not isinstance(claims,list) or not 1<=len(claims)<=10:raise ValueError('Expected 1–10 cited claims')
    allowed_evidence={e['evidence_id'] for e in public['evidence']};actions={a['action_id'] for a in public['candidates']}
    facts={f['fact_id']:f for f in claim_context['facts']};covered=0
    for claim in claims:
        if not isinstance(claim,dict) or set(claim)!={'text','evidence_ids','fact_ids','player_ids','action_id','certainty','quantities'}:raise ValueError('Invalid claim fields')
        text=claim['text']
        if not isinstance(text,str) or not 1<=len(text)<=1200 or re.search(r'[%％]',text):raise ValueError('Invalid prose or forbidden probability percentage')
        for field,allowed in (('evidence_ids',allowed_evidence),('fact_ids',set(facts)),('player_ids',set(active_ids))):
            if not isinstance(claim[field],list) or any(not isinstance(x,str) for x in claim[field]) or not set(claim[field])<=allowed:
                raise ValueError('Unregistered claim reference: '+field)
        if not claim['evidence_ids']:raise ValueError('Every claim needs evidence')
        covered+=1
        if claim['action_id'] is not None and claim['action_id'] not in actions:raise ValueError('Action outside bound candidate set')
        if claim['certainty'] not in ('observation','estimate','hypothesis'):raise ValueError('Invalid certainty')
        for fid in claim['fact_ids']:
            f=facts[fid]
            if f.get('source',{}).get('video_ms',video_ms)>video_ms:raise ValueError('Future observation leakage')
            if claim['certainty']=='observation' and f['kind']!='observed':raise ValueError('Model output or derived coordinates labelled observed')
        if claim['certainty']=='observation' and not claim['fact_ids']:raise ValueError('Observed claims need observed facts')
        if re.search(r'\b[HA]\d{2}\b',text) and not set(re.findall(r'\b[HA]\d{2}\b',text))<=set(claim['player_ids']):raise ValueError('Unlisted player in prose')
        if not isinstance(claim['quantities'],list) or len(claim['quantities'])>10:raise ValueError('Invalid quantities')
        numbers=[]
        for quantity in claim['quantities']:
            if not isinstance(quantity,dict) or set(quantity)!={'fact_id','value','unit'}:raise ValueError('Invalid quantity')
            fid=quantity['fact_id'];fact=facts.get(fid);value=quantity['value']
            if (not fact or fid not in claim['fact_ids'] or type(value) not in (int,float) or not math.isfinite(value)
                or type(fact['value']) not in (int,float) or value!=fact['value'] or quantity['unit']!=fact['unit']):
                raise ValueError('Number has no exact model/observation source')
            numbers.append(value)
        # Player IDs are entities, not numerical claims. Free textual jersey numbers must have a fact.
        stripped=re.sub(r'\b[HA]\d{2}\b','',text)
        for token in re.findall(r'(?<![\w])[-+]?\d+(?:\.\d+)?',stripped):
            if float(token) not in numbers:raise ValueError('Unsupported number in prose')
    combined=' '.join(c['text'] for c in claims)
    if note['text']!=combined:raise ValueError('Free prose must not bypass claim-level auditing')
    cited=note['cited_evidence_ids']
    if not isinstance(cited,list) or any(not isinstance(x,str) for x in cited) or set(cited)!={x for c in claims for x in c['evidence_ids']}:
        raise ValueError('Top-level citations must match claim citations')
    return dict(ok=True,claims=len(claims),cited_claims=covered,citation_coverage=covered/len(claims),
                human_factual_accuracy=None,semantic_support='requires model/human review',
                explanation_id=digest(dict(candidate_set_id=public['candidate_set_id'],text=combined,claims=claims)))


def human_metrics(labels):
    reviewed=[x for x in labels if x['verdict'] in ('supported','unsupported','incorrect')]
    return dict(reviewed_claims=len(reviewed),unsupported_or_incorrect_rate=(sum(x['verdict']!='supported' for x in reviewed)/len(reviewed) if reviewed else None),
                note='Human-labelled claims only; citation coverage is not a hallucination-rate estimate.')
