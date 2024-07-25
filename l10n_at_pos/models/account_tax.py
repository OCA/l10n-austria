from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    asign_type = fields.Selection([('reduced1', 'Reduced 1'),
                                   ('reduced2', 'Reduced 2'),
                                   ('special', 'Special'),
                                   ('null', 'Null')], string="a.sign Type")


