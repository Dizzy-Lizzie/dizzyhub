from odoo import models, _
from odoo.exceptions import UserError

class Company(models.Model):

    _inherit = 'res.company'

    def create(self, vals):
        """Prevent companies being created unless it is the main company"""
        for company in self:
            if not company is self.env.ref('base.main_company'):
                raise UserError('Creating new companies is not allowed')
        return super().create(vals)

    def write(self, vals):
        """Prevent updating any company unless a module is being installed"""

        install_mode = self.env.context.get('install_mode')

        protected_fields = {
            'name',
            'street',
            'city',
            'state_id',
            'zip',
            'country_id',
            'phone',
            'email',
            'logo',
            'website',
            'partner_id',
            'currency_id',
        }
        has_protected =  bool(protected_fields & set(vals.keys()))

        if (install_mode or not has_protected):
            return super().write(vals)
        else:
            raise models.ValidationError(
                'Edits not allowed, update in xml data file.'
            )