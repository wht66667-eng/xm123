"""fox: deterministic score planning for equal-weight, all-or-nothing marking."""
from decimal import Decimal, InvalidOperation

def correct_count(target_score, points_per_question, total):
    try:
        target, points = Decimal(str(target_score)), Decimal(str(points_per_question))
    except InvalidOperation:
        raise ValueError('分数和每题分值必须是数字') from None
    if not target.is_finite() or not points.is_finite() or points <= 0 or target < 0:
        raise ValueError('目标分数必须非负，每题分值必须大于零')
    n = target / points
    if n != n.to_integral_value() or n > total:
        raise ValueError('目标分数必须是每题分值的整数倍，且不能超过本卷满分')
    return int(n)

def build_plan(questions, lookup, target_score, points_per_question=1):
    n = correct_count(target_score, points_per_question, len(questions))
    plan=[]
    for i,q in enumerate(questions):
        options=[str(o['id']) for o in q.get('optionList',[])]
        answer=lookup(q['id'])
        if not answer:
            raise ValueError(f'第 {i+1} 题缺少题库答案，未生成计划')
        right=set(str(answer).split(','))
        if not right or not right.issubset(options):
            raise ValueError(f'第 {i+1} 题的题库选项已失效')
        chosen=[o for o in options if o in right]
        if i>=n:
            wrong=next((o for o in options if o not in right),None)
            if wrong: chosen=[wrong]
            elif len(chosen)>1: chosen=chosen[:-1]
            else: raise ValueError(f'第 {i+1} 题没有可用的不同答案，不能控分')
        plan.append(dict(questionId=q['id'],answerIds=','.join(chosen),plannedCorrect=i<n))
    return plan
