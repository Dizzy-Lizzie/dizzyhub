from odoo import models, _
from odoo.exceptions import UserError


class CrmTeam(models.Model):

    _inherit = 'crm.team'

    def unlink(self):
        default_teams = [
            self.env.ref('sales_team_shopify')
        ]
        for team in self:
            if team in default_teams:
                raise UserError(_('Cannot delete default team "%s"', team.name))
        return super(CrmTeam,self).unlink()