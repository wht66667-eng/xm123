import assert from 'node:assert/strict';
import {buildScorePlan} from './web/score-plan.js';
const questions=Array.from({length:5},(_,i)=>({id:String(i),foxAnswer:'a',optionList:[{id:'a'},{id:'b'}]}));
for(const [score,count] of [[0,0],[3,2],[7.5,5]]){
  const plan=buildScorePlan(questions,score,1.5);
  assert.equal(plan.filter(x=>x.plannedCorrect).length,count);
  assert.equal(plan.filter(x=>x.answerIds==='a').length,count);
}
for(const [target,points]of [[-1,1],[6,1],[1.5,1],[1,0],['',1]])assert.throws(()=>buildScorePlan(questions,target,points));
assert.throws(()=>buildScorePlan([{...questions[0],foxAnswer:''}],0,1));
assert.throws(()=>buildScorePlan([{...questions[0],foxAnswer:'stale'}],0,1));
console.log('Score plan JavaScript tests passed');
