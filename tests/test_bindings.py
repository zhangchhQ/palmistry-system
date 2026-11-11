import copy
import unittest

from palmistry.engine import analyze
from palmistry.observations import ObservationError
from palmistry.render import reading_sections
from tests.test_reading import sample


class BindingTests(unittest.TestCase):
    def multiple_fates(self):
        payload=sample()
        other=copy.deepcopy(payload['images'][0]['observations'][0])
        other['id']='other_fate'
        other['geometry']['start']='life_line'
        payload['images'][0]['observations'][0]['geometry'].pop('continuity')
        payload['images'][0]['observations'].append(other)
        return payload

    def test_unbound_second_fate_cannot_be_fused_into_one_combination(self):
        result=analyze(self.multiple_fates())
        self.assertEqual(result['combinations'],[])
        self.assertTrue(result['combination_gaps'])

    def test_explicit_origin_selects_the_actual_parent(self):
        payload=self.multiple_fates()
        payload['images'][0]['observations'][1]['geometry']['origin_ref']='other_fate'
        result=analyze(payload)
        self.assertEqual({c['id'] for c in result['combinations']},{'C02'})
        self.assertEqual(result['combinations'][0]['bindings']['fate'],'other_fate')

    def test_predicates_on_different_fates_do_not_make_c05(self):
        payload=self.multiple_fates()
        payload['images'][0]['observations'][1]['geometry']['origin_ref']='demo_fate'
        result=analyze(payload)
        self.assertEqual({c['id'] for c in result['combinations']},{'C01'})

    def test_candidate_order_does_not_change_bound_combination(self):
        payload=self.multiple_fates()
        payload['images'][0]['observations'][1]['geometry']['origin_ref']='other_fate'
        before=analyze(payload)['combinations']
        payload['images'][0]['observations'].reverse()
        self.assertEqual(before,analyze(payload)['combinations'])

    def test_unique_parent_remains_compatible_with_old_inputs(self):
        result=analyze(sample())
        self.assertEqual(result['combinations'][0]['id'],'C05')
        self.assertEqual(result['combinations'][0]['connections'][0]['basis'],'unique-recognized-parent')

    def test_origin_cannot_cross_photos(self):
        payload=sample();other=copy.deepcopy(payload['images'][0])
        other['id']='other_image'
        other['observations']=[copy.deepcopy(other['observations'][0])]
        other['observations'][0]['id']='other_fate'
        payload['images'].append(other)
        payload['images'][0]['observations'][1]['geometry']['origin_ref']='other_fate'
        with self.assertRaises(ObservationError):analyze(payload)

    def test_origin_must_agree_with_named_start(self):
        payload=sample()
        payload['images'][0]['observations'][0]['geometry']['origin_ref']='demo_sun'
        with self.assertRaises(ObservationError):analyze(payload)

    def test_head_sun_combination_requires_actual_connection(self):
        payload=sample()
        payload['images'][0]['observations'][0].update(id='head',feature='head',geometry={'start':'thumb_index','path':'across_palm','direction':'descending_outer'})
        sun=payload['images'][0]['observations'][1]
        sun['geometry'].update(start='head_line',origin_ref='head')
        result=analyze(payload)
        self.assertEqual({c['id'] for c in result['combinations']},{'C06'})
        sun['visibility']='partial'
        self.assertEqual(analyze(payload)['combinations'],[])

    def test_relationship_focus_does_not_render_career_synthesis(self):
        payload=sample();payload['focus']='relationships'
        self.assertEqual(reading_sections(analyze(payload)),[])

    def test_reader_prefers_user_dominant_hand_when_both_are_supported(self):
        payload=sample();left=copy.deepcopy(payload['images'][0]);left['id']='left_image';left['user_hand']='left'
        for obs in left['observations']:obs['id']='left_'+obs['id']
        payload['images'].insert(0,left)
        sections=reading_sections(analyze(payload))
        self.assertTrue(sections)
        self.assertTrue(all(s['image_id']=='demoA' for s in sections))

    def test_short_segment_does_not_enable_year_or_money_capability(self):
        payload=sample();payload['images'][0]['observations'][0]['geometry'].update(end='palm_center',path='toward_middle')
        result=analyze(payload)
        self.assertFalse(result['capabilities']['calendar_timing_from_palm'])
        self.assertFalse(result['capabilities']['income_amount_from_palm'])
        self.assertTrue(all(c['scope']=='observed-segments' for c in result['combinations']))

    def test_overlap_and_empty_gap_remain_different_shapes(self):
        payload=sample()
        g=payload['images'][0]['observations'][0]['geometry']
        g.update(continuity='overlapping',overlap=True)
        rule_ids={r['rule_id'] for r in analyze(payload)['matches']}
        self.assertIn('F06',rule_ids)
        self.assertNotIn('F04',rule_ids)
        self.assertNotIn('F05',rule_ids)
        g['overlap']=False
        self.assertEqual(analyze(payload)['observations'][0]['status'],'unresolved')
