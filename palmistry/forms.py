"""Source-specific geometric vocabulary; catalogue labels are not predictive rules."""

import json
from importlib.resources import files


def figure_forms():
    return json.loads(files('palmistry').joinpath('data/figure_forms.json').read_text(encoding='utf-8'))


def all_forms():
    data=figure_forms()
    intros=[{'id':f"B-{r['figure']:03}",**r} for r in data['main_intro_figures']]
    return data['main_foundation_figures']+data['main_examples']+data['appendix_one']+data['appendix_two']['forms']+data['essay_figures']+intros


def get_form(identifier):
    if ':' in identifier:
        unit,_,number=identifier.partition(':')
        if number.isdigit():
            n=int(number)
            if unit=='main':
                for row in all_forms():
                    if row['id'].startswith('B-') and row.get('figure')==n:
                        return {'status':'found','record':row,'mode':'shape-definition-not-personal-forecast'}
                    if row['id'].startswith('E') and any(f['number']==n for f in row['source']['figures']):
                        return {'status':'found','record':row,'selected_figure':n,'mode':'shape-definition-not-personal-forecast'}
            mapped={'appendix1':f'A1-{n:02}','appendix2':f'A2-{n:03}','essay':f'P-{n:02}'}.get(unit)
            if mapped:
                return get_form(mapped)
    key=identifier.upper()
    for row in all_forms():
        if row['id']==key:
            return {'status':'found','record':row,'mode':'shape-definition-not-personal-forecast'}
    return {'status':'unknown','id':identifier}


def search_forms(term, limit=20):
    if not isinstance(term,str) or not term.strip():
        return []
    needle=term.strip()
    return [r for r in all_forms() if any(needle in r.get(k,'') for k in ('term','neutral_shape','neutral_definition'))][:limit]


def semantic_aliases(observations):
    """Only a few fully specified aliases are automatic. All other forms remain lookup items."""
    result=[]
    def emit(identifier,term,rows):
        result.append({'form_id':identifier,'term':term,'image_id':rows[0]['image_id'],
                       'evidence_ids':[r['id'] for r in rows], 'mode':'shape-alias-only'})
    for row in observations:
        if row['status'] not in {'recognized','descriptive'}:
            continue
        g=row['geometry']
        if row['status']=='recognized' and row['feature']=='sun':
            emit('A1-19','智慧纹（附录一，太阳线）',[row])
        elif row['status']=='recognized' and row['feature']=='fate':
            emit('A1-03','玉柱纹',[row])
        elif row['status']=='recognized' and row['feature']=='square' and g.get('region')=='moon':
            emit('A1-07','天印纹（乾宫独立方符）',[row])
        elif row['kind']=='morphology' and row['feature']=='finger_joint_marks' and g.get('region')=='finger_joints' and g.get('shape')=='parallel_bundle' and g.get('stroke_count',0)>=3:
            emit('A1-27','川字纹（附录一，指节小纹束）',[row])
    for image_id in sorted({r['image_id'] for r in observations}):
        candidates=[r for r in observations if r['image_id']==image_id and r['status']=='recognized' and r['kind']=='line']
        groups={f:[r for r in candidates if r['feature']==f] for f in ('life','head','heart')}
        if all(len(g)==1 for g in groups.values()):
            emit('A1-02','三才纹（三条主线的组合）',[groups[f][0] for f in ('life','head','heart')])
    return result
