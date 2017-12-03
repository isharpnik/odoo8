# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp
from datetime import datetime

class stock_split_details(models.TransientModel):
    _name = 'stock.split_details'
    _description = 'Picking wizard'

    picking_id = fields.Many2one('stock.picking', 'Picking')
    item_ids = fields.One2many('stock.split_details_items', 'split_id', 'Items', domain=[('product_id', '!=', False)])
    picking_source_location_id = fields.Many2one('stock.location', string="Head source location", related='picking_id.location_id', store=False, readonly=True)
    picking_destination_location_id = fields.Many2one('stock.location', string="Head destination location", related='picking_id.location_dest_id', store=False, readonly=True)

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_split_details, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            return res
        assert active_model in ('stock.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        items = []
        uom_obj = self.pool['product.uom']
        if not picking.pack_operation_ids:
            picking.do_prepare_partial()
        for op in picking.pack_operation_ids:
            qty_default_uom = uom_obj._compute_qty_obj(cr, uid, op.product_uom_id, op.product_qty, op.product_id.uom_id)
            qty_default_uos = qty_default_uom * op.product_id.uos_coeff
            item = {
                'product_id': op.product_id.id,
                'product_uom_id': op.product_uom_id.id,
                'quantity': op.product_qty,
                'quantity_uos': qty_default_uos,
                'quantity_original': op.product_qty,
                'quantity_available': op.product_id.qty_available,
                'sourceloc_id': op.location_id.id,
                'destinationloc_id': op.location_dest_id.id,
                'date': op.date, 
                'owner_id': op.owner_id.id,
            }
            if op.product_id:
                items.append(item)
        res.update(item_ids=items)
        return res

    @api.one
    def do_detailed_split(self):
        if any([item.quantity > item.quantity_original or item.quantity > item.quantity_available for item in self.item_ids]):
            raise Warning(_('Quantity should to the minimum of Quantity Original and Quantity Available'))

        if self.picking_id.state not in ['assigned', 'partially_available']:
            raise Warning(_('You cannot split a picking in state \'%s\'.') % self.picking_id.state)

        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                
                pack_datas['picking_id'] = self.picking_id.id
                packop_id = self.env['stock.pack.operation'].create(pack_datas)
                processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()
        # Execute the split of the picking
        self.picking_id.do_split()
        return True


class stock_split_details_items(models.TransientModel):
    _name = 'stock.split_details_items'
    _description = 'Picking wizard items'

    split_id = fields.Many2one('stock.split_details', 'Split')
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')
    quantity = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default = 1.0)
    quantity_original = fields.Float('Quantity Original', digits=dp.get_precision('Product Unit of Measure'), default = 1.0)
    quantity_uos = fields.Float('Quantity UOS', digits=dp.get_precision('Product Unit of Measure'), default = 1.0)
    quantity_available = fields.Float('Quantity Available', digits=dp.get_precision('Product Unit of Measure'), default = 1.0)
    sourceloc_id = fields.Many2one('stock.location', 'Source Location', required=True)
    destinationloc_id = fields.Many2one('stock.location', 'Destination Location', required=True)
    date = fields.Datetime('Date')
    owner_id = fields.Many2one('res.partner', 'Owner', help="Owner of the quants")
