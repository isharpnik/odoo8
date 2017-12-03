# -*- coding: utf-8 -*-

from openerp import models, api, _


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def split_process(self):
        ctx = {
            'active_model': self._name,
            'active_ids': self.ids,
            'active_id': len(self.ids) and self.ids[0] or False,
            'do_only_split': True,
            'default_picking_id': len(self.ids) and self.ids[0] or False,
        }

        view = self.env.ref('stock_split_picking_wizard.view_stock_enter_split_details')
        return {
            'name': _('Enter quantities to split'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.split_details',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }
