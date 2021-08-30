from odoo.tests.common import TransactionCase
from ..exceptions import ValidationError

from .factories import GarmentFactory

class TestIntegrationFromProductTemplateSide(TransactionCase):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.factory = GarmentFactory(self.env)

        self.test_garment = self.factory.create_minimal_garment()

        self.product_template = self.test_garment.product_template_id


    def test_when_created_by_child_garment_has_child_garment_is_true(self):
        self.assertTrue(self.product_template.has_child_garment)


    def test_changing_product_type_when_has_child_garment_throws(self):
        with self.assertRaises(ValidationError):
            self.product_template.write({'type': 'consu'})
        with self.assertRaises(ValidationError):
            self.product_template.update({'type': 'consu'})
    

    def test_when_deleted_related_garment_is_also_deleted(self):
        self.assertIn(self.test_garment,
            self.test_garment.exists()
        )
        self.product_template.unlink()
        self.assertNotIn(self.test_garment,
            self.test_garment.exists()
        )

    def test_copy_throws_when_has_child_garment(self):
        with self.assertRaises(NotImplementedError):
            self.product_template.copy()


class TestIntegrationFromGarmentTemplateSide(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.factory = GarmentFactory(self.env)


    def test_created_garment_has_a_parent_product_template(self):
        new_garment = self.factory.create_minimal_garment()
        garment_id = new_garment.id
        product_id = new_garment.product_template_id.id

        new_garment.invalidate_cache()
        new_garment.clear_caches()
        fetched = self.env['garment.template'].browse([garment_id])
        self.assertEqual(fetched.product_template_id.id, product_id)
        self.assertIsInstance(
            new_garment.product_template_id,
            type(self.env['product.template'])
        )


    def test_created_garment_name_is_equal_to_product_template_name(self):
        name = 'Should Be Equal'
        new_garment = self.env['garment.template'].create({
            'name': name,
            'pattern_id': self.factory.create_minimal_pattern().id
        })
        self.assertEqual(name, new_garment.name)
        self.assertEqual(name, new_garment.product_template_id.name)
        self.assertEqual(
            new_garment.product_template_id.name,
            new_garment.name,
        )


    def test_updating_name_updates_product_template_name(self):
        old_name = 'Old Name'
        new_name = 'Is Updated'
        self.test_garment = self.factory.create_minimal_garment(name=old_name)
        self.test_garment.write({'name': new_name})
        self.assertEqual(self.test_garment.name, new_name)
        self.assertEqual(self.test_garment.name,
            self.test_garment.product_template_id.name
        )


    def test_deleting_garment_deletes_product_template(self):
        self.test_garment = self.factory.create_minimal_garment()
        parent_template = self.test_garment.product_template_id
        parent_literal_id = parent_template.id
        self.assertIn(parent_template,
            self.env['product.template'].browse([parent_literal_id]).exists()
        )
        
        self.test_garment.unlink()
        
        self.test_garment.invalidate_cache()
        self.test_garment.clear_caches()
        self.assertNotIn(
            parent_template,
            parent_template.exists()
        )

    def test_setting_color_on_garment_generates_attribute_line_on_product_template(self):
        garment = self.factory.create_minimal_garment()
        color = self.factory.create_minimal_color()
        garment.write({'color_id': color.id})
        lines = garment.product_template_id.attribute_line_ids
        color_attribute_value = color.product_attribute_value_id
        color_attribute = color.product_attr
        color_lines = lines.filtered_domain([
            ('attribute_id', '=', color_attribute.id)
        ])

        self.assertEqual(len(color_lines), 1)
        color_line = color_lines[0]
        self.assertEqual(color_line.product_tmpl_id.id,
            garment.product_template_id.id
        )


    def test_setting_color_on_garment_adds_color_value_to_attribute_template(self):
        garment = self.factory.create_minimal_garment()
        color = self.factory.create_minimal_color()
        garment.write({'color_id': color.id})
        lines = garment.product_template_id.attribute_line_ids
        color_attribute_value = color.product_attribute_value_id
        color_attribute = color.product_attr
        color_lines = lines.filtered_domain([
            ('attribute_id', '=', color_attribute.id)
        ])

        self.assertEqual(len(color_lines), 1)
        color_line = color_lines[0]
        self.assertEqual(len(color_line.value_ids), 1)
        self.assertEqual(color_line.value_ids.id, color_attribute_value.id)
            
