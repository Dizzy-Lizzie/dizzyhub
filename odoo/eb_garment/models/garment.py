from inspect import Attribute
from odoo import models, fields, api
from ..exceptions import (
    ValidationError, UserError, GarmentValueError
)

from odoo.exceptions import ValidationError as OdooValidationError

class GarmentTemplate(models.Model):

    _name = 'garment.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'product.template': 'product_template_id'}
    _description = 'Garment Template'

    _sql_constraints = [(
        'unique-pattern_id-color_id', 'UNIQUE(pattern_id, color_id)',
        'A style with this body and color combinationi already exists.'
    )]
    @api.constrains('type')
    def _product_template_is_type_product(self):
        for record in self:
            if self.type != 'product':
                raise ValidationError(
                    "Parent Product Template must be type product"
                )


    name = fields.Char(
        string='Style Name',
        inherited=False,
        required=True,
        inverse='_inverse_name'
    )

    product_template_id = fields.Many2one('product.template',
        required=True,
        readonly=True,
        auto_join=True,
        ondelete='cascade'
    )
    pattern_id = fields.Many2one('garment.pattern',
        string='Body',
        ondelete='restrict'
    )
    season_id = fields.Many2one('garment.season',
        string='Season',
        ondelete='restrict',
        auto_join=True,
    )
    collection_ids = fields.Many2many('garment.collection',
        string='Collections',
        ondelete='restrict',
        auto_join=True,
    )
    color_id = fields.Many2one('garment.color',
        string='Color',
        ondelete='restrict',
        inverse='_inverse_color_id',
        auto_join=True,
        store=True
    )

    model_code = fields.Char(
        name='Model Code',
        related='pattern_id.code',
        readonly=True,
    )
    color_code = fields.Char(
        name='Style Code',
        related='color_id.code',
        readonly=True,
    )
    style_num = fields.Char(
        compute='_compute_style_num'
    )


    @api.depends('color_code', 'model_code')
    def _compute_style_num(self):
        for garment_tpl in self:
            garment_tpl.style_num = False
            if garment_tpl.model_code and garment_tpl.color_code:
                garment_tpl.style_num = "-".join([
                    garment_tpl.model_code,
                    garment_tpl.color_code ,
                ])


    @api.depends('name', 'product_template_id.name')
    def _inverse_name(self):
        for garment in self:
            garment.product_template_id.name = garment.name


    @api.depends('product_template_id')
    def _inverse_color_id(self):
        for garment in self:
            color = garment.color_id
            if color:
                line = garment.existing_color_line()
                if not line:
                    line = garment.create_color_line(color)
                else:
                    line.write({
                        'value_ids': color.product_attribute_value_id.id,
                    })
            else:
                line = garment.existing_color_line()
                if line:
                    line.unlink()


    def create_color_line(self, color):
        self.ensure_one()
        return self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.product_template_id.id,
            'attribute_id': self.env['garment.color'].product_attr.id,
            'value_ids': [(4, color.product_attribute_value_id.id, 0)],
        })


    def existing_color_line(self):
        self.ensure_one()
        def filter_lines(line):
            return (
                line.attribute_id.id == 
                self.env['garment.color'].product_attr.id
            )

        product_tmpl = self.product_template_id
        lines = product_tmpl.attribute_line_ids.filtered(filter_lines)
        return next(iter(lines), False)

    def name_get(self):
        res = []

        for g in self:
            if g.style_num:
                res.append((g.id, f"[{g.style_num}] {g.name}"))
            else:
                res.append((g.id, g.name))
        return res

    def default_get(self, fields_list):
        fields_list = super().default_get(fields_list)
        fields_list['type'] = 'product'
        fields_list['display_name'] = 'New'
        return fields_list

    @api.model_create_multi
    def create(self, vals_list):

        vals_with_parent_id = []
        for vals in vals_list:
            if not 'name' in vals:
                raise ValueError("""
                    Creating a new garment_template requires the name
                    field be set to non empty value on.
                """)

            product_template = self.env['product.template'].create({
                'name': vals['name'], 
                'type': 'product',
            })

            vals_with_parent_id.append({
                **vals,
                'product_template_id': product_template.id,
            })

        return super().create(vals_with_parent_id)

    def unlink(self):
        self.product_template_id.unlink()
        return super().unlink()

    # Copy pasted from product.template
    def open_pricelist_rules(self):
        self.ensure_one()
        return self.product_template_id.open_pricelist_rules()



class GarmentPattern(models.Model):

    _name = 'garment.pattern'

    _description = 'Garment Pattern'


    _sql_constraints = [(
        'unique-code', 'UNIQUE(code)', 'Style Codes must be unique'
    )]

    name = fields.Char(
        string='Style Name',
        help='Pattern template name or style family e.g. Rome Shirt',
        required=True
    )
    code = fields.Char(
        help='The code used to generate SKUs for this style',
        required=True,
    )
    type = fields.Selection(
        [
            ('shirt', 'Shirt'),
            ('pant', 'Pant'),
            ('dress', 'Dress'),
            ('tunic', 'Tunic'),
            ('skirt', 'Skirt')
        ],
        string='Body Type'
    )

    def name_get(self):
        names = []
        for pattern in self:
            names.append((
                pattern.id,
                f"[{pattern.code}] {pattern.name}"
            ))
        return names


