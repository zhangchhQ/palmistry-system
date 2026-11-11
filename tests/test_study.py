import unittest

from palmistry.study import study_data, study_lookup
from palmistry.engine import knowledge
from palmistry.forms import get_form


class StudyTests(unittest.TestCase):
    def test_two_complete_accounts_are_labelled_retrospective(self):
        data=study_data()
        self.assertEqual(len(data['cases']),2)
        self.assertTrue(all(r['class'].startswith('historical-author-recollection') for r in data['cases']))
        self.assertTrue(all(r['read_scope'] and r['image_locator'] and r['evidence_limit'] for r in data['cases']))
        self.assertEqual(data['counts']['prospective_client_readings_verified'],0)

    def test_cross_volume_case_does_not_claim_same_page_pairing(self):
        row=study_lookup('H02')['records'][0]
        self.assertEqual(row['class'],'historical-author-recollection-cross-volume-image')
        self.assertNotEqual(row['url'],row['image_url'])

    def test_subtitle_coverage_does_not_become_full_video_verification(self):
        row=study_lookup('L01')['records'][0]
        self.assertEqual(row['duration_seconds'],283)
        self.assertFalse(row['continuous_video_watched'])
        self.assertFalse(row['all_slide_details_verified'])
        self.assertEqual(study_lookup('L02')['records'][0]['class'],'author-teaching-booklet-not-video')

    def test_all_requested_topics_have_attribution_and_conditions(self):
        data=study_data()
        self.assertEqual({d['topic'] for d in data['doctrines']},{'性情','职业','健康','婚育','富贵','流年'})
        for row in data['doctrines']:
            self.assertTrue(row['locators'] and row['conditions'] and row['historical_interpretation'])
            self.assertFalse(row['personal_inference'])

    def test_study_content_is_not_promoted_to_personal_rules(self):
        data=study_data()
        self.assertEqual(len(knowledge()['rules']),24)
        self.assertFalse(data['evaluation']['trained_model_weights'])
        self.assertFalse(data['evaluation']['personal_examples_in_repository'])
        self.assertEqual(study_lookup('健康')['mode'],'study-not-personal-reading')
        self.assertEqual(study_lookup('no-such-topic')['status'],'unknown')

    def test_shape_example_cannot_count_as_complete_client_reading(self):
        data=study_data()
        self.assertEqual(len(data['shape_examples']),6)
        for row in data['shape_examples']:
            self.assertEqual(row['class'],'shape-example-not-client-reading')
            self.assertFalse(row['personal_inference'])

    def test_form_lookup_exposes_attributed_conditions_not_personal_assessment(self):
        result=get_form('E104')
        self.assertEqual(result['mode'],'shape-definition-not-personal-forecast')
        self.assertEqual(len(result['historical_context']),1)
        self.assertEqual(len(result['historical_context'][0]['conditions']),2)
        self.assertFalse(result['historical_context'][0]['personal_inference'])
