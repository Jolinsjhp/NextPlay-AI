import test from 'node:test';
import assert from 'node:assert/strict';
import {newCoachState,coachMarkup,acceptsResponse,words} from '../replay-assistant.js';
const esc=s=>String(s??'').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const doc={snapshot_id:'s',data_version:'v',candidate_set_id:'c',public:{candidates:[{action_id:'pass:H02',eligible:true,rank:1,type:'pass'},{action_id:'hold:1s',eligible:false,type:'hold'}]}};
test('English default and bilingual training flow never labels score as goal probability',()=>{
 const state=newCoachState();assert.equal(state.language,'en');state.training=true;
 let html=coachMarkup(state,doc,{},a=>a.action_id,esc);
 assert.ok(html.includes('Lock my choice'));assert.ok(!html.includes('value="hold:1s"'));assert.ok(html.includes('id="ra-run" disabled'));
 state.language='zh';html=coachMarkup(state,doc,{},a=>a.action_id,esc);assert.ok(html.includes('先选动作再比较'));assert.ok(html.includes('不是已验证'));
 state.locked='pass:H02';html=coachMarkup(state,doc,{},a=>a.action_id,esc);assert.ok(!html.includes('id="ra-commit"'));
});
test('Model answers bind snapshot, source version and complete candidate set',()=>{
 assert.ok(acceptsResponse(doc,doc));for(const field of ['snapshot_id','data_version','candidate_set_id'])assert.ok(!acceptsResponse({...doc,[field]:'old'},doc));
});
test('Question and explanation render as escaped text',()=>{
 const state=newCoachState();state.question='<script>bad</script>';
 state.response={explanation:{text:'<img src=x>',cited_evidence_ids:['<e>']},limitations:[],agent_trace:[]};
 const html=coachMarkup(state,doc,{},a=>a.action_id,esc);
 assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img src=x>'));assert.ok(html.includes('&lt;img'));
});
test('Coach event binding targets actual IDs and invalidates answers on language changes',async()=>{
 const {bindCoach}=await import('../replay-assistant.js');
 const nodes=Object.fromEntries(['ra-question','ra-result','ra-run','ra-lang','ra-audience','ra-training'].map(k=>['#'+k,{}]));
 let redraws=0;const state=newCoachState();state.response={explanation:{text:'old'}};
 bindCoach({querySelector:s=>nodes[s]||null},state,doc,{},()=>{},()=>redraws++,undefined,()=>true);
 nodes['#ra-lang'].onchange({target:{value:'zh'}});
 assert.equal(state.language,'zh');assert.equal(state.response,null);assert.equal(redraws,1);
});