class GarmentColor(models.Model):

    _name = 'garment.color'
    _description = 'Garment Color'

    _sql_constraints = [(
        'unique-code', 'UNIQUE(code)', 'Style Codes must be unique'
    )]

    name = fields.Char(
        string='Color Name',
        help='Pattern template name or style family e.g. Rome Shirt',
        required=True
    )
    code = fields.Char(
        string='Color Code',
        help='The code used to generate SKUs for this style',
        required=True,
        inverse='_compute_uppcase_code',
        readonly=False,
    )

    # # Instance of the product.attribute record that is created
    # # by this module's xml data. This value should never
    # # be changed and should be constant between all instances.
    # # This WOULD be a class constant in a real python class.
    # product_attribute_id = fields.Many2one('product.attribute',
    #     default='_compute_product_attribute_id',
    #     compute='_compute_product_attribute_id',
    #     store=False
    # )

    product_attribute_value_id = fields.Many2one(
        'product.attribute.value',
        required=True,
        ondelete='cascade',
    )

    
    @property
    def product_attr(self):
        return self.env.ref(
            'eb_garment.garment_color_attribute'
        )


    @api.depends('code')
    def _compute_uppcase_code(self):
        self.code = str(self.code).upper() if self.code else ''


    def default_get(self, fields_list):
        fields_list = super().default_get(fields_list)
        return fields_list


    def name_get(self):
        names = []
        for color in self:
            names.append((
                color.id,
                f"[{color.code}] {color.name}"
            ))
        return names


    @api.model
    def create(self, vals):

        value_id = self.env['product.attribute.value'].create({
            'name': vals['name'],
            'attribute_id': self.product_attr.id
        })
        vals['product_attribute_value_id'] = value_id.id
        return super().create(vals)


    def write(self, vals):
        name = vals.get('name')
        if name:
            self.product_attribute_value_id.update({
                'name': vals['name']
            })
        return super().write(vals)



class GarmentSizeRangeTemplate(models.Model):
    _name = 'garment.size.range.template'
    _description = 'Size Range Template'

    name = fields.Char(string='Size Range Name', required=True)
    size_ids = fields.One2many('garment.size',
        'range_tmpl_id'
    )

    def new(self, values={}, origin=None, ref=None):
        return super().new(values, origin, ref)

    @api.model_create_multi
    def create(self, value_list):
        for val in value_list:
            if not 'name' in val:
                raise GarmentValueError("""
                    value for field 'name' must be supplied.
                """)

        return super().create(value_list)

    def unlink(self):
        if self.size_ids:
            for size in self.size_ids:
                size.unlink()
        return super().unlink()


class GarmentSizeRange(models.Model):
    _name = 'garment.size.range'
    _description = 'Size Range'
    _inherits = {
        'garment.size.range.template': 'size_range_tmpl_id'
    }

    size_range_tmpl_id = fields.Many2one('garment.size.range.template',
        string='Inherited Size Range Template',
        required=True,
        ondelete='cascade'
    )

class GarmentSizeCode(models.Model):

    _name = 'garment.size.code'
    _description = 'Garment Size Codes'

    _sql_constraints = [
        (
            'unique-code-per-size-range', 
            'UNIQUE(name, range_tmpl_id)',
            'Size code must be unique to its size range template.'
        ),
        (
            # This relies on is_identity null values not being
            # counted by the constraint
            'one-identity-per-size', 'UNIQUE(is_identity, size_id)',
            'Only one identity code is allowed per size'
        )
    ]

    name = fields.Char(
        string='Code',
        inverse='_inverse_name',
        required=True,
        store=True,
    )
    is_identity = fields.Boolean(
        string='Authoritative Code', default=False,
        compute='_compute_is_identity',
        inverse='_compute_is_identity',
        store=True,
    )

    size_id = fields.Many2one('garment.size',
        string='Technical Field to hold relation to a codes size.',
        required=True,
    )
    range_tmpl_id = fields.Many2one('garment.size.range.template',
        related='size_id.range_tmpl_id',
        depends=['size_id'],
        string='Technical for constraints',
        required=True,
        store=True,
    )

    @api.depends('name')
    def _inverse_name(self):
        self.name = str(self.name).upper() if self.name else ''

    # Ensure that this field can never be false
    def _compute_is_identity(self):
        for code in self:
            if not code.is_identity is True:
                code.is_identity = None

    # @api.model
    # def name_create(self, name):
    #     size = self.size_id.browse([self._context.get('default_size_id')])
    #     range_tmpl = size.range_tmpl_id
    #     code = self.create({
    #         'name': name,
    #         'is_identity': self._context.get('default_is_identity'),
    #         'size_id': size.id,
    #         'range_tmpl_id': range_tmpl.id,
    #     })
    #     return code.name_get()[0]
    #     return super().name_create(name)

    def create(self, values):
        return super().create(values)


