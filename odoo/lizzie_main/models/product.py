from odoo import models, fields, api

class ProductTemplate(models.Model):
    
    _inherit = 'product.template'

    # overiding field defined in the OCA 
    # product_variant_default_code module
    # code_prefix = fields.Char(
    #     required=True,
    # )

    @api.constrains('code_prefix')
    def _check_code_prefix(self):
        for rec in self:
            if not rec.code_prefix:
                raise models.ValidationError("You must include a reference mask")

