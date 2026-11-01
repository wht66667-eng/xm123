// fox: equal-weight planning; platform marking rules determine final scores.
export function buildScorePlan(questions,target,points){
  const t=Number(target),p=Number(points),count=t/p;
  if(String(target).trim()===''||String(points).trim()===''||!Number.isFinite(t)||!Number.isFinite(p)||p<=0||t<0||Math.abs(count-Math.round(count))>1e-8||count>questions.length)throw Error('目标分数须为每题分值的整数倍，且不能超过本卷满分');
  return questions.map((q,i)=>{
    const options=q.optionList.map(o=>String(o.id));
    const right=new Set(String(q.foxAnswer||'').split(','));
    if(!q.foxAnswer||[...right].some(id=>!options.includes(id)))throw Error(`第 ${i+1} 题缺失答案或选项失效，未生成控分计划`);
    let selected=options.filter(id=>right.has(id));
    if(i>=Math.round(count)){
      const wrong=options.find(id=>!right.has(id));
      if(wrong)selected=[wrong];
      else if(selected.length>1)selected=selected.slice(0,-1);
      else throw Error(`第 ${i+1} 题没有可用的不同答案，不能控分`);
    }
    return {questionId:q.id,answerIds:selected.join(','),plannedCorrect:i<Math.round(count)};
  });
}
