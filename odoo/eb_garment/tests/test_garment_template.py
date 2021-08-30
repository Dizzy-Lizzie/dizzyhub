from odoo.tests.common import TransactionCase

from .factories import GarmentFactory

class TestGarmentTemplate(TransactionCase):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.factory = GarmentFactory(self.env)


    def test_calling_create_returns_persisted_record(self):
        new_garment = self.env['garment.template'].create({
            'name': 'Test Garment',
            'pattern_id': self.factory.create_minimal_pattern().id
        })

        self.assertIn(new_garment, new_garment.exists())


    def test_creating_without_name_throws(self):
        with self.assertRaises(ValueError):
            new_garment = self.env['garment.template'].create([{
                'pattern_id': self.factory.create_minimal_pattern().id
            }])


    def test_garment_exposes_code_field_of_related_color(self):
        test_color = self.factory.create_minimal_color()
        test_garment = self.factory.create_garment_with_optional_related(
            test_color
        )
        self.assertEqual(test_garment.color_code, test_color.code)


    def test_garment_exposes_code_field_of_related_pattern(self):
        test_pattern = self.factory.create_minimal_pattern()
        test_garment = self.factory.create_garment_with_optional_related(
            test_pattern
        )
        self.assertEqual(test_garment.model_code, test_pattern.code)


    def test_when_has_required_relations_generates_a_style_number(self):
        test_pattern = self.factory.create_minimal_pattern(code='PAT1')
        test_color = self.factory.create_minimal_color(code='COL1')
        garment = self.factory.create_garment_with_optional_related(
            test_pattern, test_color
        )
        self.assertIsInstance(garment.style_num, str)
        self.assertEqual(garment.style_num, 'PAT1-COL1')
