"""Attributed study records. This endpoint has no personal-observation input."""

import json
from importlib.resources import files


def study_data():
    return json.loads(files('palmistry').joinpath('data/study.json').read_text(encoding='utf-8'))


def study_lookup(query='list'):
    data=study_data()
    rows=[row for key in ('cases','lessons','shape_examples','doctrines') for row in data[key]]
    if query=='list':
        return {'mode':'study-not-personal-reading','counts':data['counts'],
                'items':[{'id':row['id'],'title':row.get('title',row.get('topic',row.get('form_id')))} for row in rows]}
    selected=[row for row in rows if query.upper()==row['id'] or query==row.get('topic') or query==row.get('form_id')]
    return {'mode':'study-not-personal-reading','status':'found' if selected else 'unknown','records':selected}
