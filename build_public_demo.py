"""Build a compact, secret-free browser demonstration from synthetic snapshots."""
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def build():
    out=ROOT/'public-demo';out.mkdir(exist_ok=True)
    matches=[];parity=[]
    for folder in sorted((ROOT/'data/league-validated/matches').iterdir()):
        meta=json.loads((folder/'metadata.json').read_text())
        with (folder/'decisions.jsonl').open() as stream: records=[json.loads(line) for line in stream]
        with (folder/'events.jsonl').open() as stream: events={e.get('action_id'):e for e in map(json.loads,stream) if e['type'] in ('pass','carry','shot')}
        picked={}
        for kind in ('pass','carry','shot'):
            for d in [r for r in records if r['selected']['kind']==kind][:2]:picked[d['decision_id']]=d
        for t in (1200,3000,5000):
            valid=[d for d in records if d['snapshot']['in_play'] and d['action_id'] in events]
            if valid:
                d=min(valid,key=lambda d:abs(d['t_ms']-t*1000));picked[d['decision_id']]=d
        cases=[{'record':d,'event':events.get(d['action_id'])} for d in sorted(picked.values(),key=lambda d:d['t_ms']) if d['snapshot']['in_play']]
        matches.append({'match_id':folder.name,'metadata':meta,'cases':cases})
    (out/'data.json').write_text(json.dumps({'synthetic':True,'selection':'Up to nine curated moments per match; not full-match video or all decisions.','matches':matches},ensure_ascii=False,separators=(',',':')))
    shutil.copyfile(ROOT/'decision/value-model.json',out/'value-model.json')
    shutil.copyfile(ROOT/'realism/profile.json',out/'rates.json')
    shutil.copyfile(ROOT/'coach.css',out/'coach.css')
    html=(ROOT/'action-review.html').read_text().replace('action-review.js?v=1','app.js?v=1')
    html=html.replace('<a href="coach.html?dataset=validated">← 回放分析</a>', '<a href="https://github.com/Jolinsjhp/NextPlay-AI">GitHub 源码</a>')
    html=html.replace('artifacts/realism/outcome-value-validation.json','value-model.json').replace('realism-validation.html','validation.html')
    html=html.replace('合成回放样例 ·', '在线交互演示 · 40 场合成比赛的精选时刻 · 浏览器本地计算，无需密钥 ·')
    controls='<div class="controls"><button id="play-hypothesis" disabled>播放所选传球的假设推演</button><select id="hypothesis-case" aria-label="防守反应假设"><option value="quick">快速反应 0.1秒</option><option value="baseline" selected>基准反应 0.3秒</option><option value="delayed">延迟反应 0.65秒</option><option value="wide_error">落点偏移 1.5米</option></select><button id="reset-hypothesis">返回动作前快照</button></div><p id="hypothesis-status" role="status">推演只支持合法地面传球；四个情形不是成功率采样。</p>'
    html=html.replace('<div class="metrics">',controls+'<div class="metrics">')
    html=html.replace('</main>', '<footer style="margin:36px 0;color:#b5c7be"><p>数据与模型训练参考：StatsBomb Open Data。场景为合成比赛；动作排名仍含未验证假设。</p><a href="https://github.com/hudl/open-data"><img src="statsbomb-logo.png" alt="StatsBomb" style="width:170px;max-width:55%;padding:12px;background:white;border-radius:8px"></a></footer></main>')
    (out/'index.html').write_text(html)
    # Remove machine-specific paths and large local-only audit download links from this copy.
    report=(ROOT/'realism-validation.html').read_text().replace('action-review.html','index.html').replace('coach.html?dataset=validated','index.html').replace('coach.html?realism=1','index.html')
    import re
    report=re.sub(r'<a href=[\"\']artifacts/[^>]+>.*?</a>','<span>完整审计文件见 GitHub 的 artifacts/realism 目录</span>',report)
    (out/'validation.html').write_text(report)
    print(json.dumps({'matches':len(matches),'moments':sum(len(m['cases']) for m in matches),'data_bytes':(out/'data.json').stat().st_size}))

if __name__=='__main__':build()