class GarmentSize(models.Model):

    _name = 'garment.size'
    _description = 'Garment Sizes'
    _order = 'sequence, id'


    @api.constrains('code_alias_ids')
    def _constrain_code_alias_ids(self):
        for size in self:
            if len(size.ident_code_id & size.code_alias_ids) > 0:
                raise ValueError(
                    'Can\'t use a the main code {} as an alias'.format(
                        size.ident_code_id.name
                    )
                )
    name = fields.Char(
        string='Size Name',
        required=True,
    )

    code = fields.Char(related='ident_code_id.name', readonly=False)
    sequence = fields.Integer(string='Order',
        default=10,
        required=True,
    )

    ident_code_id = fields.Many2one('garment.size.code',
        string='Used to calc Code field',
        compute='_compute_ident_code_id',
        store=False,
    )
    code_ids = fields.One2many('garment.size.code',
        'size_id',
        string='Technical Field to Hold All related codes'
    )
    code_alias_ids = fields.One2many('garment.size.code',
        compute='_compute_code_alias_ids',
        inverse='_inverse_code_alias_ids',
        string='Alternative Codes',
    )
    range_tmpl_id = fields.Many2one('garment.size.range.template',
        required=True
    )

    @api.depends('code_ids', 'code_alias_ids', 'ident_code_id')
    def _compute_code_alias_ids(self):
        for size in self:
            size.code_alias_ids = size.code_ids - size.ident_code_id
    
    @api.depends('code_ids', 'code_alias_ids', 'ident_code_id')
    def _inverse_code_alias_ids(self):
        for size in self:
            size._constrain_code_alias_ids()
            without_ident = size.code_ids - size.ident_code_id
            removed_ids = without_ident - (without_ident & size.code_alias_ids)
            for removed_id in removed_ids:
                removed_id.unlink()
            size.code_ids = size.code_alias_ids + size.ident_code_id

    @api.depends('code_ids', 'ident_code_id')
    def _compute_ident_code_id(self):
        def filter(code_id):
            return code_id.is_identity

        for size in self:
            if not size.ident_code_id:
                existing = size.code_ids.filtered(filter)
                if existing.id:
                    size.ident_code_id = existing
                else:
                    size.ident_code_id = self.env['garment.size.code'].new({'is_identity': True, 'size_id': size.id, 'name': ''})
            else:
                size.ident_code_id = size.ident_code_id
            size.ident_code_id.ensure_one()


    def write(self, values):
        super().write(values)

    @api.model_create_multi
    def create(self, value_list):
        res =  super().create(value_list)
        for size, value in zip(res, value_list):
            size.ident_code_id = self.env['garment.size.code'].create({
                'is_identity': True, 
                'size_id': size.id,
                'range_tmpl_id': size.range_tmpl_id.id,
                'name': value['code']
            })
        return res

    def unlink(self):
        for code in self.code_ids:
            code.unlink()
        return super().unlink()


class GarmentSeason(models.Model):
    _name = 'garment.season'
    _description = 'Garment Season'

    _sql_constraints = [(
        'name_unique', 'UNIQUE(name)', 'Season names must be unique'
    )]

    name = fields.Char(
        string='Season Name',
        required=True
    )

    style_ids = fields.One2many('garment.template',
        'collection_ids',
        string='Styles'
    )


class GarmentCollection(models.Model):

    _name = 'garment.collection'
    _description = 'Garment Collection'


    name = fields.Char(string='Collection Name', required=True)
    season_id = fields.Many2one(
            'garment.season',
            string='Collection Season'
    )
    garment_ids = fields.Many2many(
        'garment.template',
        string='Styles',
    )


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    child_garment_id = fields.One2many(
        'garment.template',
        'product_template_id'
    )
    has_child_garment = fields.Boolean(compute='_compute_has_child_garment')


    @api.depends('child_garment_id')
    def _compute_has_child_garment(self):
        for rec in self:
            if rec.child_garment_id:
                rec.has_child_garment = True
            else:
                rec.has_child_garment = False


    @api.constrains('child_garment_id', 'type')
    def _is_type_product_when_has_garment(self):

        exception = ValidationError(
            "Related garment template requires type attribute"
            "be set to 'product'."
        )
        for record in self:
            if self.type != 'product' and self.has_child_garment:
                raise exception

    def copy(self, default=None):
        if self.has_child_garment:
            raise NotImplementedError(
                "Related garment template doesn't support copying"
            )
        return super().copy(default=default)

class ProductAttribute(models.Model):

    _inherit = 'product.attribute'

    def unlink(self):
        size_record = self.env.ref('eb_garment.garment_size_attribute')
        color_record = self.env.ref('eb_garment.garment_color_attribute')
        for attr in self:
            if (
                (attr.id == size_record.id) or
                (attr.id == color_record.id)
            ):
                raise UserError(
                    "Can't delete {} attribute, required by "
                    "Garment module.".format(attr.display_name)
                )
        return super().unlink()