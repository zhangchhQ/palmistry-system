import copy
import json
from pathlib import Path
import unittest

from palmistry.engine import analyze, lookup
from palmistry.forms import all_forms, figure_forms, get_form
from palmistry.render import render


def payload():
    return json.loads((Path(__file__).resolve().parents[1]/'examples/synthetic-cooperation.json').read_text())


class FormTests(unittest.TestCase):
    def test_numbered_example_and_figure_scopes_are_separate(self):
        data=figure_forms()
        self.assertEqual([r['example'] for r in data['main_examples']],list(range(1,165)))
        figures={f['number'] for r in data['main_examples'] for f in r['source']['figures']}
        self.assertNotIn(201,figures)
        self.assertEqual(figures|{201},set(range(94,261)))
        self.assertEqual(data['coverage']['numbered_diagram_groups'],516)

    def test_sun_health_boundary_does_not_shift_all_examples(self):
        self.assertEqual(get_form('E105')['record']['family'],'sun')
        self.assertEqual(get_form('E106')['record']['family'],'health')
        self.assertEqual(get_form('E106')['record']['source']['figures'][0]['number'],202)
        self.assertEqual(get_form('main:201')['record']['neutral_shape'],'健康线基本路径，无单独例号')

    def test_all_appendix_items_have_locations(self):
        data=figure_forms()
        self.assertEqual(len(data['appendix_one']),72)
        self.assertEqual(len(data['appendix_two']['forms']),174)
        for row in data['appendix_one']+data['appendix_two']['forms']:
            location=row['source']['reviewed_location']
            self.assertIn(location['side'],{'left','right'})
            self.assertIn(location['pdf_page'],range(1,170))

    def test_contextual_ancient_shapes_are_not_collapsed(self):
        a=get_form('appendix1:27')['record']
        self.assertIn('指节',a['neutral_definition'])
        self.assertIn('太阳线',get_form('A1-19')['record']['neutral_definition'])
        self.assertNotEqual(get_form('A1-17')['record']['neutral_definition'],get_form('A1-18')['record']['neutral_definition'])
        self.assertNotEqual(get_form('A1-39')['record']['neutral_definition'],get_form('A1-40')['record']['neutral_definition'])
        self.assertNotEqual(get_form('A1-49')['record']['neutral_definition'],get_form('A1-69')['record']['neutral_definition'])

    def test_structural_lookup_is_not_an_automatic_prediction(self):
        result=get_form('A1-64')
        self.assertEqual(result['mode'],'shape-definition-not-personal-forecast')
        self.assertEqual(get_form('A1-99')['status'],'unknown')
        self.assertEqual(lookup('千金纹')['status'],'shape-only')
        self.assertTrue(lookup('千金纹')['shape_matches'])

    def test_short_fate_segment_can_end_at_heart_with_known_direction(self):
        p=payload();g=p['images'][0]['observations'][0]['geometry']
        g.update(end='heart_line',path='toward_middle')
        result=analyze(p)
        self.assertEqual(result['observations'][0]['status'],'recognized')
        del g['path']
        self.assertEqual(analyze(p)['observations'][0]['status'],'unresolved')

    def test_short_sun_segment_still_requires_confirmed_direction(self):
        p=payload();g=p['images'][0]['observations'][1]['geometry']
        g.update(end='palm_center',path='toward_ring')
        self.assertEqual(analyze(p)['observations'][1]['status'],'recognized')
        g['path']='toward_middle'
        self.assertEqual(analyze(p)['observations'][1]['status'],'unresolved')

    def test_square_alias_needs_region(self):
        p=payload();p['images'][0]['observations']=[{'id':'sq','kind':'symbol','feature':'square','visibility':'clear','basis':'observed','geometry':{'independent':True,'closed':True,'edge_count':4}}]
        self.assertEqual(analyze(p)['shape_aliases'],[])
        p['images'][0]['observations'][0]['geometry']['region']='moon'
        self.assertEqual(analyze(p)['shape_aliases'][0]['form_id'],'A1-07')

    def test_chuan_alias_needs_finger_joint_bundle(self):
        p=payload();obs={'id':'chuan','kind':'morphology','feature':'finger_joint_marks','visibility':'clear','basis':'observed','geometry':{'shape':'parallel_bundle','stroke_count':3,'region':'finger_joints'}}
        p['images'][0]['observations']=[obs]
        self.assertEqual(analyze(p)['shape_aliases'][0]['form_id'],'A1-27')
        obs['geometry']['region']='plain'
        self.assertEqual(analyze(p)['shape_aliases'],[])
        obs['geometry']['region']='finger_joints';obs['visibility']='partial'
        self.assertEqual(analyze(p)['shape_aliases'],[])

    def test_back_tendons_need_back_view(self):
        p=payload();p['images'][0]['observations']=[{'id':'back','kind':'morphology','feature':'back_tendon_pattern','visibility':'clear','basis':'observed','geometry':{'shape':'curved'}}]
        self.assertEqual(analyze(p)['observations'][0]['status'],'unresolved')
        p['images'][0]['view']='back'
        self.assertEqual(analyze(p)['observations'][0]['status'],'descriptive')

    def test_most_specific_combination_precedes_general(self):
        result=analyze(payload())
        self.assertEqual(result['combinations'][0]['id'],'C05')
        self.assertEqual(len(result['combinations'][0]['evidence_ids']),2)
        text=render(result)
        self.assertEqual(text.count('看到的依据：'),2)
        self.assertEqual(text.count('按传统象征读法'),1)
        self.assertIn('月丘',text)
        self.assertNotIn('PDF',text)

    def test_every_entry_identity_is_unique(self):
        records=all_forms()
        self.assertEqual(len(records),len({r['id'] for r in records}))
        self.assertEqual(len(records),514)
