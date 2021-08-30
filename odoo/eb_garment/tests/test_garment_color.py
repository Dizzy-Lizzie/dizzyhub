from odoo.tests.common import TransactionCase

class TestColor(TransactionCase):
    def setUp(self, *args, **kwargs):    
        super().setUp(*args, **kwargs)

        self.test_color = self.env['garment.color'].create({
            'name': 'Test Color',
            'code': '123C'
        })


    def test_has_a_name_field_of_type_string(self):
        # self.(self.test_color.name, 'Test Color')
        self.assertTrue(hasattr(self.test_color, 'name'),
            "garment.color class have a color attribute"
        )
        self.assertIsInstance(self.test_color.name, str)


    def test_name_field_can_be_set(self):
        self.test_color.name = 'New Name'
        self.assertEqual(self.test_color.name, 'New Name')


    def test_name_can_be_updated_with_the_write_method(self):
        updated = self.test_color.write({'name': 'New Name'})
        self.assertTrue(updated)
        self.assertEqual(self.test_color.name, 'New Name')