import unittest

from palmistry.iching import all_hexagrams, cast, change, compose, element_relation, from_bits, palm_analogy


class IChingTests(unittest.TestCase):
    def test_all_64_are_bijective(self):
        rows = all_hexagrams()
        self.assertEqual(len(rows), 64)
        self.assertEqual({r['number'] for r in rows}, set(range(1,65)))
        self.assertEqual(len({tuple(r['lines_bottom_up']) for r in rows}), 64)
        for row in rows:
            with self.subTest(row=row['name']):
                self.assertEqual(from_bits(row['lines_bottom_up']), row)

    def test_upper_lower_orientation_uses_asymmetric_anchor(self):
        self.assertEqual(compose('兑','震')['name'], '归妹')
        self.assertEqual(compose('震','兑')['name'], '随')
        self.assertEqual(compose('乾','坤')['name'], '泰')
        self.assertEqual(compose('坤','乾')['name'], '否')

    def test_all_single_changes_are_involutions(self):
        for row in all_hexagrams():
            for line in range(1,7):
                with self.subTest(number=row['number'], line=line):
                    changed = change(row['lines_bottom_up'], [line])['changed']
                    back = change(changed['lines_bottom_up'], [line])['changed']
                    self.assertEqual(back, row)

    def test_guimei_to_heng(self):
        result = cast([9,7,6,7,8,8])
        self.assertEqual(result['original']['name'], '归妹')
        self.assertEqual(result['changed']['name'], '恒')
        self.assertEqual(result['moving_bottom_up'], [1,3])
        self.assertEqual(result['randomness'], 'none-generated')

    def test_guai_to_sui(self):
        result = cast([7,9,9,7,7,8])
        self.assertEqual(result['original']['name'], '夬')
        self.assertEqual(result['changed']['name'], '随')

    def test_static_six_lines_stay(self):
        result = cast([7]*6)
        self.assertEqual(result['original'], result['changed'])
        self.assertEqual(result['moving_bottom_up'], [])

    def test_invalid_values_fail(self):
        for raw in ([True]*6, [1]*6, [6]*5, '777777', [7,7,7,7,7,10]):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                cast(raw)

    def test_invalid_bits_and_duplicate_movers_fail(self):
        with self.assertRaises(ValueError):
            from_bits([True]*6)
        with self.assertRaises(ValueError):
            change([1]*6,[1,1])
        with self.assertRaises(ValueError):
            change([1]*6,[0])

    def test_elements_are_directional_and_complete(self):
        self.assertEqual(element_relation('木','火'), '我生')
        self.assertEqual(element_relation('火','木'), '生我')
        self.assertEqual(element_relation('木','土'), '我克')
        self.assertEqual(element_relation('土','木'), '克我')
        for a in '木火土金水':
            self.assertEqual({element_relation(a,b) for b in '木火土金水'}, {'我生','生我','我克','克我','同类'})

    def test_analogy_is_not_a_cast(self):
        expected = {'life':'屯','fate':'既济','head':'归妹','sun':'比'}
        for line,name in expected.items():
            result = palm_analogy(line)
            self.assertEqual(result['hexagram']['name'], name)
            self.assertFalse(result['cast'])
            self.assertIsNone(result['moving_lines'])
        with self.assertRaises(ValueError):
            palm_analogy('heart')
        self.assertEqual(palm_analogy('heart','观')['hexagram']['name'], '观')
        self.assertEqual(palm_analogy('heart','晋')['hexagram']['name'], '晋')
