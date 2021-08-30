from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase

from ..exceptions import ValidationError, GarmentValueError
from .factories import GarmentFactory

class TestGarmentSizeRangeTemplate(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.factory = GarmentFactory(self.env)

    def test_can_be_created(self):
        template = self.env['garment.size.range.template'].create({
            'name': 'Test Range Template',
        })

        self.assertIn(template, template.exists())
    
    def test_creating_without_name_throws(self):

        with self.assertRaises(GarmentValueError,) as e:
            template = self.env['garment.size.range.template'].create({
            })

class TestGarmentSize(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.factory = GarmentFactory(self.env)

    def test_can_be_created(self):
        range_tmpl = self.factory.create_minimal_size_range_template()
        size = self.env['garment.size'].create({
            'name': 'Extra Large',
            'code': 'XL',
            'range_tmpl_id': range_tmpl.id,
        })

        self.assertIn(size, size.exists())

    def test_creating_without_name_throws(self):
        range_tmpl = self.factory.create_minimal_size_range_template()

        with self.assertRaises(IntegrityError) as e:
            size = self.env['garment.size'].create({
                'code': 'XL',
                'range_tmpl_id': range_tmpl.id
            })

    def test_creating_without_size_template_relation_throws(self):
        with self.assertRaises(IntegrityError) as e:
            size = self.env['garment.size'].create({
                'name': 'Extra Large',
                'code': 'XL',
            })